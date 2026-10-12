from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional, Dict, Any, Annotated, Literal
from datetime import datetime
import json

Password = Annotated[str, Field(min_length=6, max_length=72)]
ShortText = Annotated[str, Field(min_length=1, max_length=64)]
TopicSlug = Annotated[str, Field(min_length=1, max_length=128, pattern=r"\S")]


class PasswordInput(BaseModel):
    @field_validator("password", check_fields=False)
    @classmethod
    def bound_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password cannot exceed 72 UTF-8 bytes")
        return value

# Auth Schemas
class UserProfile(BaseModel):
    experience_level: str = "fresher"  # fresher, intermediate, experienced
    interests: List[str] = Field(default_factory=list)

class UserCreate(PasswordInput):
    name: str = Field(min_length=1, max_length=100, pattern=r"\S")
    email: EmailStr
    password: Password
    experience_level: ShortText = "fresher"
    interests: List[ShortText] = Field(default_factory=list, max_length=20)

class UserLogin(PasswordInput):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    profile: UserProfile
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(PasswordInput):
    token: str = Field(min_length=1, max_length=8192)
    password: Password

# Content Schemas
class ContentBlock(BaseModel):
    type: str  # text, code, resource_link
    value: str
    language: Optional[str] = None
    label: Optional[str] = None
    url: Optional[str] = None

class SubTopic(BaseModel):
    title: str
    content_blocks: List[Dict[str, Any]]
    difficulty: Optional[str] = None

class TopicResponse(BaseModel):
    id: str
    domain_slug: str
    slug: str
    title: str
    content_blocks: Optional[List[Dict[str, Any]]] = []
    difficulty: str
    subtopics: Optional[List[SubTopic]] = []
    schema_version: Optional[int] = None
    objectives: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    order: Optional[int] = None

class DomainResponse(BaseModel):
    id: str
    slug: str
    title: str
    description: str
    topics: List[str] = []  # List of topic slugs or IDs

# AI Schemas
class AIRecommendRequest(BaseModel):
    topic_slug: TopicSlug
    answers: Dict[str, Any] = Field(max_length=50)

    @field_validator("answers")
    @classmethod
    def bound_answers(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if len(json.dumps(value, ensure_ascii=False).encode("utf-8")) > 16384:
            raise ValueError("Answers cannot exceed 16 KiB")
        return value

class AIChatRequest(BaseModel):
    topic_slug: TopicSlug
    message: str = Field(min_length=1, max_length=8000)
    subtopic_title: Optional[str] = Field(default=None, max_length=200)

class AIExplainRequest(BaseModel):
    topic_slug: TopicSlug
    level: Literal["fresher", "intermediate", "experienced"]

# Practice Schemas
class TestCase(BaseModel):
    input: str
    expected_output: str

class PracticeProblemResponse(BaseModel):
    id: str
    topic_slug: str
    title: str
    difficulty: str
    description: str
    starter_code: str
    # Test cases are hidden or returned depending on need. We return count or simple description, hide actual assertions if necessary, or return. Let's return them.
    test_cases: List[TestCase]

class CodeSubmitRequest(BaseModel):
    language: Literal["python", "javascript", "cpp", "c", "java"]
    code: str = Field(min_length=1, max_length=65536, pattern=r"\S")

    @field_validator("code")
    @classmethod
    def bound_code_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 65536:
            raise ValueError("Code cannot exceed 64 KiB")
        return value

# Progress Schemas
class ProgressUpdate(BaseModel):
    topic_slug: TopicSlug
    status: Literal["not_started", "in_progress", "completed"]
    ai_notes: Optional[str] = Field(default=None, max_length=8000)

# Activity Log & Streak Schemas
class ActivityLog(BaseModel):
    minutes_spent: int
    activity_type: str  # lesson, playground, quiz, practice
    topic_slug: Optional[str] = None

class ActivityLogCreate(ActivityLog):
    minutes_spent: int = Field(ge=0, le=1440, strict=True)
    activity_type: ShortText
    topic_slug: Optional[TopicSlug] = None

class ActivityLogResponse(BaseModel):
    id: str
    user_id: str
    date: str  # YYYY-MM-DD
    minutes_spent: int
    activity_type: str
    topic_slug: Optional[str] = None

class StreakData(BaseModel):
    current_streak: int
    longest_streak: int
    last_active_date: Optional[str] = None

class StreakResponse(StreakData):
    pass


# ===== Extended Domain Detail Schemas (Roadmap, Prep, Projects) =====
class SkillItem(BaseModel):
    name: str
    description: str
    importance: str
    level: str  # beginner, intermediate, advanced
    estimated_hours: int

class ResourceSet(BaseModel):
    documentation: Optional[str] = None
    youtube_playlist: Optional[str] = None
    articles: List[str] = []
    notes: Optional[str] = None
    practice_platform: Optional[str] = None
    cheat_sheet: Optional[str] = None

class TopicDetail(BaseModel):
    name: str
    description: str
    importance: str
    difficulty: str
    estimated_time: str
    prerequisites: List[str] = []
    resources: ResourceSet
    practice_questions: List[str] = []
    projects: List[str] = []
    interview_questions: List[str] = []

class ProjectItem(BaseModel):
    title: str
    description: str
    skills_learned: List[str] = []
    technologies_used: List[str] = []
    github_ideas: List[str] = []
    tier: str  # beginner, intermediate, advanced

class CompanyPrepGroup(BaseModel):
    group_name: str  # "Product Companies", "Service Companies"
    example_companies: List[str] = []
    focus_areas: List[str] = []

class InterviewPrep(BaseModel):
    important_topics: List[str] = []
    frequently_asked_questions: List[str] = []
    coding_questions: List[str] = []
    hr_questions: List[str] = []
    system_design_questions: List[str] = []

class RoadmapTier(BaseModel):
    tier: str  # beginner, intermediate, advanced
    items: List[str] = []

class DomainDetailResponse(BaseModel):
    domain_slug: str
    overview: str
    why_important: str
    industries_using: List[str] = []
    future_scope: str
    average_salary: Optional[str] = None
    skills_required: List[str] = []
    prerequisites: List[str] = []
    roadmap: List[RoadmapTier] = []
    topics: List[TopicDetail] = []
    skills: List[SkillItem] = []
    practice_platforms: List[str] = []
    projects: List[ProjectItem] = []
    interview_prep: InterviewPrep
    resume_tips: List[str] = []
    certifications: List[str] = []
    company_prep: List[CompanyPrepGroup] = []
