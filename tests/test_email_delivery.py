import asyncio
import json
import ssl
import threading
from unittest.mock import MagicMock

import httpx
import pytest

from backend import email_delivery as delivery

RealAsyncClient = httpx.AsyncClient
RECIPIENT = "learner@example.com"
RESET_LINK = "https://mentor.example.test/reset-password?token=test-only-reset-token"


@pytest.fixture(autouse=True)
def email_settings(monkeypatch):
    values = {
        "EMAIL_PROVIDER": "auto", "RESEND_API_KEY": "", "BREVO_API_KEY": "",
        "SMTP_FROM_EMAIL": "sender@example.com", "SMTP_HOST": "smtp.example.test", "SMTP_PORT": 587,
        "SMTP_USERNAME": "", "SMTP_PASSWORD": "",
    }
    for name, value in values.items():
        monkeypatch.setattr(delivery.settings, name, value, raising=False)
    monkeypatch.delenv("RENDER", raising=False)


def configure_http(monkeypatch, provider, handler):
    monkeypatch.setattr(delivery.settings, "EMAIL_PROVIDER", provider, raising=False)
    monkeypatch.setattr(delivery.settings, f"{provider.upper()}_API_KEY", "test-only-api-key", raising=False)
    options_seen = []

    def factory(**options):
        options_seen.append(options)
        return RealAsyncClient(transport=httpx.MockTransport(handler), **options)

    monkeypatch.setattr(delivery.httpx, "AsyncClient", factory)
    return options_seen


@pytest.mark.parametrize("provider", ["resend", "brevo"])
def test_https_provider_contract_and_idempotency(monkeypatch, caplog, provider):
    requests = []
    caplog.set_level("INFO", logger="uvicorn.error")

    def handler(request):
        requests.append(request)
        return httpx.Response(201, json={"id" if provider == "resend" else "messageId": "test-delivery-id"})

    options = configure_http(monkeypatch, provider, handler)
    assert asyncio.run(delivery.deliver_reset_email(RECIPIENT, RESET_LINK)) is True
    assert asyncio.run(delivery.deliver_reset_email(RECIPIENT, RESET_LINK)) is True
    body = json.loads(requests[0].content)
    if provider == "resend":
        assert str(requests[0].url) == "https://api.resend.com/emails"
        assert requests[0].headers["Authorization"] == "Bearer test-only-api-key"
        assert body["from"] == "sender@example.com" and body["to"] == [RECIPIENT]
        assert RESET_LINK in body["text"]
        key = "Idempotency-Key"
    else:
        assert str(requests[0].url) == "https://api.brevo.com/v3/smtp/email"
        assert requests[0].headers["api-key"] == "test-only-api-key"
        assert body["sender"] == {"email": "sender@example.com"} and body["to"] == [{"email": RECIPIENT}]
        assert RESET_LINK in body["textContent"]
        key = "idempotencyKey"
    assert requests[0].headers[key] == requests[1].headers[key]
    assert "test-only-reset-token" not in requests[0].headers[key]
    assert options[0]["follow_redirects"] is False and options[0]["trust_env"] is False
    assert options[0]["timeout"].connect == 3 and options[0]["timeout"].read == 15
    assert "accepted" in caplog.text
    for sensitive in (RECIPIENT, RESET_LINK, "test-only-api-key", "test-delivery-id"):
        assert sensitive not in caplog.text


@pytest.mark.parametrize("provider", ["resend", "brevo"])
@pytest.mark.parametrize("status", [301, 400, 401, 429, 500])
def test_provider_rejection_is_redacted_without_retry(monkeypatch, caplog, provider, status):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, headers={"Location": "https://attacker.test"}, text="sensitive provider response")

    configure_http(monkeypatch, provider, handler)
    assert asyncio.run(delivery.deliver_reset_email(RECIPIENT, RESET_LINK)) is False
    assert len(calls) == 1 and "sensitive provider response" not in caplog.text
    assert RECIPIENT not in caplog.text and RESET_LINK not in caplog.text


@pytest.mark.parametrize("provider", ["resend", "brevo"])
@pytest.mark.parametrize("content", [b"not-json", b"[]", b"{}", b'{"id":123,"messageId":123}', b'{"id":"ok","messageId":"ok","error":"sensitive"}', b"x" * 8193])
def test_malformed_or_oversized_success_is_not_accepted(monkeypatch, caplog, provider, content):
    configure_http(monkeypatch, provider, lambda request: httpx.Response(200, content=content))
    assert asyncio.run(delivery.deliver_reset_email(RECIPIENT, RESET_LINK)) is False
    assert "sensitive" not in caplog.text


def test_auto_prefers_https_without_smtp_fallback_on_timeout(monkeypatch, caplog):
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("sensitive provider credentials", request=request)

    configure_http(monkeypatch, "resend", handler)
    monkeypatch.setattr(delivery.settings, "EMAIL_PROVIDER", "auto", raising=False)
    smtp = MagicMock()
    monkeypatch.setattr(delivery, "send_smtp", smtp)
    assert asyncio.run(delivery.deliver_reset_email(RECIPIENT, RESET_LINK)) is False
    smtp.assert_not_called()
    assert len(calls) == 1 and "sensitive provider credentials" not in caplog.text


def test_auto_provider_selection_and_explicit_override(monkeypatch):
    assert delivery.selected_provider() == "smtp"
    monkeypatch.setattr(delivery.settings, "BREVO_API_KEY", "test-brevo", raising=False)
    assert delivery.selected_provider() == "brevo"
    monkeypatch.setattr(delivery.settings, "RESEND_API_KEY", "test-resend", raising=False)
    assert delivery.selected_provider() == "resend"
    monkeypatch.setattr(delivery.settings, "EMAIL_PROVIDER", "smtp", raising=False)
    assert delivery.selected_provider() == "smtp"


@pytest.mark.parametrize("name,value", [("EMAIL_PROVIDER", "invalid"), ("SMTP_FROM_EMAIL", ""), ("SMTP_FROM_EMAIL", "sender@example.com\r\nInjected: header"), ("RESEND_API_KEY", "bad\nkey")])
def test_invalid_configuration_fails_without_sending(monkeypatch, name, value):
    monkeypatch.setattr(delivery.settings, "EMAIL_PROVIDER", "resend", raising=False)
    monkeypatch.setattr(delivery.settings, "RESEND_API_KEY", "test-only-api-key", raising=False)
    monkeypatch.setattr(delivery.settings, name, value, raising=False)
    client = MagicMock()
    monkeypatch.setattr(delivery.httpx, "AsyncClient", client)
    assert asyncio.run(delivery.deliver_reset_email(RECIPIENT, RESET_LINK)) is False
    client.assert_not_called()


@pytest.mark.parametrize("port", [587, 465])
def test_smtp_verified_tls_timeout_and_authentication(monkeypatch, port):
    monkeypatch.setattr(delivery.settings, "EMAIL_PROVIDER", "smtp", raising=False)
    monkeypatch.setattr(delivery.settings, "SMTP_PORT", port)
    monkeypatch.setattr(delivery.settings, "SMTP_USERNAME", "test-user")
    monkeypatch.setattr(delivery.settings, "SMTP_PASSWORD", "test-only-password")
    smtp = MagicMock()
    smtp.return_value.__enter__.return_value.send_message.return_value = {}
    monkeypatch.setattr(delivery.smtplib, "SMTP_SSL" if port == 465 else "SMTP", smtp)
    assert asyncio.run(delivery.deliver_reset_email(RECIPIENT, RESET_LINK)) is True
    assert smtp.call_args.kwargs["timeout"] == 10
    server = smtp.return_value.__enter__.return_value
    if port == 465:
        context = smtp.call_args.kwargs["context"]
        server.starttls.assert_not_called()
    else:
        server.starttls.assert_called_once()
        context = server.starttls.call_args.kwargs["context"]
    assert context.check_hostname is True and context.verify_mode == ssl.CERT_REQUIRED
    server.login.assert_called_once_with("test-user", "test-only-password")


def test_smtp_tls_failure_cannot_fall_back_to_plaintext(monkeypatch, caplog):
    smtp = MagicMock()
    server = smtp.return_value.__enter__.return_value
    server.starttls.side_effect = RuntimeError("sensitive SMTP response")
    monkeypatch.setattr(delivery.smtplib, "SMTP", smtp)
    assert asyncio.run(delivery.deliver_reset_email(RECIPIENT, RESET_LINK)) is False
    server.send_message.assert_not_called()
    assert "sensitive SMTP response" not in caplog.text


def test_smtp_runs_off_event_loop_and_render_warning_is_sanitized(monkeypatch, caplog):
    thread_ids = []
    main_thread = threading.get_ident()
    original = delivery.send_smtp
    smtp = MagicMock()
    smtp.return_value.__enter__.return_value.send_message.return_value = {}
    monkeypatch.setattr(delivery.smtplib, "SMTP", smtp)
    monkeypatch.setenv("RENDER", "true")

    def capture_thread(email, link):
        thread_ids.append(threading.get_ident())
        original(email, link)

    monkeypatch.setattr(delivery, "send_smtp", capture_thread)
    assert asyncio.run(delivery.deliver_reset_email(RECIPIENT, RESET_LINK)) is True
    assert thread_ids[0] != main_thread
    assert "Render Free" in caplog.text and RECIPIENT not in caplog.text


def test_https_whole_delivery_deadline(monkeypatch):
    async def handler(request):
        await asyncio.sleep(1)
        return httpx.Response(201, json={"id": "test-delivery-id"})

    configure_http(monkeypatch, "resend", handler)
    monkeypatch.setattr(delivery, "DELIVERY_TIMEOUT_SECONDS", 0.01)
    assert asyncio.run(delivery.deliver_reset_email(RECIPIENT, RESET_LINK)) is False
