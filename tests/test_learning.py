import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from bson import ObjectId
from fastapi import FastAPI, HTTPException
import httpx
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError


ROOT = Path(__file__).resolve().parents[1]
fake_database = ModuleType("backend.database")
fake_database.get_collection = MagicMock()
fake_curriculum = ModuleType("backend.curriculum")
fake_curriculum.load_curriculum = MagicMock(return_value={"topics": []})
fake_auth = ModuleType("backend.auth")


async def require_authentication():
    raise HTTPException(status_code=401, detail="Authentication required")


fake_auth.get_current_user = require_authentication


def load_module(name, path, dependencies):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict("sys.modules", dependencies):
        spec.loader.exec_module(module)
    return module


mastery = load_module("mastery_under_test", "backend/mastery.py", {
    "backend.database": fake_database, "backend.curriculum": fake_curriculum,
})
learning = load_module("learning_under_test", "backend/routes/learning.py", {
    "backend.database": fake_database, "backend.auth": fake_auth, "backend.mastery": mastery,
})


def quiz(block_id, concept_id, correct_index=1):
    return {
        "type": "knowledge_check", "id": block_id, "concept_id": concept_id,
        "question": "Question " + block_id, "options": ["First", "Second"],
        "correct_index": correct_index, "explanation": "Protected explanation " + block_id,
    }


def lesson(coding_required=True):
    return {
        "slug": "python-basics", "mastery_policy": {"coding_required": coding_required},
        "subtopics": [
            {"title": "Names", "content_blocks": [quiz("names-one", "names"), quiz("names-two", "names")]},
            {"title": "Types", "content_blocks": [quiz("types-one", "types")]},
        ],
    }


def evidence(kind, source_id, score=100, concept_id=None, days=0):
    return {
        "kind": kind, "source_id": source_id, "score": score, "concept_id": concept_id,
        "recorded_at": datetime.now(timezone.utc) - timedelta(days=days),
    }


def passing_quizzes(days=0):
    return [evidence("quiz", "names-one", concept_id="names", days=days),
            evidence("quiz", "names-two", concept_id="names", days=days),
            evidence("quiz", "types-one", concept_id="types", days=days)]


class MasteryHeuristicTests(unittest.TestCase):
    def summary(self, items, topic=None, now=None):
        return mastery.summarize_mastery(topic or lesson(), {"evidence": items}, now=now)

    def test_reading_and_coding_alone_never_master(self):
        for items in ([], [evidence("reading", "lesson")], [evidence("coding", "problem")]):
            with self.subTest(items=items):
                result = self.summary(items)
                self.assertNotEqual(result["status"], "mastered")
                self.assertEqual(result["quiz_score"], None)
                self.assertEqual(result["next_activity"]["kind"], "quiz")

    def test_quizzes_need_verified_coding_for_default_lessons(self):
        result = self.summary(passing_quizzes())
        self.assertEqual(result["status"], "review")
        self.assertEqual(result["score"], 50)
        self.assertEqual(result["next_activity"]["kind"], "coding")

    def test_quiz_and_coding_thresholds_are_independent(self):
        for score, status in ((79.9999, "weak"), (80, "mastered"), (100, "mastered")):
            with self.subTest(score=score):
                result = self.summary(passing_quizzes() + [evidence("coding", "problem", score)])
                self.assertEqual(result["status"], status)

    def test_noncoding_requires_three_distinct_quizzes(self):
        topic = lesson(coding_required=False)
        result = self.summary(passing_quizzes()[:2], topic)
        self.assertNotEqual(result["status"], "mastered")
        self.assertEqual(result["minimum_quizzes"], 3)
        self.assertEqual(self.summary(passing_quizzes(), topic)["status"], "mastered")

    def test_noncoding_policy_ignores_optional_coding_scores(self):
        result = self.summary(passing_quizzes() + [evidence("coding", "optional", 0, "names")], lesson(False))
        self.assertEqual(result["status"], "mastered")
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["concepts"][0]["score"], 100)

    def test_reading_does_not_refresh_expired_assessments(self):
        result = self.summary(passing_quizzes(days=15) + [evidence("reading", "lesson")], lesson(False))
        self.assertNotEqual(result["status"], "mastered")
        self.assertEqual(result["quiz_score"], None)

    def test_canonical_key_is_scoped_and_accepts_object_id(self):
        user_id = ObjectId()
        self.assertEqual(mastery.mastery_key(user_id, "first"), mastery.mastery_key(str(user_id), "first"))
        self.assertNotEqual(mastery.mastery_key(user_id, "first")["_id"], mastery.mastery_key(user_id, "second")["_id"])
        self.assertNotEqual(mastery.mastery_key(user_id, "first")["_id"], mastery.mastery_key(ObjectId(), "first")["_id"])

    def test_all_known_concepts_must_have_fresh_passing_quizzes(self):
        items = passing_quizzes()[:2] + [evidence("coding", "problem")]
        result = self.summary(items)
        self.assertEqual(result["minimum_concepts"], 2)
        self.assertNotEqual(result["status"], "mastered")
        self.assertEqual(result["concepts"][1]["status"], "review")
        self.assertEqual(result["next_activity"]["source_id"], "types-one")

    def test_single_concept_lessons_still_need_distinct_checks(self):
        topic = lesson()
        topic["subtopics"] = topic["subtopics"][:1]
        result = self.summary(passing_quizzes()[:2] + [evidence("coding", "problem")], topic)
        self.assertEqual(result["minimum_concepts"], 1)
        self.assertEqual(result["status"], "mastered")

    def test_last_evidence_replaces_source_not_repetition_count(self):
        repeated = [evidence("quiz", "names-one", concept_id="names") for index in range(20)]
        result = self.summary(repeated, lesson(False))
        self.assertEqual(result["evidence_counts"]["quiz"], 1)
        self.assertNotEqual(result["status"], "mastered")
        repeated.append(evidence("quiz", "names-one", 0, "names"))
        result = self.summary(repeated)
        self.assertEqual(result["quiz_score"], 0)
        self.assertEqual(len(result["missed_questions"]), 1)

    def test_successful_retry_removes_missed_question(self):
        items = [evidence("quiz", "names-one", 0, "names"), evidence("quiz", "names-one", 100, "names")]
        self.assertEqual(self.summary(items)["missed_questions"], [])

    def test_stale_evidence_requires_reassessment_without_rewriting_storage(self):
        items = passing_quizzes(days=15) + [evidence("coding", "problem", days=15)]
        original = deepcopy(items)
        result = self.summary(items)
        self.assertEqual(result["status"], "review")
        self.assertEqual(result["evidence_counts"]["quiz"], 0)
        self.assertTrue(any("14 days" in reason for reason in result["reasons"]))
        self.assertEqual(items, original)

    def test_exact_expiry_and_mongo_naive_utc_timestamps(self):
        now = datetime(2026, 10, 11, tzinfo=timezone.utc)
        items = passing_quizzes() + [evidence("coding", "problem")]
        for item in items:
            item["recorded_at"] = (now - timedelta(days=14) + timedelta(seconds=1)).replace(tzinfo=None)
        self.assertEqual(self.summary(items, now=now)["status"], "mastered")
        self.assertEqual(self.summary(items, now=now + timedelta(seconds=1))["status"], "review")

    def test_bad_timestamps_scores_and_unknown_sources_do_not_grant_mastery(self):
        items = [evidence("quiz", "not-a-check", concept_id="names")]
        for score in (float("nan"), float("inf"), -1, 101, True, "100"):
            items.append(evidence("quiz", "names-one", score, "names"))
        items.append(evidence("quiz", "types-one", concept_id="wrong-concept"))
        valid = evidence("quiz", "names-two", concept_id="names")
        valid["recorded_at"] = "not a date"
        items.append(valid)
        self.assertNotEqual(self.summary(items)["status"], "mastered")
        self.assertEqual(self.summary(items)["evidence_counts"]["quiz"], 0)

    def test_future_evidence_does_not_grant_mastery(self):
        items = passing_quizzes(days=-1) + [evidence("coding", "problem", days=-1)]
        self.assertNotEqual(self.summary(items)["status"], "mastered")

    def test_concept_coding_scores_cannot_hide_failed_concept_quiz(self):
        items = passing_quizzes()
        items[-1]["score"] = 0
        result = self.summary(items + [evidence("coding", "problem", concept_id="types")])
        concept = result["concepts"][1]
        self.assertEqual(concept["score"], 50)
        self.assertEqual(concept["status"], "weak")
        self.assertTrue(concept["reasons"])

    def test_legacy_coordinates_use_all_blocks_and_zero_based_subtopics(self):
        topic = lesson()
        topic["content_blocks"] = [quiz("top", "top")]
        topic["subtopics"][0]["content_blocks"].insert(0, {"type": "text", "value": "Read"})
        for section in [topic] + topic["subtopics"]:
            for block in section.get("content_blocks", []):
                block.pop("id", None)
                block.pop("concept_id", None)
        checks = mastery.serialize_checks(topic)
        self.assertEqual(checks[0]["id"], "legacy:topic:block:0")
        self.assertEqual(checks[1]["block_id"], "legacy:subtopic:0:block:1")
        self.assertEqual(checks[-1]["concept_id"], "legacy:subtopic:1")
        self.assertEqual(checks, mastery.serialize_checks(topic))

    def test_explicit_ids_and_section_concepts_take_precedence(self):
        topic = lesson()
        block = topic["subtopics"][0]["content_blocks"][0]
        block["block_id"] = "canonical"
        del block["concept_id"]
        topic["subtopics"][0]["concept_id"] = "section-concept"
        check = mastery.serialize_checks(topic)[0]
        self.assertEqual(check["id"], "canonical")
        self.assertEqual(check["concept_id"], "section-concept")

    def test_public_serializer_whitelists_without_mutation(self):
        topic = lesson()
        block = topic["subtopics"][0]["content_blocks"][0]
        block["answer"] = "Other hidden metadata"
        original = deepcopy(topic)
        checks = mastery.serialize_checks(topic)
        self.assertEqual(topic, original)
        for check in checks:
            self.assertNotIn("correct_index", check)
            self.assertNotIn("explanation", check)
            self.assertNotIn("answer", check)

    def test_duplicate_ids_and_invalid_answer_content_fail_closed(self):
        for change in ({"id": "names-one"}, {"correct_index": True}, {"correct_index": 2}, {"options": ["Only"]}):
            topic = lesson()
            topic["subtopics"][1]["content_blocks"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                mastery.topic_checks(topic)


class EvidenceStore:
    """Mock the atomic command, not a live MongoDB connection."""
    def __init__(self):
        self.documents = {}
        self.find_one = AsyncMock(side_effect=self.read)
        self.find_one_and_update = AsyncMock(side_effect=self.write)

    async def read(self, query):
        document = self.documents.get(query["_id"])
        if document is None or any(document.get(name) != value for name, value in query.items()):
            return None
        return deepcopy(document)

    async def write(self, query, pipeline, upsert, return_document):
        self.last_pipeline = pipeline
        document = self.documents.get(query["_id"])
        if document is None and not upsert:
            return None
        if document is not None and any(document.get(name) != value for name, value in query.items()):
            return None
        document = deepcopy(document or query)
        values = pipeline[0]["$set"]
        append = values["evidence"]["$slice"][0]["$concatArrays"][1][0]
        now = datetime.now(timezone.utc)
        item = {name: value["$literal"] if isinstance(value, dict) else now if value == "$$NOW" else value
                for name, value in append.items()}
        document["evidence"] = [previous for previous in document.get("evidence", [])
                                if (previous["kind"], previous["source_id"]) != (item["kind"], item["source_id"])]
        document["evidence"] = (document["evidence"] + [item])[-mastery.MAX_EVIDENCE:]
        document.update({"updated_at": now, "schema_version": 1})
        self.documents[query["_id"]] = document
        return deepcopy(document)


class LearningTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.topic = lesson()
        self.user_id = str(ObjectId())
        self.other_user_id = str(ObjectId())
        self.store = EvidenceStore()
        self.topics = SimpleNamespace(find_one=AsyncMock(side_effect=lambda query: deepcopy(self.topic) if query["slug"] == self.topic["slug"] else None))
        self.collections = {"topics": self.topics, "user_mastery": self.store}
        for module in (mastery, learning):
            patcher = patch.object(module, "get_collection", side_effect=self.collections.__getitem__)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.curriculum_patch = patch.object(mastery, "load_curriculum", return_value={"topics": []})
        self.curriculum_loader = self.curriculum_patch.start()
        self.addCleanup(self.curriculum_patch.stop)
        self.app = FastAPI()
        self.app.include_router(learning.router)
        self.app.dependency_overrides[learning.get_current_user] = lambda: {"id": self.user_id}
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test")
        self.addAsyncCleanup(self.client.aclose)

    async def record(self, kind="quiz", score=100, source="names-one", concept="names", user_id=None):
        return await mastery.record_evidence(user_id or self.user_id, self.topic["slug"], kind, score, source, concept)

    async def test_server_grades_and_records_canonical_concept(self):
        response = await self.client.post("/learning/python-basics/check", json={"block_id": "names-one", "selected_index": 1})
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["correct"])
        self.assertEqual(result["explanation"], "Protected explanation names-one")
        document = next(iter(self.store.documents.values()))
        self.assertEqual(document["user_id"], ObjectId(self.user_id))
        self.assertEqual(document["evidence"][0]["score"], 100)
        self.assertEqual(document["evidence"][0]["concept_id"], "names")

    async def test_legacy_check_can_be_graded_with_returned_identity(self):
        block = self.topic["subtopics"][0]["content_blocks"][0]
        del block["id"]
        del block["concept_id"]
        checks = (await self.client.get("/learning/python-basics/checks")).json()["checks"]
        response = await self.client.post("/learning/python-basics/check", json={"block_id": checks[0]["id"], "selected_index": 1})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["correct"])
        document = next(iter(self.store.documents.values()))
        self.assertEqual(document["evidence"][0]["source_id"], "legacy:subtopic:0:block:0")
        self.assertEqual(document["evidence"][0]["concept_id"], "legacy:subtopic:0")

    async def test_incorrect_answer_returns_explanation_and_user_missed_question(self):
        response = await self.client.post("/learning/python-basics/check", json={"block_id": "names-one", "selected_index": 0})
        self.assertFalse(response.json()["correct"])
        result = (await self.client.get("/learning/python-basics/mastery")).json()
        self.assertEqual(result["status"], "weak")
        self.assertEqual(result["missed_questions"][0]["block_id"], "names-one")
        self.assertNotIn("correct_index", result["missed_questions"][0])
        self.assertNotIn("explanation", result["missed_questions"][0])
        self.store.find_one.assert_awaited_with(mastery.mastery_key(self.user_id, "python-basics"))

    async def test_checks_are_answer_free_and_authenticated(self):
        response = await self.client.get("/learning/python-basics/checks")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["checks"]), 3)
        self.assertNotIn("correct_index", response.text)
        self.assertNotIn("Protected explanation", response.text)
        self.app.dependency_overrides.clear()
        self.topics.find_one.reset_mock()
        for method, path, kwargs in (
            ("GET", "checks", {}), ("GET", "mastery", {}),
            ("POST", "check", {"json": {"block_id": "names-one", "selected_index": 1}}),
        ):
            response = await self.client.request(method, "/learning/python-basics/" + path, **kwargs)
            self.assertEqual(response.status_code, 401)
        self.topics.find_one.assert_not_called()
        self.store.find_one_and_update.assert_not_called()

    async def test_strict_request_rejects_spoofing_and_bad_indices(self):
        requests = [{"block_id": "names-one", "selected_index": value} for value in (True, "1", 1.0, -1, 20, 2)]
        requests.extend((
            {"block_id": "names-one", "selected_index": 1, "score": 100},
            {"block_id": "names-one", "selected_index": 1, "user_id": self.other_user_id},
            {"block_id": "names-one", "selected_index": 1, "correct_index": 1},
            {"block_id": "", "selected_index": 1},
        ))
        for payload in requests:
            with self.subTest(payload=payload):
                response = await self.client.post("/learning/python-basics/check", json=payload)
                self.assertEqual(response.status_code, 422)
        self.store.find_one_and_update.assert_not_called()

    async def test_missing_topic_check_and_bad_catalog_have_no_write(self):
        response = await self.client.get("/learning/missing/checks")
        self.assertEqual(response.status_code, 404)
        response = await self.client.post("/learning/python-basics/check", json={"block_id": "unknown", "selected_index": 1})
        self.assertEqual(response.status_code, 404)
        self.topic["subtopics"][0]["content_blocks"][0]["correct_index"] = True
        response = await self.client.get("/learning/python-basics/checks")
        self.assertEqual(response.status_code, 503)
        self.store.find_one_and_update.assert_not_called()

    async def test_builtin_fallback_supplies_full_trusted_data_for_all_routes(self):
        self.topics.find_one.side_effect = None
        self.topics.find_one.return_value = None
        self.curriculum_loader.return_value = {"topics": [deepcopy(self.topic)]}
        response = await self.client.get("/learning/python-basics/checks")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("explanation", response.text)
        response = await self.client.post("/learning/python-basics/check", json={"block_id": "names-one", "selected_index": 1})
        self.assertTrue(response.json()["correct"])
        self.assertEqual(response.json()["explanation"], "Protected explanation names-one")
        response = await self.client.get("/learning/python-basics/mastery")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["quiz_score"], 100)

    async def test_db_topic_wins_and_db_errors_never_become_fallback_success(self):
        await self.client.get("/learning/python-basics/checks")
        self.curriculum_loader.assert_not_called()
        self.topics.find_one.side_effect = ServerSelectionTimeoutError("mock failure")
        with self.assertRaises(ServerSelectionTimeoutError):
            await mastery.load_topic("python-basics")
        self.curriculum_loader.assert_not_called()

    async def test_unavailable_fallback_returns_sanitized_503(self):
        self.topics.find_one.side_effect = None
        self.topics.find_one.return_value = None
        self.curriculum_loader.side_effect = ValueError("private file details")
        response = await self.client.get("/learning/python-basics/checks")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private", response.text)

    async def test_all_personal_reads_and_writes_are_user_and_topic_scoped(self):
        await self.record(score=0)
        await self.record(user_id=self.other_user_id, source="types-one", concept="types", score=0)
        response = await self.client.get("/learning/python-basics/mastery")
        self.assertEqual([item["block_id"] for item in response.json()["missed_questions"]], ["names-one"])
        self.user_id = self.other_user_id
        response = await self.client.get("/learning/python-basics/mastery")
        self.assertEqual([item["block_id"] for item in response.json()["missed_questions"]], ["types-one"])
        for call in self.store.find_one_and_update.await_args_list + self.store.find_one.await_args_list:
            self.assertIn("user_id", call.args[0])
            self.assertEqual(call.args[0]["topic_slug"], "python-basics")
        self.assertEqual(len(self.store.documents), 2)

    async def test_atomic_pipeline_has_bounded_filter_replace_and_literal_values(self):
        await self.record(kind="coding", source="$special", concept=None)
        call = self.store.find_one_and_update.await_args
        query, pipeline = call.args
        self.assertEqual(query, mastery.mastery_key(self.user_id, "python-basics"))
        self.assertEqual(call.kwargs, {"upsert": True, "return_document": ReturnDocument.AFTER})
        expression = pipeline[0]["$set"]["evidence"]["$slice"]
        self.assertEqual(expression[1], -64)
        filtered, appended = expression[0]["$concatArrays"]
        self.assertEqual(filtered["$filter"]["input"], {"$ifNull": ["$evidence", []]})
        self.assertEqual(filtered["$filter"]["cond"], {"$not": [{"$and": [
            {"$eq": ["$$item.kind", {"$literal": "coding"}]},
            {"$eq": ["$$item.source_id", {"$literal": "$special"}]},
        ]}]})
        self.assertEqual(appended[0]["source_id"], {"$literal": "$special"})
        self.assertEqual(appended[0]["recorded_at"], "$$NOW")
        self.store.find_one.assert_not_called()

    async def test_replacement_and_concurrent_distinct_sources_remain_bounded(self):
        await asyncio.gather(*(self.record(kind="coding", source="problem-" + str(index), concept=None)
                               for index in range(70)))
        document = next(iter(self.store.documents.values()))
        self.assertEqual(len(document["evidence"]), 64)
        self.assertEqual(document["evidence"][0]["source_id"], "problem-6")
        await self.record(kind="coding", source="problem-69", score=0, concept=None)
        document = next(iter(self.store.documents.values()))
        self.assertEqual(len(document["evidence"]), 64)
        self.assertEqual(document["evidence"][-1]["score"], 0)
        self.assertEqual(len({(item["kind"], item["source_id"]) for item in document["evidence"]}), 64)

    async def test_initial_upsert_race_retries_once_with_same_scoped_key(self):
        real_write = self.store.write
        await self.record()
        existing = next(iter(self.store.documents.values()))
        self.store.find_one_and_update.reset_mock()
        self.store.find_one_and_update.side_effect = [DuplicateKeyError("mock race"), deepcopy(existing)]
        await self.record()
        calls = self.store.find_one_and_update.await_args_list
        self.assertEqual(calls[0].args, calls[1].args)
        self.assertTrue(calls[0].kwargs["upsert"])
        self.assertFalse(calls[1].kwargs["upsert"])
        self.store.find_one_and_update.side_effect = real_write

    async def test_failed_race_recovery_never_falls_back_to_unscoped_read(self):
        self.store.find_one_and_update.side_effect = [DuplicateKeyError("mock race"), None]
        with self.assertRaisesRegex(RuntimeError, "could not be recorded"):
            await self.record()
        self.store.find_one.assert_not_called()

    async def test_public_api_validates_evidence_and_catalog_identity(self):
        for overrides in (
            {"kind": "client-grade"}, {"score": True}, {"score": float("nan")}, {"score": -1}, {"score": 101},
            {"source_id": ""}, {"source_id": "invented"}, {"concept_id": "wrong"}, {"user_id": "invalid"},
        ):
            arguments = {"user_id": self.user_id, "topic_slug": "python-basics", "kind": "quiz",
                         "score": 100, "source_id": "names-one", "concept_id": "names"}
            arguments.update(overrides)
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                await mastery.record_evidence(**arguments)
        self.store.find_one_and_update.assert_not_called()

    async def test_practice_agent_can_call_public_api_without_concept(self):
        result = await mastery.record_evidence(self.user_id, "python-basics", "coding", 80, "problem-id")
        self.assertEqual(result["coding_score"], 80)
        self.assertNotEqual(result["status"], "mastered")


if __name__ == "__main__":
    unittest.main()
