import argparse
import asyncio
import json
import sys

import httpx

from backend.ai_provider import AIProviderError, provider
from backend.config import settings
from backend.database import db_client


async def smoke(options):
    passed = True
    if options.email_config:
        if not settings.BREVO_API_KEY:
            print(json.dumps({"check": "email_config", "passed": False, "kind": "not_configured"}))
            passed = False
        else:
            async with httpx.AsyncClient(timeout=15, follow_redirects=False, trust_env=False) as client:
                for path in ["account", "senders"]:
                    try:
                        response = await client.get(f"https://api.brevo.com/v3/{path}", headers={"api-key": settings.BREVO_API_KEY})
                        print(json.dumps({"check": "email_config", "endpoint": path, "status": response.status_code}))
                        passed = passed and response.is_success
                        if response.status_code == 401:
                            message = str(response.json().get("message", "")).lower()
                            blocked_ip = any(value in message for value in ["ip address", "unrecognised ip", "unrecognized ip", "unauthorized ip"])
                            print(json.dumps({"check": "email_authentication", "kind": "ip_not_authorized" if blocked_ip else "key_rejected"}))
                        if path == "senders" and response.is_success:
                            from email.utils import parseaddr
                            sender_address = parseaddr(settings.SMTP_FROM_EMAIL)[1].lower()
                            senders = response.json().get("senders", [])
                            match = [sender for sender in senders if sender.get("email", "").lower() == sender_address]
                            active = any(sender.get("active") is True for sender in match)
                            print(json.dumps({"check": "configured_sender", "passed": active, "verified_sender_count": sum(sender.get("active") is True for sender in senders)}))
                            passed = passed and active
                    except (httpx.RequestError, ValueError):
                        print(json.dumps({"check": "email_config", "passed": False, "kind": "network_or_response"}))
                        passed = False
    if options.ai:
        try:
            available = await provider.available_models()
            for model in dict.fromkeys([settings.GROQ_PRIMARY_MODEL, settings.GROQ_FALLBACK_MODEL]):
                active = model in available
                print(json.dumps({"check": "model_access", "model": model, "passed": active}))
                passed = passed and active
                if active:
                    result = await provider.complete([{"role": "user", "content": "Reply with the single word OK."}], model=model)
                    exact_model = result.model == model and bool(result.text.strip())
                    print(json.dumps({"check": "completion", "model": result.model, "passed": exact_model}))
                    passed = passed and exact_model
            chunks = [chunk async for chunk in provider.stream([{"role": "user", "content": "Reply with the single word OK."}])]
            print(json.dumps({"check": "streaming", "passed": bool(chunks)}))
            passed = passed and bool(chunks)
        except (AIProviderError, httpx.RequestError) as error:
            print(json.dumps({"check": "ai", "passed": False, "kind": getattr(error, "kind", "network")}))
            passed = False
    if options.database:
        try:
            db_client.connect()
            ready = await db_client.ping()
            print(json.dumps({"check": "database_ping", "passed": ready}))
            passed = passed and ready
            if ready:
                for collection in ["domains", "topics", "users", "user_progress"]:
                    count = await db_client.db[collection].count_documents({})
                    print(json.dumps({"check": "collection_count", "collection": collection, "count": count}))
                shapes = []
                async for document in db_client.db["topics"].find({}, {"subtopics": 1, "content_blocks": 1}).limit(5):
                    shapes.append({"subtopics": len(document.get("subtopics", [])), "top_level_blocks": len(document.get("content_blocks", []))})
                print(json.dumps({"check": "topic_schema_shapes", "shapes": shapes}))
        except (RuntimeError, Exception) as error:
            print(json.dumps({"check": "database", "passed": False, "kind": type(error).__name__}))
            passed = False
        finally:
            db_client.disconnect()
    if options.deployment:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for path in ["/", "/login", "/domains", "/topic/sde-programming-foundations", "/health/ready"]:
                try:
                    response = await client.get(options.deployment.rstrip("/") + path)
                    print(json.dumps({"check": "deployment", "path": path, "status": response.status_code}))
                    passed = passed and response.is_success
                except httpx.RequestError:
                    print(json.dumps({"check": "deployment", "path": path, "passed": False, "kind": "network"}))
                    passed = False
    return passed


def main():
    parser = argparse.ArgumentParser(description="Optional real-service checks; never prints secrets or writes to MongoDB.")
    parser.add_argument("--ai", action="store_true", help="Check account models and make minimal paid AI requests.")
    parser.add_argument("--database", action="store_true", help="Read-only ping, collection counts and schema shapes.")
    parser.add_argument("--deployment", help="Base URL to check; this does not trigger a deployment.")
    parser.add_argument("--email-config", action="store_true", help="Check Brevo account/sender access; does not send any email.")
    options = parser.parse_args()
    if not (options.ai or options.database or options.deployment or options.email_config):
        parser.error("Select at least one check")
    return 0 if asyncio.run(smoke(options)) else 1


if __name__ == "__main__":
    sys.exit(main())
