import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from backend.curriculum import (
    Curriculum, DEFAULT_PATH, DEFAULT_PRACTICE_PATH, KnowledgeCheck,
    PracticeCurriculum, ResourceLink, load_curriculum, load_practice, public_practice,
)
from scripts.import_curriculum import ImportConflict, import_curriculum, main, preview_import


def authored_blocks(topic):
    return [block for subtopic in topic["subtopics"] for block in subtopic["content_blocks"]]


class FakeCollection:
    def __init__(self, documents=()):
        self.documents = copy.deepcopy(list(documents))
        self.insertions = []
        self.fail_insert = False

    def find(self, query):
        return [copy.deepcopy(document) for document in self.documents if document.get("slug") == query["slug"]]

    def insert_one(self, document):
        if self.fail_insert:
            raise RuntimeError("simulated interrupted insert")
        self.insertions.append(copy.deepcopy(document))
        self.documents.append(copy.deepcopy(document))


class FakeDatabase:
    name = "isolated_curriculum_test"

    def __init__(self):
        self.collections = {name: FakeCollection() for name in ("domains", "topics")}

    def __getitem__(self, name):
        return self.collections[name]


class CurriculumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authored = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        cls.curriculum = load_curriculum()
        cls.practice_raw = json.loads(DEFAULT_PRACTICE_PATH.read_text(encoding="utf-8"))
        cls.practice = load_practice()

    def test_exact_flagship_contract_and_count(self):
        self.assertEqual(set(self.curriculum), {"domains", "topics"})
        self.assertEqual(len(self.curriculum["domains"]), 1)
        self.assertEqual(len(self.curriculum["topics"]), 15)
        domain = self.curriculum["domains"][0]
        self.assertEqual(domain["slug"], "python-foundations")
        self.assertEqual(self.curriculum["topics"][0]["slug"], "python-foundations-values-and-types")
        self.assertEqual(domain["topics"], [topic["slug"] for topic in self.curriculum["topics"]])
        self.assertEqual([topic["order"] for topic in self.curriculum["topics"]], list(range(1, 16)))

    def test_substantive_lesson_structure(self):
        ids = set()
        required = {"text", "heading", "list", "code", "callout", "diagram", "knowledge_check", "resource_link"}
        for topic in self.curriculum["topics"]:
            with self.subTest(slug=topic["slug"]):
                blocks = authored_blocks(topic)
                self.assertEqual({block["type"] for block in blocks}, required)
                self.assertGreaterEqual(len(topic["objectives"]), 2)
                self.assertGreater(len(" ".join(block.get("value", "") for block in blocks if block["type"] == "text")), 1500)
                headings = [block["value"].casefold() for block in blocks if block["type"] == "heading"]
                for section in ("explanation", "worked example", "progressive practice", "interview question"):
                    self.assertTrue(any(section in heading for heading in headings))
                self.assertTrue(any(block.get("title") == "Next step" for block in blocks))
                self.assertGreaterEqual(sum(block["type"] == "resource_link" for block in blocks), 2)
                checks = [block for block in blocks if block["type"] == "knowledge_check"]
                self.assertGreaterEqual(len(checks), 2)
                for check in checks:
                    self.assertNotIn(check["id"], ids)
                    ids.add(check["id"])
                    self.assertIn(check["correct_index"], range(len(check["options"])))
                    self.assertTrue(check["concept_id"])

    def test_knowledge_answer_review(self):
        reviewed_indices = [(1, 2), (1, 0), (1, 0), (1, 2), (0, 1), (1, 2), (0, 1), (1, 1), (2, 0), (1, 0), (1, 2), (1, 0), (1, 2), (1, 0), (1, 2)]
        for topic, expected in zip(self.curriculum["topics"], reviewed_indices):
            checks = [block for block in authored_blocks(topic) if block["type"] == "knowledge_check"]
            self.assertEqual(tuple(check["correct_index"] for check in checks), expected, topic["slug"])

    def test_repeated_load_returns_independent_dicts(self):
        first = load_curriculum()
        first["topics"][0]["title"] = "changed"
        self.assertNotEqual(first, load_curriculum())

    def test_bad_schema_metadata_and_references(self):
        mutations = [
            lambda data: data.update(schema_version=True),
            lambda data: data.update(schema_version=2),
            lambda data: data.update(unknown="extra"),
            lambda data: data["topics"][0].pop("objectives"),
            lambda data: data["topics"][0].update(schema_version=1.0),
            lambda data: data["topics"][0].update(difficulty="easy"),
            lambda data: data["topics"][0].update(domain_slug="missing"),
            lambda data: data["topics"][0].update(order=True),
            lambda data: data["topics"][1].update(order=1),
            lambda data: data["topics"][0].update(prerequisites=[data["topics"][1]["slug"]]),
            lambda data: data["topics"][1].update(prerequisites=["missing"]),
            lambda data: data["domains"][0]["topics"].reverse(),
            lambda data: data["topics"].append(copy.deepcopy(data["topics"][0])),
            lambda data: data["domains"][0].update(schema_version=False),
        ]
        for position, mutate in enumerate(mutations):
            with self.subTest(mutation=position):
                data = copy.deepcopy(self.authored)
                mutate(data)
                with self.assertRaises(ValidationError):
                    Curriculum.model_validate(data)

    def test_bad_block_shapes_are_rejected(self):
        for replacement in (
            {"type": "code", "language": "python", "value": "print(1)"},
            {"type": "heading", "level": 8, "value": "bad"},
            {"type": "heading", "level": True, "value": "bad"},
            {"type": "list", "items": [], "ordered": False},
            {"type": "text", "value": "   "},
            {"type": "unknown", "value": "bad"},
            {"type": "text", "value": "valid", "url": "https://example.com"},
        ):
            data = copy.deepcopy(self.authored)
            data["topics"][0]["subtopics"][0]["content_blocks"][0] = replacement
            with self.subTest(replacement=replacement), self.assertRaises(ValidationError):
                Curriculum.model_validate(data)

    def test_bad_check_indices_and_duplicates(self):
        check = next(block for block in authored_blocks(self.curriculum["topics"][0]) if block["type"] == "knowledge_check")
        for invalid in (-1, 3, True, "1", 1.0):
            with self.subTest(index=invalid), self.assertRaises(ValidationError):
                KnowledgeCheck.model_validate({**check, "correct_index": invalid})
        with self.assertRaises(ValidationError):
            KnowledgeCheck.model_validate({**check, "options": ["same", " SAME "]})
        data = copy.deepcopy(self.authored)
        checks = [block for block in authored_blocks(data["topics"][0]) if block["type"] == "knowledge_check"]
        checks[1]["id"] = checks[0]["id"]
        with self.assertRaises(ValidationError):
            Curriculum.model_validate(data)

    def test_unsafe_urls_are_rejected(self):
        invalid_urls = [
            "javascript:alert(1)", "data:text/html,bad", "http://docs.python.org/3/",
            "https://evil.example/3/", "https://docs.python.org.evil.example/3/",
            "https://user@docs.python.org/3/", "https://docs.python.org:443/3/",
            "https://docs.python.org/3/?redirect=bad", "https://docs.python.org/3/\"onload=bad",
            "https://docs.python.org/3/%22", "https://docs.python.org/3/\\bad",
            "https://docs.python.org/3/\n", "//docs.python.org/3/",
        ]
        for url in invalid_urls:
            with self.subTest(url=url), self.assertRaises(ValidationError):
                ResourceLink.model_validate({"type": "resource_link", "label": "docs", "url": url})

    def test_duplicate_json_keys_and_no_runtime_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                load_curriculum(path)
            data = copy.deepcopy(self.authored)
            code = next(block for block in authored_blocks(data["topics"][0]) if block["type"] == "code")
            code["value"] = "raise RuntimeError('must not run during loading')"
            path.write_text(json.dumps(data), encoding="utf-8")
            with patch("subprocess.run", side_effect=AssertionError("loader must not launch processes")):
                self.assertEqual(load_curriculum(path)["topics"][0]["slug"], self.curriculum["topics"][0]["slug"])

    def run_authored(self, code, input_text=""):
        compile(code, "trusted-version-controlled-example", "exec")
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, "-X", "utf8", "-I", "-c", code],
                input=input_text, capture_output=True, text=True, encoding="utf-8",
                cwd=directory, timeout=10, check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        return completed.stdout.replace("\r\n", "\n")

    def test_all_trusted_lesson_code_stdout(self):
        for topic in self.curriculum["topics"]:
            for block in authored_blocks(topic):
                if block["type"] == "code":
                    with self.subTest(slug=topic["slug"]):
                        self.assertEqual(self.run_authored(block["value"]), block["expected_output"])

    def test_practice_count_topic_alignment_and_public_projection(self):
        self.assertEqual(len(self.practice), 15)
        self.assertEqual([problem["topic_slug"] for problem in self.practice], [topic["slug"] for topic in self.curriculum["topics"]])
        for problem in self.practice:
            with self.subTest(topic=problem["topic_slug"]):
                from bson import ObjectId
                self.assertEqual(str(ObjectId(problem["id"])), problem["id"])
                public = public_practice({**problem, "future_private_field": "secret"})
                self.assertNotIn("reference_solution", public)
                self.assertNotIn("future_private_field", public)
                compile(problem["starter_code"], "trusted-starter", "exec")

    def test_all_trusted_reference_solutions_stdout(self):
        for problem in self.practice:
            for position, case in enumerate(problem["test_cases"]):
                with self.subTest(topic=problem["topic_slug"], case=position):
                    self.assertEqual(self.run_authored(problem["reference_solution"], case["input"]), case["expected_output"])

    def test_invalid_practice_schema(self):
        mutations = [
            lambda data: data.update(schema_version=True),
            lambda data: data["practice_problems"][0].update(id="bad"),
            lambda data: data["practice_problems"][0].update(id="0" * 24),
            lambda data: data["practice_problems"][0].update(language="javascript"),
            lambda data: data["practice_problems"][0].pop("reference_solution"),
            lambda data: data["practice_problems"][0].update(test_cases=[]),
            lambda data: data["practice_problems"][0]["test_cases"][0].update(input=123),
            lambda data: data["practice_problems"].append(copy.deepcopy(data["practice_problems"][0])),
        ]
        for position, mutate in enumerate(mutations):
            with self.subTest(mutation=position):
                data = copy.deepcopy(self.practice_raw)
                mutate(data)
                with self.assertRaises(ValidationError):
                    PracticeCurriculum.model_validate(data)

    def test_reference_specific_mechanism_contracts(self):
        namespace = {"__name__": "trusted_reference_test"}
        exec(compile(self.practice[5]["reference_solution"], "trusted-combine", "exec"), namespace)
        base = [1]
        extras = [2]
        combined = namespace["combine"](base, extras)
        self.assertEqual((base, extras, combined), ([1], [2], [1, 2]))
        self.assertIsNot(combined, base)
        namespace = {"__name__": "trusted_reference_test"}
        exec(compile(self.practice[10]["reference_solution"], "trusted-generator", "exec"), namespace)
        def exploding_suffix():
            yield 2
            raise AssertionError("lazy generator consumed too much")
        stream = namespace["positive_totals"](exploding_suffix())
        self.assertEqual(next(stream), 2)


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.database = FakeDatabase()
        self.curriculum = load_curriculum()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.receipt = Path(self.directory.name) / "receipt.json"

    def apply(self):
        return import_curriculum(self.database, self.curriculum, apply=True, receipt_path=self.receipt, exclusive_writes=True)

    def test_default_preview_has_no_writes(self):
        report = import_curriculum(self.database, self.curriculum)
        self.assertEqual(report["mode"], "dry-run")
        self.assertEqual(len(report["operations"]), 16)
        for collection in self.database.collections.values():
            self.assertEqual(collection.insertions, [])
        self.assertFalse(self.receipt.exists())

    def test_apply_inserts_only_and_is_idempotent(self):
        unrelated = {"_id": "legacy-id", "slug": "legacy-rich", "subtopics": [{"content_blocks": [{"value": "valuable"}]}]}
        self.database["topics"].documents.append(copy.deepcopy(unrelated))
        report = self.apply()
        self.assertEqual(report["status"], "complete")
        self.assertEqual(len(report["insertions"]), 16)
        self.assertEqual(self.database["topics"].documents[0], unrelated)
        self.assertEqual(len(self.database["topics"].insertions), 15)
        self.assertEqual({item["action"] for item in preview_import(self.database, self.curriculum)["operations"]}, {"skip"})
        self.receipt = Path(self.directory.name) / "second.json"
        self.assertEqual(self.apply()["insertions"], [])
        self.assertEqual(len(self.database["topics"].insertions), 15)

    def test_existing_identical_doc_preserves_id_and_extra_fields(self):
        existing = {**copy.deepcopy(self.curriculum["topics"][0]), "_id": "valuable-existing-id", "private_note": "keep"}
        self.database["topics"].documents.append(existing)
        self.apply()
        self.assertEqual(self.database["topics"].documents[0], existing)
        self.assertEqual(len(self.database["topics"].insertions), 14)

    def test_conflict_fails_before_any_insert(self):
        existing = {"_id": "valuable", "slug": self.curriculum["topics"][-1]["slug"], "content_blocks": [{"type": "text", "value": "do not replace"}]}
        self.database["topics"].documents.append(copy.deepcopy(existing))
        self.assertEqual(preview_import(self.database, self.curriculum)["operations"][14]["action"], "conflict")
        with self.assertRaises(ImportConflict):
            self.apply()
        self.assertEqual(self.database["topics"].documents, [existing])
        self.assertEqual(self.database["domains"].insertions, [])
        self.assertFalse(self.receipt.exists())

    def test_duplicate_existing_slug_fails(self):
        topic = copy.deepcopy(self.curriculum["topics"][0])
        self.database["topics"].documents.extend([topic, copy.deepcopy(topic)])
        with self.assertRaises(ImportConflict):
            self.apply()

    def test_apply_requires_external_new_receipt_and_exclusive_window(self):
        with self.assertRaises(ValueError):
            import_curriculum(self.database, self.curriculum, apply=True)
        with self.assertRaises(ValueError):
            import_curriculum(self.database, self.curriculum, apply=True, exclusive_writes=True)
        with self.assertRaises(ValueError):
            import_curriculum(self.database, self.curriculum, apply=True, exclusive_writes=True, receipt_path=DEFAULT_PATH.parent / "recovery.json")
        self.receipt.write_text("preserve existing receipt", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.apply()
        self.assertEqual(self.receipt.read_text(encoding="utf-8"), "preserve existing receipt")
        self.assertEqual(self.database["topics"].insertions, [])

    def test_partial_failure_has_receipt_and_never_inserts_domain(self):
        self.database["topics"].fail_insert = True
        with self.assertRaises(RuntimeError):
            self.apply()
        report = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "incomplete")
        self.assertEqual(report["insertions"][0]["status"], "pending")
        self.assertEqual(self.database["domains"].insertions, [])

    def test_invalid_source_rejected_before_database_reads(self):
        self.curriculum["topics"][0]["order"] = "1"
        with self.assertRaises(ValidationError):
            preview_import(self.database, self.curriculum)

    def test_cli_help_and_incomplete_apply_never_connect(self):
        with patch("sys.stdout", new_callable=io.StringIO), self.assertRaises(SystemExit) as help_exit:
            main(["--help"])
        self.assertEqual(help_exit.exception.code, 0)
        with patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit) as apply_exit:
            main(["--apply"])
        self.assertEqual(apply_exit.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
