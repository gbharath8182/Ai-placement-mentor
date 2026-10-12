import argparse
import asyncio
import json
import logging
import os
from email.utils import parseaddr
from urllib.parse import urlsplit
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from pydantic import EmailStr, TypeAdapter, ValidationError

from backend.config import settings
from backend.database import get_collection
from backend.email_delivery import delivery_available, selected_provider
from backend.routes import auth

AUTHORIZED_RECIPIENT = os.getenv("RESET_TEST_RECIPIENT", "")


def emit(check, **fields):
    print(json.dumps({"check": check, **fields}))


def validate_options(recipient, base_url):
    try:
        normalized = str(TypeAdapter(EmailStr).validate_python(recipient))
    except ValidationError:
        raise ValueError("recipient_invalid") from None
    if normalized.casefold() != AUTHORIZED_RECIPIENT.casefold():
        raise ValueError("recipient_not_authorized")
    if any(character.isspace() or ord(character) < 32 for character in base_url):
        raise ValueError("base_url_invalid")
    try:
        parsed = urlsplit(base_url)
        parsed.port
    except ValueError:
        raise ValueError("base_url_invalid") from None
    if (not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.scheme not in {"http", "https"}
            or (parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"})):
        raise ValueError("base_url_invalid")
    return normalized, base_url.rstrip("/")


async def account_exists(recipient):
    user = await asyncio.wait_for(
        get_collection("users").find_one({"email": recipient}, {"_id": 1}), timeout=10,
    )
    return user is not None


async def brevo_preflight():
    sender = parseaddr(getattr(settings, "SMTP_FROM_EMAIL", ""))[1].casefold()
    async with httpx.AsyncClient(timeout=httpx.Timeout(10, connect=3), follow_redirects=False, trust_env=False) as client:
        for endpoint in ("account", "senders"):
            async with client.stream(
                "GET", f"https://api.brevo.com/v3/{endpoint}",
                headers={"api-key": getattr(settings, "BREVO_API_KEY", "")},
            ) as response:
                emit("brevo_preflight", endpoint=endpoint, status=response.status_code)
                if not response.is_success:
                    return False
                if endpoint == "account":
                    continue
                content = bytearray()
                async for chunk in response.aiter_bytes(chunk_size=4096):
                    if len(content) + len(chunk) > 65536:
                        return False
                    content.extend(chunk)
                result = json.loads(content)
                senders = result.get("senders") if isinstance(result, dict) else None
                if not isinstance(senders, list):
                    return False
                verified = any(
                    isinstance(item, dict) and isinstance(item.get("email"), str)
                    and item["email"].casefold() == sender and item.get("active") is True
                    for item in senders
                )
                emit("configured_sender", verified=verified)
                return verified
    return False


def run(recipient, base_url, confirm_send):
    if not confirm_send:
        emit("reset_delivery", accepted=False, kind="confirm_send_required")
        return 2
    try:
        recipient, base_url = validate_options(recipient, base_url)
    except ValueError as error:
        emit("reset_delivery", accepted=False, kind=str(error))
        return 2
    if selected_provider() != "brevo" or not delivery_available():
        emit("reset_delivery", accepted=False, kind="configure_brevo_and_verified_sender")
        return 2
    accepted = []
    original_send = auth.send_reset_email

    async def capture_delivery(email, reset_link):
        if accepted:
            raise RuntimeError("Duplicate delivery attempt refused")
        accepted.append(False)
        accepted[0] = await original_send(email, reset_link) is True
        return accepted[0]

    try:
        with patch.object(settings, "RESET_PASSWORD_BASE_URL", base_url, create=True), patch.dict(os.environ, {"RESET_PASSWORD_BASE_URL": base_url}):
            if auth.reset_base_url() != base_url:
                emit("reset_delivery", accepted=False, kind="reset_base_rejected_use_https")
                return 2
            from backend.main import app

            with TestClient(app, base_url=base_url, raise_server_exceptions=False) as client:
                exists = client.portal.call(account_exists, recipient)
                emit("authorized_account", exists=exists)
                if not exists:
                    return 1
                if not client.portal.call(brevo_preflight):
                    emit("reset_delivery", accepted=False, kind="provider_preflight_failed_no_send")
                    return 1
                with patch.object(auth, "send_reset_email", capture_delivery):
                    response = client.post("/auth/forgot-password", json={"email": recipient}, follow_redirects=False)
                successful = response.status_code == 200 and accepted == [True]
                emit("reset_delivery", status=response.status_code, attempts=len(accepted), accepted=successful)
                return 0 if successful else 1
    except Exception:
        emit("reset_delivery", accepted=False, kind="service_or_response_failure", attempts=len(accepted))
        return 1


def main():
    parser = argparse.ArgumentParser(description="Send exactly one real reset email to the explicitly authorized account; writes its reset digest only after confirmation and provider checks.")
    parser.add_argument("--to", required=True, help="Explicit user-owned, authorized recipient; never printed.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8879", help="Reset-link base URL; use HTTPS with production APP_ENV.")
    parser.add_argument("--confirm-send", action="store_true", help="Confirm one real reset request and its Atlas reset-digest write.")
    options = parser.parse_args()
    previous_logging = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        return run(options.to, options.base_url, options.confirm_send)
    finally:
        logging.disable(previous_logging)


if __name__ == "__main__":
    raise SystemExit(main())
