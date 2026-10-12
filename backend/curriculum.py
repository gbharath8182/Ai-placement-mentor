"""Strict, database-independent validation for version-controlled curriculum."""

import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal, Union
from urllib.parse import unquote, urlsplit

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator


DEFAULT_PATH = Path(__file__).resolve().parents[1] / "curriculum" / "python-foundations.json"
DEFAULT_PRACTICE_PATH = DEFAULT_PATH.with_name("python-practice.json")
Text = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
Slug = Annotated[str, StringConstraints(min_length=1, max_length=128, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
Difficulty = Literal["beginner", "intermediate", "advanced"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    @field_validator("schema_version", mode="before", check_fields=False)
    @classmethod
    def strict_version(cls, value):
        if type(value) is not int:
            raise ValueError("schema_version must be an integer")
        return value


class TextBlock(StrictModel):
    type: Literal["text"]
    value: Text


class HeadingBlock(StrictModel):
    type: Literal["heading"]
    value: Text
    level: int = Field(ge=2, le=4)


class ListBlock(StrictModel):
    type: Literal["list"]
    items: list[Text] = Field(min_length=1)
    ordered: bool


class CodeBlock(StrictModel):
    type: Literal["code"]
    language: Literal["python"]
    value: Text
    expected_output: str


class CalloutBlock(StrictModel):
    type: Literal["callout"]
    kind: Literal["info", "tip", "warning", "important"]
    title: Text
    value: Text


class DiagramBlock(StrictModel):
    type: Literal["diagram"]
    title: Text
    value: Text


class KnowledgeCheck(StrictModel):
    type: Literal["knowledge_check"]
    id: Slug
    concept_id: Slug
    question: Text
    options: list[Text] = Field(min_length=2, max_length=6)
    correct_index: int = Field(ge=0)
    explanation: Text

    @model_validator(mode="after")
    def validate_answer(self):
        if self.correct_index >= len(self.options):
            raise ValueError("correct_index must address an option")
        if len({option.strip().casefold() for option in self.options}) != len(self.options):
            raise ValueError("knowledge check options must be distinct")
        return self


class ResourceLink(StrictModel):
    type: Literal["resource_link"]
    label: Text
    url: Text

    @field_validator("url")
    @classmethod
    def official_https_url(cls, value):
        decoded = unquote(value)
        if any(character.isspace() or ord(character) < 32 or character in '<>"\'`\\' for character in decoded):
            raise ValueError("resource URL contains unsafe characters")
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https" or parsed.netloc != "docs.python.org"
            or not parsed.path.startswith("/3") or parsed.query
        ):
            raise ValueError("resources must use HTTPS official Python documentation URLs")
        return value


ContentBlock = Annotated[
    Union[TextBlock, HeadingBlock, ListBlock, CodeBlock, CalloutBlock, DiagramBlock, KnowledgeCheck, ResourceLink],
    Field(discriminator="type"),
]


class Subtopic(StrictModel):
    title: Text
    difficulty: Difficulty
    content_blocks: list[ContentBlock] = Field(min_length=1)


class Lesson(StrictModel):
    schema_version: Literal[1]
    slug: Slug
    domain_slug: Slug
    title: Text
    difficulty: Difficulty
    order: int = Field(ge=1)
    objectives: list[Text] = Field(min_length=2)
    prerequisites: list[Slug]
    subtopics: list[Subtopic] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_depth(self):
        blocks = [block for subtopic in self.subtopics for block in subtopic.content_blocks]
        required = {"text", "heading", "list", "code", "callout", "diagram", "knowledge_check", "resource_link"}
        if required - {block.type for block in blocks}:
            raise ValueError("lesson must include all eight supported block types")
        if sum(block.type == "knowledge_check" for block in blocks) < 2:
            raise ValueError("lesson requires at least two knowledge checks")
        if len(set(self.prerequisites)) != len(self.prerequisites):
            raise ValueError("prerequisites must be distinct")
        return self


class Domain(StrictModel):
    schema_version: Literal[1]
    slug: Slug
    title: Text
    description: Text
    topics: list[Slug] = Field(min_length=1)


class Curriculum(StrictModel):
    schema_version: Literal[1]
    domains: list[Domain] = Field(min_length=1)
    topics: list[Lesson] = Field(min_length=1)

    @field_validator("schema_version")
    @classmethod
    def integer_version(cls, value):
        if type(value) is not int:
            raise ValueError("schema_version must be an integer")
        return value

    @model_validator(mode="after")
    def validate_references(self):
        domains = {domain.slug: domain for domain in self.domains}
        lessons = {lesson.slug: lesson for lesson in self.topics}
        if len(domains) != len(self.domains) or len(lessons) != len(self.topics):
            raise ValueError("domain and topic slugs must be unique")
        check_ids = set()
        for domain in self.domains:
            ordered = sorted((lesson for lesson in self.topics if lesson.domain_slug == domain.slug), key=lambda lesson: lesson.order)
            if domain.topics != [lesson.slug for lesson in ordered]:
                raise ValueError("domain topics must exactly list its lessons in order")
            if [lesson.order for lesson in ordered] != list(range(1, len(ordered) + 1)):
                raise ValueError("lesson order must be contiguous starting at one")
        for lesson in self.topics:
            if type(lesson.schema_version) is not int or lesson.domain_slug not in domains:
                raise ValueError("lesson requires an integer version and a known domain")
            for prerequisite in lesson.prerequisites:
                earlier = lessons.get(prerequisite)
                if earlier is None or earlier.domain_slug != lesson.domain_slug or earlier.order >= lesson.order:
                    raise ValueError("prerequisites must reference earlier lessons in the same domain")
            for subtopic in lesson.subtopics:
                for block in subtopic.content_blocks:
                    if isinstance(block, KnowledgeCheck):
                        if block.id in check_ids:
                            raise ValueError("knowledge check ids must be globally unique")
                        check_ids.add(block.id)
        if any(type(domain.schema_version) is not int for domain in self.domains):
            raise ValueError("domain schema_version must be an integer")
        return self


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_curriculum(path=None) -> dict:
    """Return fresh JSON-compatible domains/topics; never connect to DB or run code."""
    source = DEFAULT_PATH if path is None else Path(path)
    raw = json.loads(source.read_text(encoding="utf-8"), object_pairs_hook=_unique_keys)
    validated = Curriculum.model_validate(raw)
    return validated.model_dump(mode="json", include={"domains", "topics"})


class PracticeCase(StrictModel):
    input: str
    expected_output: str


class PracticeProblem(StrictModel):
    id: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{24}$")]
    topic_slug: Slug
    title: Text
    difficulty: Difficulty
    description: Text
    starter_code: Text
    language: Literal["python"]
    test_cases: list[PracticeCase] = Field(min_length=3)
    reference_solution: Text

    @model_validator(mode="after")
    def stable_identity(self):
        expected_id = hashlib.sha256(self.topic_slug.encode("utf-8")).hexdigest()[:24]
        if self.id != expected_id:
            raise ValueError("practice id must be the first 24 hex digits of SHA-256(topic_slug)")
        if len({case.input for case in self.test_cases}) != len(self.test_cases):
            raise ValueError("practice test inputs must be distinct")
        return self


class PracticeCurriculum(StrictModel):
    schema_version: Literal[1]
    practice_problems: list[PracticeProblem] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_problems(self):
        if len({problem.id for problem in self.practice_problems}) != len(self.practice_problems):
            raise ValueError("practice ids must be unique")
        if len({problem.topic_slug for problem in self.practice_problems}) != len(self.practice_problems):
            raise ValueError("only one flagship practice problem per topic")
        return self


def load_practice(path=None) -> list[dict]:
    """Load authored practice INCLUDING private solutions; use public_practice for API/DB."""
    source = DEFAULT_PRACTICE_PATH if path is None else Path(path)
    raw = json.loads(source.read_text(encoding="utf-8"), object_pairs_hook=_unique_keys)
    validated = PracticeCurriculum.model_validate(raw)
    known_topics = {topic["slug"] for topic in load_curriculum()["topics"]}
    if any(problem.topic_slug not in known_topics for problem in validated.practice_problems):
        raise ValueError("practice must reference a known flagship topic")
    return [problem.model_dump(mode="json") for problem in validated.practice_problems]


def public_practice(problem: dict) -> dict:
    """Allowlisted public projection: never publish or persist reference_solution."""
    return {key: problem[key] for key in (
        "id", "topic_slug", "title", "difficulty", "description", "starter_code", "language", "test_cases",
    )}
