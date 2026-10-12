import asyncio
import hashlib
import json
import logging
import os
import smtplib
import ssl
import uuid
from email.mime.text import MIMEText
from email.utils import parseaddr

import httpx

from backend.config import settings

logger = logging.getLogger("uvicorn.error")
DELIVERY_TIMEOUT_SECONDS = 30
MAX_RESPONSE_BYTES = 8192


def selected_provider():
    provider = getattr(settings, "EMAIL_PROVIDER", "auto").strip().lower()
    if provider not in {"auto", "smtp", "resend", "brevo"}:
        return None
    if provider != "auto":
        return provider
    if getattr(settings, "RESEND_API_KEY", ""):
        return "resend"
    if getattr(settings, "BREVO_API_KEY", ""):
        return "brevo"
    return "smtp"


def delivery_available() -> bool:
    provider = selected_provider()
    sender = getattr(settings, "SMTP_FROM_EMAIL", "")
    if not isinstance(sender, str) or not sender or "\r" in sender or "\n" in sender:
        return False
    address = parseaddr(sender)[1]
    if "@" not in address or len(address) > 254:
        return False
    if provider == "smtp":
        return bool(getattr(settings, "SMTP_HOST", ""))
    if provider in {"resend", "brevo"}:
        key = getattr(settings, f"{provider.upper()}_API_KEY", "")
        return isinstance(key, str) and 0 < len(key) <= 4096 and key.isascii() and not any(character.isspace() for character in key)
    return False


def reset_text(reset_link: str) -> str:
    return f"Hello,\n\nPlease use this link to reset your password:\n{reset_link}\n\nThis link is valid for 15 minutes. If you did not request it, ignore this email.\n"


def send_smtp(to_email: str, reset_link: str):
    port = getattr(settings, "SMTP_PORT", 587)
    if os.getenv("RENDER") and port in {25, 465, 587}:
        logger.warning("SMTP ports 25/465/587 are blocked on Render Free; configure an HTTPS email provider or a paid service")
    message = MIMEText(reset_text(reset_link))
    message["Subject"] = "Password Reset Request"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email
    context = ssl.create_default_context()
    options = {"timeout": 10}
    smtp_class = smtplib.SMTP
    if port == 465:
        smtp_class = smtplib.SMTP_SSL
        options["context"] = context
    with smtp_class(settings.SMTP_HOST, port, **options) as server:
        if port != 465:
            server.starttls(context=context)
        username = getattr(settings, "SMTP_USERNAME", "")
        password = getattr(settings, "SMTP_PASSWORD", "")
        if username or password:
            if not username or not password:
                raise ValueError("Incomplete SMTP authentication configuration")
            server.login(username, password)
        refused = server.send_message(message)
        if refused:
            raise RuntimeError("SMTP rejected delivery")


async def send_https(provider: str, to_email: str, reset_link: str) -> bool:
    digest = hashlib.sha256((to_email + "\n" + reset_link).encode("utf-8")).digest()
    idempotency_key = str(uuid.UUID(bytes=digest[:16], version=4))
    headers = {"Accept": "application/json", "User-Agent": "AI-placement-mentor/1.0"}
    if provider == "resend":
        endpoint = "https://api.resend.com/emails"
        headers.update({"Authorization": f"Bearer {getattr(settings, 'RESEND_API_KEY', '')}", "Idempotency-Key": idempotency_key})
        payload = {"from": settings.SMTP_FROM_EMAIL, "to": [to_email], "subject": "Password Reset Request", "text": reset_text(reset_link)}
        identity_key = "id"
    else:
        endpoint = "https://api.brevo.com/v3/smtp/email"
        headers.update({"api-key": getattr(settings, "BREVO_API_KEY", ""), "idempotencyKey": idempotency_key})
        payload = {"sender": {"email": parseaddr(settings.SMTP_FROM_EMAIL)[1]}, "to": [{"email": to_email}],
                   "subject": "Password Reset Request", "textContent": reset_text(reset_link)}
        identity_key = "messageId"
    async with httpx.AsyncClient(timeout=httpx.Timeout(15, connect=3, pool=3), follow_redirects=False, trust_env=False) as client:
        async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
            if not 200 <= response.status_code < 300:
                logger.error("Password reset email rejected (provider=%s status=%d)", provider, response.status_code)
                return False
            content = bytearray()
            async for chunk in response.aiter_bytes(chunk_size=4096):
                if len(content) + len(chunk) > MAX_RESPONSE_BYTES:
                    logger.error("Password reset email returned an oversized response (provider=%s)", provider)
                    return False
                content.extend(chunk)
    result = json.loads(content)
    identity = result.get(identity_key) if isinstance(result, dict) and "error" not in result else None
    if not isinstance(identity, str) or not 1 <= len(identity) <= 254:
        logger.error("Password reset email returned an invalid response (provider=%s)", provider)
        return False
    return True


async def deliver_reset_email(to_email: str, reset_link: str) -> bool:
    provider = selected_provider()
    if not delivery_available():
        logger.warning("Password reset email unavailable: configure EMAIL_PROVIDER, sender and provider credentials")
        return False
    try:
        if provider == "smtp":
            await asyncio.wait_for(asyncio.to_thread(send_smtp, to_email, reset_link), timeout=DELIVERY_TIMEOUT_SECONDS)
            accepted = True
        else:
            accepted = await asyncio.wait_for(send_https(provider, to_email, reset_link), timeout=DELIVERY_TIMEOUT_SECONDS)
    except Exception:
        logger.error("Password reset email delivery failed (provider=%s)", provider)
        return False
    if accepted:
        logger.info("Password reset email accepted (provider=%s)", provider)
    return accepted
