# Deployment and local operations

This guide describes the V2 checkout. The existing service is [AI Placement Mentor](https://ai-placement-mentor-zo2w.onrender.com/), linked to [the original repository](https://github.com/gbharath8182/Ai-placement-mentor). Check the latest deployed commit and readiness before assuming a source change is live. No production content import or collection replacement is required.

## Local setup

1. Work from the repository root. Install Python 3.11.9 for deployment parity; the separate local validation environment uses Python 3.13. Use a fresh virtual environment rather than global dependencies.
2. On Windows: `py -3.11 -m venv .venv`, then `.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt`. On Linux/macOS: `python3.11 -m venv .venv`, then `.venv/bin/python -m pip install -r requirements-dev.txt`.
3. If absent, create a private `.env` using `.env.example`. Never overwrite an existing environment or backup. Configure `APP_ENV=development`, `APP_URL=http://localhost:8000`, `ALLOWED_ORIGINS=http://localhost:8000`, `COOKIE_SECURE=false`, and `RESET_PASSWORD_BASE_URL=http://localhost:8000`.
4. Set a newly generated random `JWT_SECRET` (at least 32 characters) and a disposable test database, e.g. `MONGO_URI=mongodb://localhost:27017/placement_mentor_dev`. Run local MongoDB separately. Atlas requires authorized network access and TLS; do not disable certificate checks.
5. Start `python -m uvicorn backend.main:app --reload --port 8000` using the virtual environment's Python. Visit [localhost](http://localhost:8000), then check `/health/live` and `/health/ready`.

Leave AI/email keys and `PISTON_EXECUTE_URL` empty for offline/mocked work. Missing keys do not enable a successful demonstration AI mode. Database-backed actions still require MongoDB.

## Render web service

The user has approved the release and requested a push and deployed-version verification. Configure the existing service or a separate staging **Web Service**, not a Static Site. Keep its repository root at the top level so `backend/`, `frontend/`, and `curriculum/` are available. A push does not prove automatic deployment is enabled: check the Render service's deploy settings, linked branch, latest deployed commit, and deployment status.

| Setting | Value |
| --- | --- |
| Runtime | Python 3 |
| Python selection | `PYTHON_VERSION=3.11.9` |
| Build command | `python -m pip install -r requirements.txt` |
| Start command | `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| Health-check path | `/health/ready` |
| Root directory | Repository root (leave blank) |

Keep `runtime.txt` unchanged at `python-3.11.9`. Set `PYTHON_VERSION` explicitly instead of relying on a platform default or inferring version selection from this legacy file. Render documents the environment-variable override in [Python version configuration](https://render.com/docs/python-version). Binding `0.0.0.0:$PORT` is required for public traffic; see [Render web services](https://render.com/docs/web-services).

Set these in Render's private Environment settings, not in committed files:

| Variable | Production value |
| --- | --- |
| `APP_ENV` | `production` |
| `APP_URL` | Exact existing HTTPS deployment origin, without a trailing slash |
| `ALLOWED_ORIGINS` | Exact trusted HTTPS origin(s), comma-separated; no wildcard |
| `RESET_PASSWORD_BASE_URL` | Same trusted HTTPS app origin |
| `COOKIE_SECURE` | `true` |
| `JWT_SECRET` | Independent random production secret of at least 32 characters |
| `MONGO_URI` | Private Atlas URI with the intended database name and required permissions |
| `GROQ_API_KEY` | Approved Groq account API key |
| `GROQ_PRIMARY_MODEL` | `openai/gpt-oss-20b` |
| `GROQ_FALLBACK_MODEL` | `openai/gpt-oss-120b` |
| `PISTON_EXECUTE_URL` | Intentionally empty until a trusted HTTPS remote runner is approved |
| `PISTON_API_KEY` | Optional runner credential, only if the approved service requires it |

Do not override `PORT` to 8000; the start command uses Render's assigned port. Allow the service's actual outbound IP ranges in Atlas as needed, with a least-privilege database user; do not use a blanket open network rule as a shortcut. Get the service's ranges from **Connect → Outbound**, as described in [Render outbound IPs](https://render.com/docs/outbound-ip-addresses).

Use `/health/ready` for database-aware readiness; `/health/live` only proves the process responds. Render's [health checks](https://render.com/docs/health-checks) gate routing/restarts, so a database outage can make the service unhealthy. Neither endpoint proves AI, email, or remote execution is available.

Render Free can cold-start after inactivity and uses ephemeral local storage. Persist user data in MongoDB and keep any recovery receipts outside the service filesystem. See [Free service limitations](https://render.com/docs/free). Rate limiting is in-process, not a shared distributed limit.

## Email on Render Free and Brevo troubleshooting

Use an **HTTPS** transport on Render Free. Outbound SMTP ports 25, 465, and 587 are blocked on Free web services; switching SMTP passwords does not fix that network restriction. See [Render's SMTP restriction](https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports).

For Brevo, configure:

```dotenv
EMAIL_PROVIDER=brevo
BREVO_API_KEY=<private-api-key-from-brevo-not-an-smtp-key>
SMTP_FROM_EMAIL=<sender-address-verified-in-brevo>
RESET_PASSWORD_BASE_URL=<exact-trusted-https-app-origin>
```

For Resend instead, use `EMAIL_PROVIDER=resend`, private `RESEND_API_KEY`, and a sender authorized by that account in `SMTP_FROM_EMAIL`. Prefer an explicit provider over `auto` when deploying: auto prioritizes a configured Resend key, then Brevo, then SMTP.

**Current blocker:** the canonical Brevo key is active, but the 401 was confirmed via sanitized upstream error classification as an **unauthorized source IP**, not an invalid key. The user's approval of their trusted local IP is pending. `SMTP_FROM_EMAIL` is configured, but sender verification could not yet be confirmed; successful reset-email delivery has not been demonstrated.

1. In Brevo, have the account owner review **Security → Authorized IPs / Unauthorized IPs** and authorize only the recognized local source IP. Do not approve unfamiliar addresses or disable security globally. A valid key can still be blocked by IP policy: see [Brevo IP security](https://developers.brevo.com/docs/ip-security).
2. Separately authorize the Render service's outbound source ranges for deployment; local IP authorization does not cover Render. Review the risk of shared regional ranges; use a more narrowly controlled egress arrangement if required.
3. Confirm the selected private `BREVO_API_KEY` is an API key for the intended account, not an SMTP key. Use canonical `BREVO_API_KEY` rather than the legacy `bravo_key` fallback. Do not paste keys into logs or commit them.
4. Once IP access succeeds, check account access and the exact `SMTP_FROM_EMAIL` sender. Complete sender/domain verification in Brevo as necessary. Configuration alone is not verification.
5. Run the explicitly approved, **read-only** `python -m scripts.live_smoke --email-config` from the correct isolated environment. It checks Brevo account/sender endpoints and sends no email. Only after it passes, use a controlled test recipient to validate actual reset delivery.

A generic forgot-password response does not prove delivery, and provider acceptance does not guarantee inbox receipt. The normal reset flow stores token state and may send email: do not use a real user's account for smoke checks. Review classified failures without exposing reset links, credentials, or raw provider responses.

## Remote execution and curriculum

`PISTON_EXECUTE_URL` is intentionally empty. Code submission and playground execution should return an unavailable error until an operator-approved Piston-compatible HTTPS endpoint is configured. The web app itself is not the sandbox. Check required language/version support, authentication, isolation, resource limits, and network access before enabling it; do not substitute an arbitrary public runner.

The authored catalog contains 15 Python topics and 15 practice tasks. Built-in content does not mean it was imported into production. Do not add a seed/import operation to Render's build or start command. For a separately approved data operation, preview the maintained insert-only importer and review database identity, conflicts, exclusive-write confirmation, and an external recovery receipt. Never replay `scripts/legacy/` or the deprecated seed. See [tool guide](../scripts/README.md) and [database recovery](database-recovery.md).

## Release gate and checkpoint

For the user-approved release, main should rerun `python -m pytest tests` in the chosen isolated environment, `node --test tests/frontend-smoke.test.js`, JS syntax checks, and `python scripts/check_secrets.py --staged` after staging. CI targets Python 3.11; local Python 3.13 success is not a completed production-runtime validation. Keep secrets, backups, and browser artifacts out of the commit.

For point-in-time verification results and the authorized Atlas insert-only synchronization, see [the maintainer checkpoint](revamp-checkpoint.md). The source release passed GitHub CI; deployment must still be verified independently. Email IP authorization/sender verification and remote runner configuration remain release caveats.

After the approved push, check whether Render auto-deploy is enabled for the pushed branch. Verify the latest deployed commit matches the intended commit and its deployment completed successfully, then rerun approved read-only page/readiness checks. If auto-deploy is disabled or deployment failed, report that state rather than claiming the release is live. A push or passing local test does not establish that the new revision is serving traffic. See [README](../README.md) and [contributor guidance](../CONTRIBUTING.md).
