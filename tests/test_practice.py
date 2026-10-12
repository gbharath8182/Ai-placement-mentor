import asyncio
import sys
from types import SimpleNamespace, ModuleType
from unittest.mock import AsyncMock

import httpx
import pytest
from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routes import practice

RealAsyncClient = httpx.AsyncClient


class Cursor:
    def __init__(self, documents):
        self.documents = documents
        self.offset = 0
        self.count = len(documents)
        self.timeout = None

    def skip(self, offset):
        self.offset = offset
        return self

    def limit(self, count):
        self.count = count
        return self

    def max_time_ms(self, timeout):
        self.timeout = timeout
        return self

    def __aiter__(self):
        async def iterate():
            for document in self.documents[self.offset:self.offset + self.count]:
                yield document
        return iterate()


@pytest.fixture
def practice_client(monkeypatch):
    document = {
        "_id": ObjectId(), "topic_slug": "python", "title": "Echo",
        "difficulty": "easy", "description": "Echo stdin", "starter_code": "",
        "test_cases": [{"input": "hello", "expected_output": "hello"}],
    }
    cursor = Cursor([document])
    problems = SimpleNamespace(find=lambda query: cursor, find_one=AsyncMock(return_value=document))
    progress = SimpleNamespace(update_one=AsyncMock())
    mastery = ModuleType("backend.mastery")
    mastery.record_evidence = AsyncMock()
    progress.record_evidence = mastery.record_evidence
    monkeypatch.setitem(sys.modules, "backend.mastery", mastery)
    monkeypatch.setattr(practice, "get_collection", lambda name: problems if name == "practice_problems" else progress)
    monkeypatch.setattr(practice, "builtin_problems", lambda: [])
    monkeypatch.delenv("PISTON_EXECUTE_URL", raising=False)
    monkeypatch.setattr(practice.settings, "PISTON_EXECUTE_URL", "", raising=False)
    monkeypatch.setattr(practice.settings, "PISTON_API_KEY", "", raising=False)
    app = FastAPI()
    app.include_router(practice.router)
    user_id = str(ObjectId())
    progress.user_id = user_id
    app.dependency_overrides[practice.get_current_user] = lambda: {"id": user_id}
    with TestClient(app) as client:
        yield client, document, problems, progress, cursor


def install_sandbox(monkeypatch, handler):
    created = []
    monkeypatch.setenv("PISTON_EXECUTE_URL", "https://sandbox.example.test/api/v2/execute")
    monkeypatch.setattr(practice.settings, "PISTON_EXECUTE_URL", "https://sandbox.example.test/api/v2/execute", raising=False)

    def factory(**options):
        created.append(options)
        return RealAsyncClient(transport=httpx.MockTransport(handler), **options)

    monkeypatch.setattr(practice.httpx, "AsyncClient", factory)
    return created


def submit(client, document, **overrides):
    return client.post(f"/practice/{document['_id']}/submit", json={"language": "python", "code": "print(input())", **overrides})


def test_listing_is_bounded_and_nonmutating(practice_client):
    client, document, _, _, cursor = practice_client
    response = client.get("/practice/python?limit=1&offset=0")
    assert response.status_code == 200 and len(response.json()) == 1
    assert response.json()[0]["id"] == str(document["_id"])
    assert "_id" in document and "id" not in document
    assert cursor.count == 1 and cursor.timeout == 5000
    assert client.get("/practice/python?offset=1").json() == []
    assert client.get("/practice/python?limit=101").status_code == 422
    assert client.get("/practice/python?offset=-1").status_code == 422
    assert client.get("/practice/" + "x" * 129).status_code == 422


def test_invalid_id_rejected_before_database(practice_client):
    client, document, problems, progress, _ = practice_client
    assert client.post("/practice/not-an-id/submit", json={"language": "python", "code": "pass"}).status_code == 400
    problems.find_one.assert_not_awaited()
    problems.find_one.return_value = None
    progress.update_one.assert_not_awaited()


def test_database_error_is_not_misreported_as_invalid_id(practice_client, monkeypatch):
    client, document, problems, _, _ = practice_client
    install_sandbox(monkeypatch, lambda request: httpx.Response(200, json={}))
    problems.find_one.side_effect = RuntimeError("database unavailable")
    with pytest.raises(RuntimeError, match="database unavailable"):
        submit(client, document)


def test_self_reported_completion_is_rejected_without_writes(practice_client):
    client, document, problems, progress, _ = practice_client
    response = client.post(f"/practice/{document['_id']}/completed")
    assert response.status_code == 409 and "/submit" in response.json()["detail"]
    problems.find_one.assert_not_awaited()
    progress.update_one.assert_not_awaited()
    progress.record_evidence.assert_not_awaited()


def test_remote_execution_is_disabled_by_default(practice_client):
    client, document, problems, progress, _ = practice_client
    assert submit(client, document).status_code == 503
    problems.find_one.assert_not_awaited()
    progress.update_one.assert_not_awaited()
    progress.record_evidence.assert_not_awaited()


@pytest.mark.parametrize("endpoint", [
    "http://localhost:2000/execute", "file:///tmp/execute", "https://user:pass@sandbox.test/execute",
    "https://sandbox.test/execute?url=http://attacker.test", "https://sandbox.test/#fragment", "https://[bad",
])
def test_untrusted_sandbox_configuration_rejected(practice_client, monkeypatch, endpoint):
    client, document, problems, _, _ = practice_client
    monkeypatch.setenv("PISTON_EXECUTE_URL", endpoint)
    monkeypatch.setattr(practice.settings, "PISTON_EXECUTE_URL", endpoint, raising=False)
    assert submit(client, document).status_code == 503
    problems.find_one.assert_not_awaited()


def test_execution_boundary_budgets_and_results(practice_client, monkeypatch):
    import json

    client, document, _, progress, _ = practice_client
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"run": {"stdout": "hello\r\n", "stderr": "", "code": 0, "signal": None}})

    created = install_sandbox(monkeypatch, handler)
    response = submit(client, document, endpoint="https://attacker.test", run_timeout=999999)
    assert response.status_code == 200 and response.json()["overall_passed"] is True
    assert response.json()["results"][0]["test_case_index"] == 0
    assert len(requests) == 1
    assert str(requests[0].url) == "https://sandbox.example.test/api/v2/execute"
    payload = json.loads(requests[0].content)
    assert payload["files"] == [{"name": "main.py", "content": "print(input())"}]
    assert payload["stdin"] == "hello" and payload["args"] == []
    assert payload["run_timeout"] == 3000 and payload["compile_timeout"] == 10000
    assert payload["run_memory_limit"] == 128 * 1024 * 1024
    assert payload["compile_memory_limit"] == 256 * 1024 * 1024
    assert payload["run_cpu_time"] == 3000
    assert created[0]["follow_redirects"] is False and created[0]["trust_env"] is False
    assert created[0]["timeout"].connect == 3 and created[0]["timeout"].read == 15
    progress.update_one.assert_awaited_once()
    query, update = progress.update_one.call_args.args
    assert query == {"user_id": ObjectId(progress.user_id), "topic_slug": "python"}
    assert update["$set"]["status"] == "completed"
    assert update["$set"]["updated_at"].tzinfo is not None
    progress.record_evidence.assert_awaited_once_with(progress.user_id, "python", "coding", 100.0, source_id=str(document["_id"]))


@pytest.mark.parametrize("result", [
    {"run": {"stdout": "wrong", "stderr": "", "code": 0}},
    {"run": {"stdout": "hello", "stderr": "error", "code": 0}},
    {"run": {"stdout": "hello", "stderr": "", "code": 1}},
    {"run": {"stdout": "hello", "stderr": "", "code": None, "signal": "SIGKILL"}},
    {"compile": {"stdout": "", "stderr": "compile error", "code": 1}},
])
def test_failed_or_signalled_execution_does_not_pass(practice_client, monkeypatch, result):
    client, document, _, progress, _ = practice_client
    install_sandbox(monkeypatch, lambda request: httpx.Response(200, json=result))
    response = submit(client, document)
    assert response.status_code == 200 and response.json()["overall_passed"] is False
    progress.update_one.assert_not_awaited()
    progress.record_evidence.assert_awaited_once_with(progress.user_id, "python", "coding", 0.0, source_id=str(document["_id"]))


@pytest.mark.parametrize("content", [
    b"not-json", b"[]", b"{}", b'{"run":{"stdout":[]}}', b'{"compile":[],"run":{}}',
    b'{"run":{"stdout":"hello","stderr":""}}', b'{"run":{"stdout":"hello","stderr":"","code":null}}',
])
def test_malformed_sandbox_responses(practice_client, monkeypatch, content):
    client, document, _, progress, _ = practice_client
    install_sandbox(monkeypatch, lambda request: httpx.Response(200, content=content))
    assert submit(client, document).status_code == 502
    progress.update_one.assert_not_awaited()
    progress.record_evidence.assert_not_awaited()


def test_response_size_bound(practice_client, monkeypatch):
    client, document, _, _, _ = practice_client
    install_sandbox(monkeypatch, lambda request: httpx.Response(200, content=b"x" * 65537))
    assert submit(client, document).status_code == 502


@pytest.mark.parametrize("status", [301, 400, 429, 500])
def test_upstream_status_redacted_and_redirect_not_followed(practice_client, monkeypatch, status):
    client, document, _, _, _ = practice_client
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(status, headers={"Location": "https://attacker.test"}, text="sensitive upstream diagnostics")

    install_sandbox(monkeypatch, handler)
    response = submit(client, document)
    assert response.status_code == 502
    assert len(requests) == 1 and "sensitive" not in response.text


@pytest.mark.parametrize("exception,status", [(httpx.ReadTimeout, 504), (httpx.ConnectError, 502)])
def test_transport_failures_redacted(practice_client, monkeypatch, exception, status):
    client, document, _, _, _ = practice_client

    def handler(request):
        raise exception("sensitive upstream address", request=request)

    install_sandbox(monkeypatch, handler)
    response = submit(client, document)
    assert response.status_code == status and "sensitive" not in response.text


def test_whole_submission_deadline(practice_client, monkeypatch):
    client, document, _, progress, _ = practice_client

    async def handler(request):
        await asyncio.sleep(1)
        return httpx.Response(200, json={})

    install_sandbox(monkeypatch, handler)
    monkeypatch.setattr(practice, "SUBMISSION_TIMEOUT_SECONDS", 0.01)
    assert submit(client, document).status_code == 504
    progress.update_one.assert_not_awaited()
    progress.record_evidence.assert_not_awaited()


@pytest.mark.parametrize("test_cases", [[], [{}], [None], [{"input": "x" * 16385, "expected_output": ""}], [{"input": "", "expected_output": ""}] * 21])
def test_problem_test_case_bounds(practice_client, monkeypatch, test_cases):
    client, document, _, progress, _ = practice_client
    document["test_cases"] = test_cases
    calls = []
    install_sandbox(monkeypatch, lambda request: calls.append(request))
    assert submit(client, document).status_code == 422
    assert calls == []
    progress.update_one.assert_not_awaited()
    progress.record_evidence.assert_not_awaited()


def test_partial_results_record_fractional_score_without_completing(practice_client, monkeypatch):
    client, document, _, progress, _ = practice_client
    document["test_cases"] = [
        {"input": "hello", "expected_output": "hello"},
        {"input": "world", "expected_output": "world"},
    ]
    install_sandbox(monkeypatch, lambda request: httpx.Response(200, json={"run": {"stdout": "hello", "stderr": "", "code": 0}}))
    response = submit(client, document)
    assert response.status_code == 200 and response.json()["overall_passed"] is False
    progress.record_evidence.assert_awaited_once_with(progress.user_id, "python", "coding", 50.0, source_id=str(document["_id"]))
    progress.update_one.assert_not_awaited()


def test_missing_problem_cannot_record_evidence(practice_client, monkeypatch):
    client, document, problems, progress, _ = practice_client
    install_sandbox(monkeypatch, lambda request: httpx.Response(200, json={}))
    problems.find_one.return_value = None
    assert submit(client, document).status_code == 404
    progress.update_one.assert_not_awaited()
    progress.record_evidence.assert_not_awaited()


def test_missing_mastery_integration_fails_closed(practice_client, monkeypatch):
    client, document, problems, progress, _ = practice_client
    calls = []
    install_sandbox(monkeypatch, lambda request: calls.append(request))
    monkeypatch.setitem(sys.modules, "backend.mastery", None)
    assert submit(client, document).status_code == 503
    problems.find_one.assert_not_awaited()
    progress.update_one.assert_not_awaited()
    assert calls == []


def test_submission_bounds_before_execution(practice_client):
    client, document, problems, _, _ = practice_client
    for body in ({"language": "shell", "code": "echo hi"}, {"language": "python", "code": "x" * 65537}):
        assert client.post(f"/practice/{document['_id']}/submit", json=body).status_code == 422
    problems.find_one.assert_not_awaited()


def test_submit_requires_authentication(monkeypatch):
    app = FastAPI()
    app.include_router(practice.router)
    with TestClient(app) as client:
        assert client.post(f"/practice/{ObjectId()}/submit", json={"language": "python", "code": "pass"}).status_code == 401
        assert client.post("/practice/run", json={"language": "python", "code": "pass", "test_cases": [{"input": "", "expected_output": ""}]}).status_code == 401


def test_playground_javascript_shim_api_key_and_no_evidence(practice_client, monkeypatch):
    import json

    client, _, problems, progress, _ = practice_client
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"run": {"stdout": "hello", "stderr": "", "code": 0}})

    install_sandbox(monkeypatch, handler)
    monkeypatch.setattr(practice.settings, "PISTON_API_KEY", "test-only-sandbox-key", raising=False)
    monkeypatch.setitem(sys.modules, "backend.mastery", None)
    response = client.post("/practice/run", json={"language": "javascript", "code": "console.log(prompt());", "test_cases": [{"input": "hello", "expected_output": "hello"}]})
    assert response.status_code == 200 and response.json()["overall_passed"] is True
    code = json.loads(requests[0].content)["files"][0]["content"]
    assert 'readFileSync(0,"utf8").split(/\\r?\\n/)' in code
    assert 'const prompt=()=>inputLines[inputCursor++]||"";' in code
    assert code.endswith("console.log(prompt());")
    assert requests[0].headers["Authorization"] == "Bearer test-only-sandbox-key"
    assert "test-only-sandbox-key" not in response.text
    problems.find_one.assert_not_awaited()
    progress.update_one.assert_not_awaited()
    progress.record_evidence.assert_not_awaited()
    paths = [route.path for route in practice.router.routes]
    assert paths.index("/practice/run") < paths.index("/practice/{topic_slug}")


@pytest.mark.parametrize("test_cases", [
    [], [{}], [{"input": "", "expected_output": ""}] * 21,
    [{"input": "x" * 16385, "expected_output": ""}],
    [{"input": "", "expected_output": "é" * 8193}],
])
def test_playground_input_bounds(practice_client, test_cases):
    client, _, problems, progress, _ = practice_client
    response = client.post("/practice/run", json={"language": "python", "code": "pass", "test_cases": test_cases})
    assert response.status_code == 422
    problems.find_one.assert_not_awaited()
    progress.update_one.assert_not_awaited()


def test_playground_timeout_and_disabled_configuration(practice_client, monkeypatch):
    client, _, _, progress, _ = practice_client
    body = {"language": "python", "code": "pass", "test_cases": [{"input": "", "expected_output": ""}]}
    assert client.post("/practice/run", json=body).status_code == 503

    async def handler(request):
        await asyncio.sleep(1)
        return httpx.Response(200, json={})

    install_sandbox(monkeypatch, handler)
    monkeypatch.setattr(practice, "SUBMISSION_TIMEOUT_SECONDS", 0.01)
    assert client.post("/practice/run", json=body).status_code == 504
    progress.update_one.assert_not_awaited()
    progress.record_evidence.assert_not_awaited()


def test_sandbox_setting_takes_precedence_over_environment(practice_client, monkeypatch):
    monkeypatch.setattr(practice.settings, "PISTON_EXECUTE_URL", "https://configured.example.test/execute", raising=False)
    monkeypatch.setenv("PISTON_EXECUTE_URL", "https://environment.example.test/execute")
    assert practice.sandbox_url() == "https://configured.example.test/execute"


def test_listing_builtin_fallback_without_solutions(practice_client, monkeypatch):
    client, document, problems, _, cursor = practice_client
    builtin = {**document, "id": "a" * 24, "reference_solution": "test-only-reference-solution"}
    builtin.pop("_id")
    cursor.documents = []
    problems.find_one.return_value = None
    monkeypatch.setattr(practice, "builtin_problems", lambda: [builtin])
    response = client.get("/practice/python")
    assert response.status_code == 200 and response.json()[0]["id"] == "a" * 24
    assert "reference_solution" not in response.text
    assert "reference_solution" not in practice.serialize_problem(builtin)
    assert builtin["reference_solution"] == "test-only-reference-solution"
    assert client.get("/practice/python?offset=1").json() == []


def test_mongo_topic_overrides_builtin_even_at_empty_offset(practice_client, monkeypatch):
    client, document, _, _, _ = practice_client
    document["reference_solution"] = "test-only-reference-solution"

    def forbidden_builtin_read():
        raise AssertionError("Mongo topic must take precedence")

    monkeypatch.setattr(practice, "builtin_problems", forbidden_builtin_read)
    response = client.get("/practice/python")
    assert response.status_code == 200 and "reference_solution" not in response.text
    assert client.get("/practice/python?offset=1").json() == []


def test_submit_builtin_problem_uses_trusted_cases_and_stable_id(practice_client, monkeypatch):
    client, document, problems, progress, _ = practice_client
    builtin = {**document, "id": "a" * 24, "reference_solution": "test-only-reference-solution"}
    builtin.pop("_id")
    problems.find_one.return_value = None
    monkeypatch.setattr(practice, "builtin_problems", lambda: [builtin])
    install_sandbox(monkeypatch, lambda request: httpx.Response(200, json={"run": {"stdout": "hello", "stderr": "", "code": 0}}))
    response = client.post(f"/practice/{builtin['id']}/submit", json={"language": "python", "code": "print(input())", "test_cases": [{"input": "client-forged", "expected_output": "client-forged"}]})
    assert response.status_code == 200 and response.json()["overall_passed"] is True
    assert response.json()["results"][0]["input"] == "hello"
    assert "reference_solution" not in response.text
    progress.record_evidence.assert_awaited_once_with(progress.user_id, "python", "coding", 100.0, source_id="a" * 24)
    progress.update_one.assert_awaited_once()
    problems.find_one.assert_awaited_once_with({"_id": ObjectId("a" * 24)})


def test_problem_id_case_variants_share_one_evidence_identity(practice_client, monkeypatch):
    client, document, problems, progress, _ = practice_client
    canonical_id = "abcdef012345abcdef012345"
    document["_id"] = ObjectId(canonical_id)
    install_sandbox(monkeypatch, lambda request: httpx.Response(200, json={"run": {"stdout": "hello", "stderr": "", "code": 0}}))
    for identifier in (canonical_id, canonical_id.upper()):
        response = client.post(f"/practice/{identifier}/submit", json={"language": "python", "code": "print(input())"})
        assert response.status_code == 200 and response.json()["overall_passed"] is True
    assert progress.record_evidence.await_count == 2
    assert {call.kwargs["source_id"] for call in progress.record_evidence.await_args_list} == {canonical_id}
    assert all(call.args[0] == {"_id": ObjectId(canonical_id)} for call in problems.find_one.await_args_list)
