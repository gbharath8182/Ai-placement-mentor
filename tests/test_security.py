import hashlib
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlsplit

import jwt
import pytest
from bson import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend import auth as tokens
from backend.models import (
    ActivityLogCreate, AIChatRequest, AIRecommendRequest, CodeSubmitRequest,
    ProgressUpdate, ResetPasswordRequest, TopicResponse, UserCreate, UserLogin,
)
from backend.routes import auth

send_reset_email = auth.send_reset_email


class Users:
    def __init__(self):
        self.user = {
            "_id": ObjectId(), "name": "Learner", "email": "learner@example.com",
            "password_hash": tokens.hash_password("old-password"),
            "profile": {"experience_level": "fresher", "interests": []},
            "created_at": datetime.now(timezone.utc),
        }
        self.updates = []

    async def find_one(self, query):
        if query.get("email") == self.user["email"]:
            return dict(self.user)
        return None

    async def update_one(self, query, changes):
        self.updates.append((query, changes))
        for key, value in query.items():
            actual = self.user.get(key)
            if isinstance(value, dict):
                if actual is None or actual <= value["$gt"]:
                    return SimpleNamespace(modified_count=0)
            elif actual != value:
                return SimpleNamespace(modified_count=0)
        self.user.update(changes.get("$set", {}))
        for key, value in changes.get("$inc", {}).items():
            self.user[key] = self.user.get(key, 0) + value
        for key in changes.get("$unset", {}):
            self.user.pop(key, None)
        return SimpleNamespace(modified_count=1)


@pytest.fixture
def security_client(monkeypatch):
    monkeypatch.setattr(tokens.settings, "JWT_SECRET", "test-only-signing-key-not-a-secret-123456")
    monkeypatch.setattr(auth.settings, "SMTP_HOST", "smtp.example.test")
    monkeypatch.setattr(auth.settings, "SMTP_FROM_EMAIL", "sender@example.com")
    monkeypatch.setattr(auth.settings, "SMTP_USERNAME", "")
    monkeypatch.setattr(auth.settings, "SMTP_PASSWORD", "")
    monkeypatch.setattr(auth.settings, "REFRESH_TOKEN_EXPIRE_DAYS", 2)
    monkeypatch.setattr(auth.settings, "EMAIL_PROVIDER", "smtp", raising=False)
    monkeypatch.setattr(auth.settings, "RESEND_API_KEY", "", raising=False)
    monkeypatch.setattr(auth.settings, "BREVO_API_KEY", "", raising=False)
    monkeypatch.setattr(auth.settings, "APP_ENV", "development", raising=False)
    monkeypatch.setattr(auth.settings, "APP_URL", "http://localhost:8000", raising=False)
    monkeypatch.setattr(auth.settings, "RESET_PASSWORD_BASE_URL", "", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("COOKIE_SECURE", raising=False)
    monkeypatch.setenv("RESET_PASSWORD_BASE_URL", "https://mentor.example.test")
    users = Users()
    delivered = []
    monkeypatch.setattr(tokens, "get_collection", lambda name: users)
    monkeypatch.setattr(auth, "get_collection", lambda name: users)
    monkeypatch.setattr(auth, "send_reset_email", lambda email, link: delivered.append((email, link)))
    app = FastAPI()
    app.include_router(auth.router)
    with TestClient(app) as client:
        yield client, users, delivered


def login(client):
    return client.post("/auth/login", json={"email": "learner@example.com", "password": "old-password"})


def request_reset(client, delivered):
    response = client.post("/auth/forgot-password", json={"email": "learner@example.com"})
    assert response.status_code == 200
    return parse_qs(urlsplit(delivered[-1][1]).query)["token"][0]


@pytest.mark.parametrize("environment,override,secure", [
    ("production", None, True), ("production", "false", True),
    ("staging", None, True), ("development", None, False),
    ("test", "true", True), ("local", "false", False),
])
def test_cookie_environment_and_lifetime(security_client, monkeypatch, environment, override, secure):
    client, _, _ = security_client
    monkeypatch.setenv("APP_ENV", environment)
    if override is not None:
        monkeypatch.setenv("COOKIE_SECURE", override)
    response = login(client)
    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert ("Secure" in cookie) is secure
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie and "Path=/" in cookie
    assert "Max-Age=172800" in cookie
    assert response.headers["cache-control"] == "no-store"
    assert "refresh_token" in response.json()
    response = client.post("/auth/refresh", json={"refresh_token": response.json()["refresh_token"]})
    assert response.status_code == 200
    assert ("Secure" in response.headers["set-cookie"]) is secure
    logout = client.post("/auth/logout")
    assert "Max-Age=0" in logout.headers["set-cookie"]
    assert ("Secure" in logout.headers["set-cookie"]) is secure


def test_cookie_defaults_secure_without_environment(security_client, monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.setattr(auth.settings, "APP_ENV", "production", raising=False)
    assert auth.cookie_secure() is True


@pytest.mark.parametrize("body", [[], "token", 12, None, {"refresh_token": {"$ne": None}}, {"refresh_token": ["token"]}])
def test_refresh_rejects_non_string_tokens(security_client, body):
    client, users, _ = security_client
    response = client.post("/auth/refresh", json=body)
    assert response.status_code == 401
    assert users.updates == []


def test_refresh_body_bound(security_client):
    client, _, _ = security_client
    assert client.post("/auth/refresh", content=b"x" * 16385).status_code == 413
    assert client.post("/auth/refresh", content=b"{").status_code == 401


@pytest.mark.parametrize("change", [
    {"exp": None}, {"sub": {"$ne": None}}, {"sub": ""}, {"type": "other"},
    {"uid": {}}, {"ver": True}, {"ver": -1}, {"exp": "tomorrow"}, {"exp": float("inf")}, {"exp": float("nan")},
])
def test_bad_claims_are_rejected(security_client, change):
    payload = {"sub": "learner@example.com", "type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    payload.update(change)
    token = jwt.encode(payload, tokens.settings.JWT_SECRET, algorithm="HS256")
    with pytest.raises(HTTPException) as error:
        tokens.decode_token(token)
    assert error.value.status_code == 401


@pytest.mark.parametrize("missing", ["exp", "sub", "type"])
def test_claims_are_required(security_client, missing):
    payload = {"sub": "learner@example.com", "type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    payload.pop(missing)
    with pytest.raises(HTTPException):
        tokens.decode_token(jwt.encode(payload, tokens.settings.JWT_SECRET, algorithm="HS256"))


def test_expired_tampered_oversized_tokens(security_client):
    expired = jwt.encode({"sub": "learner@example.com", "type": "access", "exp": 1}, tokens.settings.JWT_SECRET, algorithm="HS256")
    valid = tokens.create_access_token({"sub": "learner@example.com"})
    for token in (expired, valid + "invalid", "x" * 8193, None):
        with pytest.raises(HTTPException):
            tokens.decode_token(token)


def test_identity_and_token_type_enforcement(security_client):
    client, users, _ = security_client
    assert client.get("/auth/me").status_code == 401
    for token in (
        tokens.create_refresh_token({"sub": users.user["email"]}),
        tokens.create_access_token({"sub": users.user["email"], "uid": str(ObjectId())}),
        tokens.create_access_token({"sub": users.user["email"], "ver": 1}),
    ):
        assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    token = tokens.create_refresh_token({"sub": users.user["email"], "uid": str(ObjectId())})
    assert client.post("/auth/refresh", json={"refresh_token": token}).status_code == 401


def test_reset_is_single_use_and_revokes_sessions(security_client):
    client, users, delivered = security_client
    session = login(client).json()
    token = request_reset(client, delivered)
    assert users.user["password_reset_token_hash"] == hashlib.sha256(token.encode()).hexdigest()
    assert token not in repr(users.user)
    response = client.post("/auth/reset-password", json={"token": token, "password": "new-password"})
    assert response.status_code == 200
    assert users.user["auth_version"] == 1
    assert "password_reset_token_hash" not in users.user
    assert tokens.verify_password("new-password", users.user["password_hash"])
    assert client.post("/auth/reset-password", json={"token": token, "password": "new-password"}).status_code == 400
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {session['access_token']}"}).status_code == 401
    client.cookies.clear()
    assert client.post("/auth/refresh", json={"refresh_token": session["refresh_token"]}).status_code == 401


def test_new_reset_supersedes_previous_and_untracked_tokens_fail(security_client):
    client, _, delivered = security_client
    previous = request_reset(client, delivered)
    current = request_reset(client, delivered)
    assert previous != current
    untracked = tokens.create_reset_token("learner@example.com")
    for token in (previous, untracked):
        assert client.post("/auth/reset-password", json={"token": token, "password": "new-password"}).status_code == 400
    assert client.post("/auth/reset-password", json={"token": current, "password": "new-password"}).status_code == 200


def test_atomic_reset_condition_prevents_race(security_client, monkeypatch):
    client, users, delivered = security_client
    token = request_reset(client, delivered)
    original_update = users.update_one

    async def consume_before_update(query, changes):
        users.user.pop("password_reset_token_hash", None)
        return await original_update(query, changes)

    monkeypatch.setattr(users, "update_one", consume_before_update)
    response = client.post("/auth/reset-password", json={"token": token, "password": "new-password"})
    assert response.status_code == 400
    assert tokens.verify_password("old-password", users.user["password_hash"])


def test_reset_expiry_checked_in_database(security_client):
    client, users, delivered = security_client
    token = request_reset(client, delivered)
    users.user["password_reset_expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert client.post("/auth/reset-password", json={"token": token, "password": "new-password"}).status_code == 400


def test_forgot_password_never_discloses_link_or_host(security_client, caplog):
    client, _, delivered = security_client
    known = client.post("/auth/forgot-password", headers={"Host": "attacker.example"}, json={"email": "learner@example.com"})
    unknown = client.post("/auth/forgot-password", json={"email": "missing@example.com"})
    assert known.json() == unknown.json()
    assert set(known.json()) == {"message"}
    assert delivered[0][1].startswith("https://mentor.example.test/reset-password?token=")
    assert "learner@example.com" not in caplog.text
    assert "token=" not in caplog.text


def test_missing_smtp_does_not_issue_or_disclose_tokens(security_client, monkeypatch):
    client, users, delivered = security_client
    monkeypatch.setattr(auth.settings, "SMTP_HOST", "")
    response = client.post("/auth/forgot-password", json={"email": "learner@example.com"})
    assert response.status_code == 200 and set(response.json()) == {"message"}
    assert users.updates == [] and delivered == []


def test_production_reset_requires_trusted_https_base(security_client, monkeypatch):
    client, users, delivered = security_client
    monkeypatch.setenv("APP_ENV", "production")
    for base in ("", "http://mentor.example.test", "https://user:pass@example.test", "https://example.test?token=x", "https://[bad"):
        monkeypatch.setenv("RESET_PASSWORD_BASE_URL", base)
        assert client.post("/auth/forgot-password", json={"email": "learner@example.com"}).status_code == 200
    assert users.updates == [] and delivered == []


def test_reset_email_delegates_to_central_worker(security_client, monkeypatch):
    worker = AsyncMock(return_value=True)
    monkeypatch.setattr(auth, "deliver_reset_email", worker)
    assert asyncio.run(send_reset_email("learner@example.com", "https://mentor.example.test/reset-password?token=test-token")) is True
    worker.assert_awaited_once()


@pytest.mark.parametrize("provider,key_name", [("resend", "RESEND_API_KEY"), ("brevo", "BREVO_API_KEY")])
def test_reset_route_supports_https_email_without_smtp(security_client, monkeypatch, provider, key_name):
    client, users, delivered = security_client
    monkeypatch.setattr(auth.settings, "SMTP_HOST", "")
    monkeypatch.setattr(auth.settings, "EMAIL_PROVIDER", provider, raising=False)
    monkeypatch.setattr(auth.settings, key_name, "test-only-provider-key", raising=False)
    monkeypatch.setattr(auth.settings, "APP_ENV", "production", raising=False)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("RESET_PASSWORD_BASE_URL", raising=False)
    monkeypatch.setattr(auth.settings, "RESET_PASSWORD_BASE_URL", "https://mentor.example.test", raising=False)
    response = client.post("/auth/forgot-password", json={"email": "learner@example.com"})
    assert response.status_code == 200 and set(response.json()) == {"message"}
    assert len(delivered) == 1 and "password_reset_token_hash" in users.user


def test_reset_base_falls_back_to_configured_app_url(security_client, monkeypatch):
    monkeypatch.delenv("RESET_PASSWORD_BASE_URL", raising=False)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setattr(auth.settings, "APP_URL", "https://mentor.example.test", raising=False)
    assert auth.reset_base_url() == "https://mentor.example.test"


def test_password_byte_bounds_and_legacy_login():
    with pytest.raises(ValidationError):
        UserCreate(name="Learner", email="learner@example.com", password="é" * 37)
    with pytest.raises(ValidationError):
        ResetPasswordRequest(token="token", password="short")
    assert UserLogin(email="learner@example.com", password="old").password == "old"
    password = "é" * 36
    assert tokens.verify_password(password, tokens.hash_password(password))
    assert not tokens.verify_password(password + "é", tokens.hash_password(password))
    with pytest.raises(ValueError):
        tokens.hash_password("x" * 73)


@pytest.mark.parametrize("model,data", [
    (UserCreate, {"name": " ", "email": "learner@example.com", "password": "password"}),
    (UserCreate, {"name": "Learner", "email": "learner@example.com", "password": "password", "interests": ["python"] * 21}),
    (AIChatRequest, {"topic_slug": "python", "message": "x" * 8001}),
    (AIChatRequest, {"topic_slug": "python", "message": "Explain this", "subtopic_title": "x" * 201}),
    (AIRecommendRequest, {"topic_slug": "python", "answers": {"answer": "x" * 16385}}),
    (CodeSubmitRequest, {"language": "shell", "code": "whoami"}),
    (CodeSubmitRequest, {"language": "python", "code": "é" * 32769}),
    (ActivityLogCreate, {"minutes_spent": -1, "activity_type": "practice"}),
    (ActivityLogCreate, {"minutes_spent": 1441, "activity_type": "practice"}),
    (ActivityLogCreate, {"minutes_spent": True, "activity_type": "practice"}),
    (ProgressUpdate, {"topic_slug": "python", "status": "invalid"}),
])
def test_input_bounds(model, data):
    with pytest.raises(ValidationError):
        model(**data)
import asyncio


def test_chat_grounding_and_topic_metadata_preserved():
    request = AIChatRequest(topic_slug="python", message="Explain this", subtopic_title="Variables")
    assert request.subtopic_title == "Variables"
    topic = TopicResponse(id="python", domain_slug="python", slug="python", title="Python", difficulty="beginner",
                          schema_version=1, objectives=["Understand values"], prerequisites=["intro"], order=2)
    assert topic.model_dump()["objectives"] == ["Understand values"]
    assert topic.schema_version == 1 and topic.order == 2
