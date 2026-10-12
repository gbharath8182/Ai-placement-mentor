import asyncio
import copy
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pymongo.errors import OperationFailure

from backend.ai_provider import AIProviderError, GroqProvider
from backend.routes import mock_interview as interview
from backend.routes import domain_details
from backend.curriculum import load_curriculum


USER = {"id": "candidate-one"}
OTHER_USER = {"id": "candidate-two"}
QUESTION = {"question": "How do you detect duplicates?", "category": "coding", "difficulty": "beginner"}
GRADE = {
    "assessment": "partial", "rubric_scores": {"correctness": 6, "reasoning": 4, "edge_cases": 2, "clarity": 8},
    "strengths": ["Recognizes the lookup operation"], "weaknesses": ["Missing complexity justification"],
    "model_answer_hint": "Track prior values in a set and justify expected linear time.",
    "misconception": "Complexity was not justified.", "next_practice": "Trace the set on [1,2,2].",
    "clarification_question": "",
}
TEACHING = {
    "ideal_answer": "Use a seen set.", "reasoning": ["Look up before inserting."],
    "misconceptions": ["Insertion before checking marks every value as seen."],
    "worked_example": "[1,2,2] returns true on the third value.",
    "next_practice": "Try an empty array.", "check_understanding": "Why check before inserting?",
}
BENCHMARK = json.loads((Path(__file__).resolve().parents[1] / "curriculum" / "interview-benchmark.json").read_text(encoding="utf-8"))


class FakeCursor:
    def __init__(self, documents):
        self.documents = copy.deepcopy(documents)
        self.maximum = len(documents)
        self.timeout = None

    def limit(self, maximum):
        self.maximum = maximum
        return self

    def max_time_ms(self, timeout):
        self.timeout = timeout
        return self

    def __aiter__(self):
        async def iterate():
            for document in self.documents[:self.maximum]:
                yield copy.deepcopy(document)
        return iterate()


class FakeCollection:
    def __init__(self, documents=()):
        self.documents = {document["_id"]: copy.deepcopy(document) for document in documents}
        self.queries = []
        self.updates = []
        self.cursors = []

    async def find_one(self, query, **kwargs):
        self.queries.append(copy.deepcopy(query))
        return next((copy.deepcopy(document) for document in self.documents.values()
                     if all(document.get(key) == value for key, value in query.items())), None)

    def find(self, query=None, projection=None):
        query = query or {}
        self.queries.append(copy.deepcopy(query))
        cursor = FakeCursor([document for document in self.documents.values()
                             if all(document.get(key) == value for key, value in query.items())])
        self.cursors.append(cursor)
        return cursor

    async def insert_one(self, document):
        if document["_id"] in self.documents:
            raise AssertionError("Duplicate session id")
        self.documents[document["_id"]] = copy.deepcopy(document)
        return SimpleNamespace(inserted_id=document["_id"])

    async def update_one(self, query, update):
        self.updates.append((copy.deepcopy(query), copy.deepcopy(update)))
        for document in self.documents.values():
            if all(document.get(key) == value for key, value in query.items()):
                document.update(copy.deepcopy(update["$set"]))
                for key, value in update.get("$inc", {}).items():
                    document[key] += value
                return SimpleNamespace(modified_count=1)
        return SimpleNamespace(modified_count=0)


class InterviewTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.collections = {
            "interview_sessions": FakeCollection(),
            "domain_details": FakeCollection([{"_id": "domain", "domain_slug": "python", "interview_prep": {}}]),
            "domains": FakeCollection(),
            "topics": FakeCollection(),
        }
        self.sessions = self.collections["interview_sessions"]
        self.replace(interview, "get_collection", self.collections.__getitem__)
        self.replace(domain_details, "get_collection", self.collections.__getitem__)
        self.ai = SimpleNamespace(structured=AsyncMock(side_effect=self.valid_structured))
        self.replace(interview, "provider", self.ai)

    def replace(self, target, name, value):
        replacement = patch.object(target, name, value)
        replacement.start()
        self.addCleanup(replacement.stop)

    async def valid_structured(self, messages, schema, model=None):
        if issubclass(schema, interview.InterviewGrade):
            payload = GRADE
        elif schema is interview.InterviewTeaching:
            payload = TEACHING
        else:
            difficulty = next(level for level in interview.DIFFICULTY_LEVELS
                              if "required difficulty: " + level in messages[0]["content"])
            category = "hr" if "Requested mode: hr" in messages[0]["content"] else "coding"
            payload = {**QUESTION, "question": "Question for " + difficulty, "category": category, "difficulty": difficulty}
        return schema.model_validate(payload), "actual-model"

    def seed(self, total=2, mode="coding", category="coding"):
        session = {
            "_id": "session-one", "user_id": USER["id"], "domain_slug": "python", "mode": mode,
            "num_questions": total, "index": 0, "version": 0, "status": "active",
            "questions_asked": [{**QUESTION, "category": category}], "results": [],
            "_domain_doc": {"domain_slug": "python", "interview_prep": {}},
        }
        self.sessions.documents[session["_id"]] = copy.deepcopy(session)
        return session

    def request(self, answer="Use a set", question_number=1):
        return interview.MockInterviewAnswerRequest(session_id="session-one", answer=answer, question_number=question_number)

    def transport(self, responses):
        bodies = []
        remaining = iter(responses)

        def handle(request):
            self.assertEqual(request.url.host, "api.groq.com")
            bodies.append(json.loads(request.content))
            return httpx.Response(200, json={"choices": [{"message": {"content": next(remaining)}, "finish_reason": "stop"}]})

        self.replace(interview, "provider", GroqProvider(httpx.MockTransport(handle)))
        self.replace(interview.settings, "GROQ_API_KEY", "offline-test-key")
        self.replace(interview.settings, "GROQ_MAX_RETRIES", 0)
        return bodies

    def client(self):
        app = FastAPI()
        app.include_router(interview.router)
        app.dependency_overrides[interview.get_current_user] = lambda: USER
        return TestClient(app)

    async def test_start_persists_session_and_reports_actual_model(self):
        result = await interview.start_mock_interview(interview.MockInterviewStartRequest(domain_slug="python", mode="coding"), USER)
        stored = self.sessions.documents[result["session_id"]]
        self.assertEqual(stored["user_id"], USER["id"])
        self.assertEqual(stored["version"], 0)
        self.assertEqual(stored["status"], "active")
        self.assertEqual(stored["questions_asked"][0]["question"], result["question"])
        self.assertEqual(result["generated_by_model"], "actual-model")
        self.assertFalse(hasattr(interview, "interview_sessions"))

    async def test_failed_start_does_not_persist_or_return_demo(self):
        self.ai.structured.side_effect = AIProviderError("not_configured", "AI is not configured", False)
        with self.assertRaises(AIProviderError) as caught:
            await interview.start_mock_interview(interview.MockInterviewStartRequest(domain_slug="python", mode="coding"), USER)
        self.assertEqual(caught.exception.kind, "not_configured")
        self.assertFalse(self.sessions.documents)

    async def test_unknown_domain_does_not_call_ai(self):
        with self.assertRaises(HTTPException) as caught:
            await interview.start_mock_interview(interview.MockInterviewStartRequest(domain_slug="unknown"), USER)
        self.assertEqual(caught.exception.status_code, 404)
        self.ai.structured.assert_not_awaited()

    async def test_builtin_domain_is_listed_and_starts_without_mongo_import(self):
        curriculum = load_curriculum()
        domain = next(domain for domain in curriculum["domains"] if domain["slug"] == "python-foundations")
        original = copy.deepcopy(curriculum)
        self.replace(domain_details, "builtin_curriculum", lambda: curriculum)
        self.replace(interview, "builtin_curriculum", lambda: curriculum)
        picker = await domain_details.list_domains_with_details()
        published = next(item for item in picker if item["slug"] == domain["slug"])
        self.assertEqual(published["title"], domain["title"])
        self.assertFalse(published["has_detailed_content"])
        response = await interview.start_mock_interview(
            interview.MockInterviewStartRequest(domain_slug=domain["slug"], mode="coding"), USER,
        )
        context = self.sessions.documents[response["session_id"]]["_domain_doc"]
        self.assertEqual(context["title"], domain["title"])
        self.assertEqual(context["topics"], [{"name": topic["title"]} for topic in curriculum["topics"]
                                            if topic["domain_slug"] == domain["slug"]][:50])
        self.assertEqual(curriculum, original)
        self.assertEqual(self.collections["domains"].cursors[0].maximum, 100)
        self.assertEqual(self.collections["domain_details"].cursors[0].maximum, 1000)
        self.assertEqual(self.collections["topics"].cursors[0].maximum, 50)
        for collection in ["domains", "domain_details", "topics"]:
            self.assertEqual(self.collections[collection].cursors[0].timeout, 5000)

    async def test_mongo_domain_and_topic_titles_override_matching_builtin_entries(self):
        curriculum = load_curriculum()
        domain = next(domain for domain in curriculum["domains"] if domain["slug"] == "python-foundations")
        topic = next(topic for topic in curriculum["topics"] if topic["domain_slug"] == domain["slug"])
        self.collections["domains"].documents["mongo-domain"] = {"_id": "mongo-domain", "slug": domain["slug"], "title": "Mongo domain priority"}
        self.collections["topics"].documents["mongo-topic"] = {"_id": "mongo-topic", "slug": topic["slug"], "domain_slug": domain["slug"], "title": "Mongo topic priority"}
        picker = await domain_details.list_domains_with_details()
        matching = [item for item in picker if item["slug"] == domain["slug"]]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["title"], "Mongo domain priority")
        response = await interview.start_mock_interview(interview.MockInterviewStartRequest(domain_slug=domain["slug"], mode="coding"), USER)
        context = self.sessions.documents[response["session_id"]]["_domain_doc"]
        self.assertEqual(context["title"], "Mongo domain priority")
        self.assertEqual(context["topics"][0], {"name": "Mongo topic priority"})
        self.assertNotIn({"name": topic["title"]}, context["topics"])

    async def test_detailed_mongo_domain_does_not_load_builtin_context(self):
        unexpected = lambda: self.fail("Existing detailed Mongo context must take priority")
        self.replace(interview, "builtin_curriculum", unexpected)
        response = await interview.start_mock_interview(interview.MockInterviewStartRequest(domain_slug="python", mode="coding"), USER)
        self.assertEqual(self.sessions.documents[response["session_id"]]["_domain_doc"]["_id"], "domain")
        self.assertFalse(self.collections["domains"].queries)
        self.assertFalse(self.collections["topics"].queries)

    async def test_builtin_domain_never_masks_database_read_failures(self):
        for collection_name in ["domain_details", "domains", "topics"]:
            with self.subTest(collection=collection_name):
                collection = self.collections[collection_name]
                method = "find" if collection_name == "topics" else "find_one"
                failure = OperationFailure("Private database unavailable")
                replacement = AsyncMock(side_effect=failure) if method == "find_one" else Mock(side_effect=failure)
                with patch.object(collection, method, replacement):
                    with self.assertRaises(OperationFailure):
                        await interview.start_mock_interview(interview.MockInterviewStartRequest(domain_slug="python-foundations", mode="coding"), USER)
        self.assertFalse(self.sessions.documents)
        self.ai.structured.assert_not_awaited()

    async def test_builtin_picker_never_masks_database_failures(self):
        for collection_name in ["domain_details", "domains"]:
            with self.subTest(collection=collection_name):
                with patch.object(self.collections[collection_name], "find", side_effect=OperationFailure("Private database unavailable")):
                    with self.assertRaises(OperationFailure):
                        await domain_details.list_domains_with_details()

    async def test_all_session_operations_are_user_scoped(self):
        self.seed()
        operations = [
            (interview.submit_mock_interview_answer, self.request()),
            (interview.end_mock_interview, interview.EndInterviewRequest(session_id="session-one")),
            (interview.explain_more, interview.ExplainMoreRequest(session_id="session-one")),
        ]
        for endpoint, payload in operations:
            with self.subTest(endpoint=endpoint.__name__):
                with self.assertRaises(HTTPException) as caught:
                    await endpoint(payload, OTHER_USER)
                self.assertEqual(caught.exception.status_code, 404)
                self.assertEqual(self.sessions.queries[-1], {"_id": "session-one", "user_id": OTHER_USER["id"]})
        self.assertFalse(self.sessions.updates)
        self.ai.structured.assert_not_awaited()

    async def test_invalid_questions_fall_back_through_provider(self):
        malformed = [
            "not json", json.dumps({**QUESTION, "category": "unsupported"}),
            json.dumps({**QUESTION, "question": " "}), json.dumps({"question": "Question", "category": "coding"}),
            json.dumps({**QUESTION, "difficulty": "advanced"}), json.dumps({**QUESTION, "category": "hr"}),
            json.dumps({**QUESTION, "surprise": "extra field"}),
        ]
        for bad in malformed:
            with self.subTest(response=bad):
                bodies = self.transport([bad, json.dumps(QUESTION)])
                result = await interview.start_mock_interview(interview.MockInterviewStartRequest(domain_slug="python", mode="coding"), USER)
                self.assertEqual([body["model"] for body in bodies], [interview.settings.GROQ_PRIMARY_MODEL, interview.settings.GROQ_FALLBACK_MODEL])
                self.assertEqual(result["generated_by_model"], interview.settings.GROQ_FALLBACK_MODEL)
                self.assertTrue(all(body["response_format"] == {"type": "json_object"} for body in bodies))

    async def test_invalid_grades_fall_back_without_fabricating(self):
        malformed = [
            {**GRADE, "rubric_scores": {"correctness": value, "reasoning": 4, "edge_cases": 2, "clarity": 8}}
            for value in [11, -1, "6", True, float("inf")]
        ] + [
            {**GRADE, "strengths": "Not an array"}, {**GRADE, "assessment": "ambiguous", "clarification_question": ""},
            {**GRADE, "model_answer_hint": " "}, {**GRADE, "rubric_scores": {"correctness": 5}}, {**GRADE, "score": 10},
        ]
        for invalid in malformed:
            with self.subTest(response=invalid):
                self.seed(total=1)
                bodies = self.transport([json.dumps(invalid), json.dumps(GRADE)])
                result = await interview.submit_mock_interview_answer(self.request(), USER)
                self.assertTrue(result["done"])
                self.assertEqual(result["feedback"]["score"], 5.1)
                self.assertEqual(result["feedback"]["graded_by_model"], interview.settings.GROQ_FALLBACK_MODEL)
                self.assertEqual(len(bodies), 2)
                self.assertEqual(len(self.sessions.documents["session-one"]["results"]), 1)

    async def test_exhausted_fallback_does_not_grade_or_advance(self):
        original = self.seed()
        self.transport(["bad", "also bad"])
        with self.assertRaises(AIProviderError) as caught:
            await interview.submit_mock_interview_answer(self.request(), USER)
        self.assertEqual(caught.exception.kind, "invalid_response")
        self.assertEqual(self.sessions.documents["session-one"], original)
        self.assertFalse(self.sessions.updates)

    async def test_next_question_failure_is_atomic_and_retry_saves_one_grade(self):
        original = self.seed()
        generate = AsyncMock(side_effect=AIProviderError("invalid_response", "Next question unavailable", True))
        self.replace(interview, "_get_next_question", generate)
        with self.assertRaises(AIProviderError):
            await interview.submit_mock_interview_answer(self.request(), USER)
        self.assertEqual(self.sessions.documents["session-one"], original)
        self.assertFalse(self.sessions.updates)
        generate.side_effect = None
        generate.return_value = {"question": "Explain complexity", "category": "coding", "difficulty": "intermediate"}
        result = await interview.submit_mock_interview_answer(self.request(), USER)
        stored = self.sessions.documents["session-one"]
        self.assertEqual(result["question_number"], 2)
        self.assertEqual((len(stored["results"]), stored["index"], stored["version"]), (1, 1, 1))
        self.assertEqual(len(stored["questions_asked"]), 2)
        query = self.sessions.updates[-1][0]
        self.assertEqual(query, {"_id": "session-one", "user_id": USER["id"], "version": 0, "status": "active"})

    async def test_concurrent_submissions_only_commit_once(self):
        self.seed(total=1)
        both_ready = asyncio.Event()
        calls = 0

        async def grade(messages, schema, model=None):
            nonlocal calls
            calls += 1
            if calls == 2:
                both_ready.set()
            await both_ready.wait()
            return schema.model_validate(GRADE), "actual-model"

        self.ai.structured.side_effect = grade
        results = await asyncio.gather(
            interview.submit_mock_interview_answer(self.request(), USER),
            interview.submit_mock_interview_answer(self.request(), USER), return_exceptions=True,
        )
        self.assertEqual(len([result for result in results if isinstance(result, dict)]), 1)
        failures = [result for result in results if isinstance(result, HTTPException)]
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].status_code, 409)
        self.assertEqual(len(self.sessions.documents["session-one"]["results"]), 1)

    async def test_malformed_next_question_rolls_back_grade_and_retry_commits_once(self):
        original = self.seed()
        next_question = {**QUESTION, "question": "Explain hashing complexity", "difficulty": "intermediate"}
        bodies = self.transport([
            json.dumps(GRADE), "malformed question", json.dumps({**next_question, "category": "hr"}),
            json.dumps(GRADE), json.dumps(next_question),
        ])
        with self.assertRaises(AIProviderError):
            await interview.submit_mock_interview_answer(self.request(), USER)
        self.assertEqual(self.sessions.documents["session-one"], original)
        self.assertFalse(self.sessions.updates)
        result = await interview.submit_mock_interview_answer(self.request(), USER)
        self.assertEqual(result["question"], next_question["question"])
        self.assertEqual(len(self.sessions.documents["session-one"]["results"]), 1)
        self.assertEqual(len(bodies), 5)

    async def test_end_during_grading_prevents_late_commit(self):
        self.seed(total=1)
        ready, release = asyncio.Event(), asyncio.Event()

        async def grade(messages, schema, model=None):
            ready.set()
            await release.wait()
            return schema.model_validate(GRADE), "actual-model"

        self.ai.structured.side_effect = grade
        task = asyncio.create_task(interview.submit_mock_interview_answer(self.request(), USER))
        await ready.wait()
        await interview.end_mock_interview(interview.EndInterviewRequest(session_id="session-one"), USER)
        release.set()
        with self.assertRaises(HTTPException) as caught:
            await task
        self.assertEqual(caught.exception.status_code, 409)
        stored = self.sessions.documents["session-one"]
        self.assertEqual(stored["status"], "ended")
        self.assertEqual(stored["results"], [])

    async def test_ended_sessions_reject_answers_and_end_is_idempotent(self):
        for session_status in ["ended", "completed"]:
            with self.subTest(status=session_status):
                self.seed()
                self.sessions.documents["session-one"]["status"] = session_status
                with self.assertRaises(HTTPException) as caught:
                    await interview.submit_mock_interview_answer(self.request(), USER)
                self.assertEqual(caught.exception.status_code, 409)
                response = await interview.end_mock_interview(interview.EndInterviewRequest(session_id="session-one"), USER)
                self.assertEqual(response["summary"]["questions_answered"], 0)
                self.assertIsNone(response["summary"]["average_score"])
        self.assertFalse(self.sessions.updates)
        self.ai.structured.assert_not_awaited()

    async def test_stale_question_number_is_rejected_before_grading(self):
        self.seed()
        self.sessions.documents["session-one"]["index"] = 1
        with self.assertRaises(HTTPException) as caught:
            await interview.submit_mock_interview_answer(self.request(), USER)
        self.assertEqual(caught.exception.status_code, 409)
        self.ai.structured.assert_not_awaited()

    async def test_model_selection_does_not_depend_on_answer_length(self):
        for answer in ["Correct short answer", "reasoning " * 300]:
            with self.subTest(answer_length=len(answer)):
                self.seed(total=1, mode="technical", category="conceptual")
                await interview.submit_mock_interview_answer(self.request(answer), USER)
                self.assertIsNone(self.ai.structured.await_args.kwargs.get("model"))

    async def test_mixed_hr_question_uses_behavioral_rubric(self):
        self.seed(total=1, mode="mixed", category="hr")
        case = next(case for case in BENCHMARK["cases"] if case["id"] == "hr-strong")
        self.ai.structured.side_effect = None
        self.ai.structured.return_value = interview.BehavioralGrade.model_validate(case["expected"]["grade"]), "actual-hr-model"
        result = await interview.submit_mock_interview_answer(self.request(), USER)
        self.assertIs(self.ai.structured.await_args.args[1], interview.BehavioralGrade)
        self.assertEqual(result["feedback"]["rubric_weights"], interview.RUBRIC_WEIGHTS["hr"])
        self.assertEqual(result["feedback"]["graded_by_model"], "actual-hr-model")
        self.assertIn("Do not require technical code", self.ai.structured.await_args.args[0][0]["content"])

    async def test_curated_pool_is_validated_deduplicated_and_persisted(self):
        self.collections["domain_details"].documents["domain"]["interview_prep"] = {
            "hr_questions": ["Describe a disagreement", "describe a disagreement", " ", {"bad": "shape"}],
        }
        response = await interview.start_mock_interview(interview.MockInterviewStartRequest(domain_slug="python", mode="hr"), USER)
        stored = self.sessions.documents[response["session_id"]]
        self.assertEqual(len(stored["_pool"]), 1)
        self.assertEqual(response["category"], "hr")
        self.assertIsNone(response["generated_by_model"])
        self.ai.structured.assert_not_awaited()

    async def test_duplicate_generated_question_falls_back(self):
        alternative = {**QUESTION, "question": "What is a hash collision?", "difficulty": "intermediate"}
        bodies = self.transport([json.dumps({**QUESTION, "difficulty": "intermediate"}), json.dumps(alternative)])
        result = await interview._get_next_question("coding", {"domain_slug": "python"}, {"questions_asked": [QUESTION], "index": 0})
        self.assertEqual(result["question"], alternative["question"])
        self.assertEqual(len(bodies), 2)

    async def test_maximum_session_completes_at_fifteen_questions(self):
        self.seed(total=15)

        async def next_question(mode, domain, session):
            return {**QUESTION, "question": "Question " + str(session["index"] + 1)}

        self.replace(interview, "_get_next_question", next_question)
        for number in range(1, 16):
            response = await interview.submit_mock_interview_answer(self.request(question_number=number), USER)
            self.assertEqual(response["done"], number == 15)
        stored = self.sessions.documents["session-one"]
        self.assertEqual((len(stored["questions_asked"]), len(stored["results"])), (15, 15))
        self.assertEqual(stored["status"], "completed")
        self.assertEqual(response["summary"]["questions_answered"], 15)

    async def test_structured_teaching_reports_actual_model_and_legacy_explanation(self):
        self.seed(total=1)
        await interview.submit_mock_interview_answer(self.request(), USER)
        result = await interview.explain_more(interview.ExplainMoreRequest(session_id="session-one"), USER)
        self.assertEqual(result["teaching"], TEACHING)
        self.assertEqual(result["model_used"], "actual-model")
        self.assertIn(TEACHING["worked_example"], result["explanation"])
        self.assertEqual(self.ai.structured.await_args.kwargs["model"], interview.settings.GROQ_FALLBACK_MODEL)

    async def test_teaching_requires_a_grade(self):
        self.seed()
        with self.assertRaises(HTTPException) as caught:
            await interview.explain_more(interview.ExplainMoreRequest(session_id="session-one"), USER)
        self.assertEqual(caught.exception.status_code, 400)
        self.ai.structured.assert_not_awaited()

    async def test_invalid_teaching_falls_back_without_mutating_session(self):
        self.seed(total=1)
        await interview.submit_mock_interview_answer(self.request(), USER)
        original = copy.deepcopy(self.sessions.documents["session-one"])
        self.transport([json.dumps({**TEACHING, "reasoning": []}), json.dumps(TEACHING)])
        response = await interview.explain_more(interview.ExplainMoreRequest(session_id="session-one"), USER)
        self.assertEqual(response["teaching"], TEACHING)
        self.assertEqual(response["model_used"], interview.settings.GROQ_PRIMARY_MODEL)
        self.assertEqual(self.sessions.documents["session-one"], original)

    async def test_curated_benchmark_schema_weighted_grading_and_mocked_repeatability(self):
        for case in BENCHMARK["cases"]:
            with self.subTest(case=case["id"]):
                key = interview._rubric_key(case["category"])
                schema = interview.BehavioralGrade if key == "hr" else interview.TechnicalGrade
                expected = schema.model_validate(case["expected"]["grade"])
                self.ai.structured.side_effect = None
                self.ai.structured.return_value = expected, "offline-anchor"
                question = {**QUESTION, "question": case["question"], "category": case["category"]}
                first = await interview._grade_answer(question, case["answer"])
                second = await interview._grade_answer(question, case["answer"])
                self.assertEqual(first, second)
                low, high = case["expected"]["score_range"]
                self.assertLessEqual(low, first["score"])
                self.assertLessEqual(first["score"], high)
                self.assertEqual(first["provisional"], expected.assessment == "ambiguous")
                self.assertEqual(first["rubric_weights"], BENCHMARK["rubric_weights"][key])
                self.assertAlmostEqual(sum(first["rubric_weights"].values()), 1)

    def test_benchmark_covers_each_assessment_for_each_rubric(self):
        self.assertEqual(len({case["id"] for case in BENCHMARK["cases"]}), len(BENCHMARK["cases"]))
        for key in interview.RUBRIC_WEIGHTS:
            cases = [case for case in BENCHMARK["cases"] if interview._rubric_key(case["category"]) == key]
            self.assertEqual({case["expected"]["grade"]["assessment"] for case in cases}, {"strong", "partial", "incorrect", "ambiguous"})

    def test_request_bounds_reject_invalid_input_before_ai(self):
        starts = [
            {"domain_slug": "python", "num_questions": 16}, {"domain_slug": "python", "num_questions": 0},
            {"domain_slug": "python", "num_questions": True}, {"domain_slug": "python", "mode": "invalid"},
            {"domain_slug": {"$ne": None}}, {"domain_slug": " "},
        ]
        answers = [
            {"session_id": "session-one", "answer": " "}, {"session_id": "session-one", "answer": "x" * 20001},
            {"session_id": {"$ne": None}, "answer": "Use a set"},
            {"session_id": "session-one", "answer": "Use a set", "question_number": 16},
        ]
        with self.client() as client:
            for endpoint, payloads in [("start", starts), ("answer", answers)]:
                for payload in payloads:
                    with self.subTest(endpoint=endpoint, payload=payload):
                        self.assertEqual(client.post("/mock-interview/" + endpoint, json=payload).status_code, 422)
        self.ai.structured.assert_not_awaited()

    def test_grade_rejects_nonfinite_scores(self):
        for value in [float("nan"), float("inf"), -float("inf")]:
            with self.subTest(score=value), self.assertRaises(ValidationError):
                interview.TechnicalGrade.model_validate({**GRADE, "rubric_scores": {**GRADE["rubric_scores"], "correctness": value}})


if __name__ == "__main__":
    unittest.main()
