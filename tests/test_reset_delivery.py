import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from scripts import test_reset_delivery as smoke

TEST_RECIPIENT = "reset-owner@example.com"

@pytest.fixture(autouse=True)
def authorized_test_recipient(monkeypatch):
    monkeypatch.setattr(smoke, "AUTHORIZED_RECIPIENT", TEST_RECIPIENT)


def test_confirmation_gate_has_no_service_access(monkeypatch, capsys):
    monkeypatch.setattr(smoke, "selected_provider", lambda: pytest.fail("No provider access before confirmation"))
    assert smoke.run(smoke.AUTHORIZED_RECIPIENT, "http://127.0.0.1:8879", False) == 2
    output = capsys.readouterr().out
    assert "confirm_send_required" in output
    assert smoke.AUTHORIZED_RECIPIENT not in output


@pytest.mark.parametrize("recipient,base", [
    ("another@example.com", "https://mentor.example.test"),
    (TEST_RECIPIENT, "http://external.example.test"),
    (TEST_RECIPIENT, "https://user:password@mentor.example.test"),
    (TEST_RECIPIENT, "https://mentor.example.test?token=sensitive"),
    (TEST_RECIPIENT, "https://[bad"),
])
def test_unsafe_options_rejected_without_pii(recipient, base, capsys):
    assert smoke.run(recipient, base, True) == 2
    output = capsys.readouterr().out
    assert recipient not in output and "password" not in output and "sensitive" not in output


@pytest.mark.parametrize("preflight,delivery,expected,attempts", [(False, True, 1, 0), (True, False, 1, 1), (True, True, 0, 1)])
def test_one_route_request_and_observable_acceptance(monkeypatch, capsys, preflight, delivery, expected, attempts):
    calls = []
    sender = AsyncMock(return_value=delivery)
    monkeypatch.setattr(smoke, "selected_provider", lambda: "brevo")
    monkeypatch.setattr(smoke, "delivery_available", lambda: True)
    monkeypatch.setattr(smoke, "account_exists", AsyncMock(return_value=True))
    monkeypatch.setattr(smoke, "brevo_preflight", AsyncMock(return_value=preflight))
    monkeypatch.setattr(smoke.auth, "send_reset_email", sender)
    monkeypatch.setattr(smoke.auth, "reset_base_url", lambda: "https://mentor.example.test")
    monkeypatch.setitem(sys.modules, "backend.main", SimpleNamespace(app=object()))

    class Client:
        portal = SimpleNamespace(call=lambda function, *args: asyncio.run(function(*args)))

        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, path, **options):
            calls.append(path)
            asyncio.run(smoke.auth.send_reset_email(options["json"]["email"], "test-only-reset-link"))
            return SimpleNamespace(status_code=200)

    monkeypatch.setattr(smoke, "TestClient", Client)
    assert smoke.run(smoke.AUTHORIZED_RECIPIENT, "https://mentor.example.test", True) == expected
    assert len(calls) == attempts and sender.await_count == attempts
    output = capsys.readouterr().out
    assert smoke.AUTHORIZED_RECIPIENT not in output and "test-only-reset-link" not in output
