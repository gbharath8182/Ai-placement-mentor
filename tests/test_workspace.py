from copy import deepcopy
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
from bson import ObjectId
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

from backend.mastery import topic_checks
from backend.middleware import SafetyMiddleware
from backend.routes import workspace


OWNER = ObjectId("000000000000000000000001")
OTHER = ObjectId("000000000000000000000002")


class Cursor:
    def __init__(self, documents):
        self.documents = list(documents)

    def sort(self, key, direction):
        self.documents.sort(key=lambda document: document.get(key, ""), reverse=direction < 0)
        return self

    def limit(self, count):
        self.documents = self.documents[:count]
        return self

    def max_time_ms(self, duration):
        assert 0 < duration <= 3000
        return self

    def __aiter__(self):
        async def iterate():
            for document in self.documents:
                yield deepcopy(document)
        return iterate()


class Collection:
    def __init__(self, documents=()):
        self.documents = list(documents)
        self.queries = []

    def find(self, query, projection):
        self.queries.append((query, projection))
        documents = self.documents
        if "user_id" in query:
            documents = [document for document in documents if document.get("user_id") == query["user_id"]]
        if "slug" in query:
            documents = [document for document in documents if document["slug"] in query["slug"]["$in"]]
        return Cursor(documents)


@pytest.fixture
def setup(monkeypatch):
    collections = {name: Collection() for name in ("user_progress", "user_mastery", "topics")}
    monkeypatch.setattr(workspace, "get_collection", collections.__getitem__)
    app = FastAPI()
    app.include_router(workspace.router)
    app.add_middleware(SafetyMiddleware)
    app.dependency_overrides[workspace.get_current_user] = lambda: {"id": str(OWNER)}

    @app.exception_handler(PyMongoError)
    async def database_error(request, error):
        return JSONResponse({"detail": "Database unavailable"}, status_code=503)

    with TestClient(app) as client:
        yield client, collections, app


def progress(slug, status="in_progress", owner=OWNER):
    return {"user_id": owner, "topic_slug": slug, "status": status, "updated_at": datetime.now(timezone.utc), "ai_notes": "private notes"}


def evidence(topic, score=20, age=0):
    check = topic_checks(topic)[0]
    return {"user_id": OWNER, "topic_slug": topic["slug"], "updated_at": datetime.now(timezone.utc), "evidence": [{
        "kind": "quiz", "source_id": check["block_id"], "concept_id": check["concept_id"],
        "score": score, "recorded_at": datetime.now(timezone.utc) - timedelta(days=age),
    }]}


def test_new_user_has_honest_empty_queue_and_real_starting_point(setup):
    client, collections, app = setup
    response = client.get("/workspace/overview")
    data = response.json()
    assert response.status_code == 200
    assert data["counts"] == {"in_progress": 0, "review": 0, "mastered": 0}
    assert data["continue"] == data["reviews"] == []
    assert data["suggested"]["slug"] == workspace.builtin_curriculum()["topics"][0]["slug"]
    assert response.headers["cache-control"] == "no-store"
    assert len(response.headers["x-request-id"]) == 32


def test_overview_requires_authentication(setup):
    client, collections, app = setup
    app.dependency_overrides.clear()
    assert client.get("/workspace/overview").status_code == 401


def test_invalid_user_id_fails_closed(setup):
    client, collections, app = setup
    app.dependency_overrides[workspace.get_current_user] = lambda: {"id": "invalid"}
    assert client.get("/workspace/overview").status_code == 401


def test_progress_is_owner_scoped_and_private_fields_never_returned(setup):
    client, collections, app = setup
    first, second = workspace.builtin_curriculum()["topics"][:2]
    collections["user_progress"].documents = [progress(first["slug"]), progress(second["slug"], owner=OTHER)]
    response = client.get("/workspace/overview")
    assert [item["slug"] for item in response.json()["continue"]] == [first["slug"]]
    assert "private notes" not in response.text and "user_id" not in response.text
    assert collections["user_progress"].queries[0][0] == {"user_id": OWNER}
    assert collections["user_mastery"].queries[0][0] == {"user_id": OWNER}


@pytest.mark.parametrize("age,score", [(0, 20), (20, 100)])
def test_weak_and_stale_evidence_become_reviews_not_mastery(setup, age, score):
    client, collections, app = setup
    topic = workspace.builtin_curriculum()["topics"][0]
    collections["user_mastery"].documents = [evidence(topic, score, age)]
    collections["user_progress"].documents = [progress(topic["slug"])]
    data = client.get("/workspace/overview").json()
    assert data["counts"] == {"in_progress": 0, "review": 1, "mastered": 0}
    assert data["reviews"][0]["slug"] == topic["slug"]
    assert data["reviews"][0]["kind"] == "quiz"
    assert "evidence" not in data["reviews"][0]


def test_reading_without_assessment_does_not_create_review_or_mastery(setup):
    client, collections, app = setup
    topic = workspace.builtin_curriculum()["topics"][0]
    collections["user_progress"].documents = [progress(topic["slug"])]
    collections["user_mastery"].documents = [{"user_id": OWNER, "topic_slug": topic["slug"], "evidence": []}]
    data = client.get("/workspace/overview").json()
    assert data["counts"] == {"in_progress": 1, "review": 0, "mastered": 0}


def test_database_topic_wins_over_builtin_without_answer_leak(setup):
    client, collections, app = setup
    topic = deepcopy(workspace.builtin_curriculum()["topics"][0])
    topic["title"] = "Database title"
    collections["topics"].documents = [topic]
    collections["user_progress"].documents = [progress(topic["slug"])]
    response = client.get("/workspace/overview")
    assert response.json()["continue"][0]["title"] == "Database title"
    assert "correct_index" not in response.text and "content_blocks" not in response.text


def test_deleted_lessons_are_not_dead_links(setup):
    client, collections, app = setup
    collections["user_progress"].documents = [progress("removed-topic")]
    data = client.get("/workspace/overview").json()
    assert data["continue"] == [] and data["unavailable_lessons"] == 1


def test_completed_lesson_not_recommended_as_first_step(setup):
    client, collections, app = setup
    first, second = workspace.builtin_curriculum()["topics"][:2]
    collections["user_progress"].documents = [progress(first["slug"], "completed")]
    data = client.get("/workspace/overview").json()
    assert data["suggested"]["slug"] == second["slug"]
    assert data["counts"]["mastered"] == 0
    assert data["has_history"] is True


def test_fresh_mastery_is_not_recommended_as_unfinished_work(setup):
    client, collections, app = setup
    topic = workspace.builtin_curriculum()["topics"][0]
    document = evidence(topic, 100)
    document["evidence"] = [{"kind": "quiz", "source_id": check["block_id"], "concept_id": check["concept_id"], "score": 100, "recorded_at": datetime.now(timezone.utc)} for check in topic_checks(topic)]
    document["evidence"].append({"kind": "coding", "source_id": "fixture-task", "score": 100, "recorded_at": datetime.now(timezone.utc)})
    collections["user_mastery"].documents = [document]
    collections["user_progress"].documents = [progress(topic["slug"])]
    data = client.get("/workspace/overview").json()
    assert data["counts"]["mastered"] == 1
    assert data["continue"] == data["reviews"] == []
    assert data["suggested"]["slug"] != topic["slug"]


def test_recent_window_is_bounded_and_disclosed(setup):
    client, collections, app = setup
    collections["user_progress"].documents = [progress(f"topic-{index}") for index in range(105)]
    data = client.get("/workspace/overview").json()
    assert data["limited"] is True and data["window"] == 100
    assert len(collections["topics"].queries[0][0]["slug"]["$in"]) <= 100


def test_private_database_failure_is_not_fake_empty_success(setup, monkeypatch):
    client, collections, app = setup
    monkeypatch.setattr(collections["user_progress"], "find", Mock(side_effect=ServerSelectionTimeoutError("secret-host")))
    response = client.get("/workspace/overview")
    assert response.status_code == 503 and "secret-host" not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_search_never_returns_assessment_answers(setup):
    client, collections, app = setup
    topic = deepcopy(workspace.builtin_curriculum()["topics"][0])
    topic["title"] = "Database values title"
    collections["topics"].documents = [topic]
    response = client.get("/catalog/search", params={"q": "values"})
    assert any(item["title"] == "Database values title" for item in response.json()["results"])
    assert "content_blocks" not in response.text and "correct_index" not in response.text
    assert "evidence" not in response.text


def test_search_escapes_regex_and_bounds_query(setup):
    client, collections, app = setup
    assert client.get("/catalog/search", params={"q": ".*"}).status_code == 200
    condition = collections["topics"].queries[-1][0]["$and"][0]["$or"][0]
    assert condition["title"]["$regex"] == r"\.\*"
    assert client.get("/catalog/search", params={"q": "a" * 81}).status_code == 422


def test_short_search_does_not_query_database(setup):
    client, collections, app = setup
    assert client.get("/catalog/search", params={"q": "a"}).json() == {"results": [], "degraded": False}
    assert collections["topics"].queries == []


def test_public_search_has_explicit_builtin_fallback(setup, monkeypatch):
    client, collections, app = setup
    monkeypatch.setattr(collections["topics"], "find", Mock(side_effect=ServerSelectionTimeoutError("secret-host")))
    response = client.get("/catalog/search", params={"q": "values"})
    assert response.status_code == 200 and response.json()["degraded"] is True
    assert response.json()["results"] and "secret-host" not in response.text


@pytest.mark.parametrize("slug", ["javascript:alert(1)", "../login", "unsafe/slug", "x" * 129])
def test_unsafe_catalog_slugs_are_not_linked(setup, slug):
    client, collections, app = setup
    collections["topics"].documents = [{"slug": slug, "title": "Sample"}]
    assert client.get("/catalog/search", params={"q": "sample"}).json()["results"] == []
