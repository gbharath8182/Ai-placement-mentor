import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymongo.errors import ServerSelectionTimeoutError

from backend.routes import content


class Cursor:
    def __init__(self, documents):
        self.documents = documents

    def limit(self, count):
        return self

    def max_time_ms(self, duration):
        return self

    def __aiter__(self):
        async def iterate():
            for document in self.documents:
                yield document
        return iterate()


class ContentTests(unittest.TestCase):
    def setUp(self):
        self.topic = {"slug": "sample", "title": "Authored topic", "domain_slug": "python-foundations", "difficulty": "beginner", "order": 1, "objectives": ["Learn names"], "prerequisites": [], "subtopics": [{"title": "Names", "content_blocks": [{"type": "knowledge_check", "question": "Which is correct?", "options": ["One", "Two"], "correct_index": 1, "explanation": "Private answer"}]}]}
        self.domain = {"slug": "python-foundations", "title": "Python Foundations", "description": "Original teaching", "topics": ["sample"]}
        self.collection = SimpleNamespace(find_one=AsyncMock(return_value=None), find=lambda *args: Cursor([]))
        self.patches = [patch.object(content, "builtin_curriculum", return_value={"domains": [self.domain], "topics": [self.topic]}), patch.object(content, "get_collection", return_value=self.collection)]
        for replacement in self.patches:
            replacement.start()
            self.addCleanup(replacement.stop)
        app = FastAPI()
        app.include_router(content.router)
        self.client = TestClient(app)

    def test_public_topic_hides_assessment_answers(self):
        response = self.client.get("/topics/sample")
        self.assertEqual(response.status_code, 200)
        block = response.json()["subtopics"][0]["content_blocks"][0]
        self.assertNotIn("correct_index", block)
        self.assertNotIn("explanation", block)
        self.assertEqual(self.topic["subtopics"][0]["content_blocks"][0]["correct_index"], 1)

    def test_existing_database_lesson_takes_priority(self):
        document = {**self.topic, "_id": ObjectId(), "title": "Existing valuable lesson"}
        self.collection.find_one.return_value = document
        response = self.client.get("/topics/sample")
        self.assertEqual(response.json()["title"], "Existing valuable lesson")
        self.assertIn("_id", document)

    def test_builtin_lesson_readable_during_database_failure(self):
        self.collection.find_one.side_effect = ServerSelectionTimeoutError("private database information")
        self.assertEqual(self.client.get("/topics/sample").status_code, 200)
        self.assertEqual(self.client.get("/domains/python-foundations/topics").status_code, 200)

    def test_domain_list_merges_without_overwriting_existing(self):
        database_domain = {**self.domain, "_id": ObjectId(), "title": "Existing curriculum"}
        self.collection.find = lambda *args: Cursor([database_domain])
        response = self.client.get("/domains")
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["title"], "Existing curriculum")

    def test_public_catalog_summary_keeps_answers_off_wire(self):
        response = self.client.get("/curriculum")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("content_blocks", response.text)
        self.assertNotIn("correct_index", response.text)
