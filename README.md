# AI Placement Mentor

A placement-preparation learning app built with FastAPI, MongoDB, and vanilla HTML/CSS/JavaScript. Browse lessons publicly, then sign in for contextual AI tutoring, assessments, coding practice, interview preparation, and resume drafting.

> **[Live application](https://ai-placement-mentor-zo2w.onrender.com/)** · **[GitHub repository](https://github.com/gbharath8182/Ai-placement-mentor)**
>
> This repository documents V2 source. A successful push does not by itself confirm that Render has deployed it; check the deployed version and readiness before using new workflows.

**Operational warning:** do NOT run `scripts/legacy/` or `backend/seed.py.DEPRECATED_DO_NOT_RUN` against production. No production database import, migration, or reset was performed during this work.

## What the current source supports

- **Public learning:** landing page at `/`, curriculum at `/learn`, and lessons at `/topic/{slug}`, without a login wall. Personal learning actions require authentication.
- **Structured curriculum:** fifteen version-controlled Python lessons and fifteen linked tasks with objectives, prerequisites, worked examples, diagrams and thirty knowledge checks. Existing MongoDB content takes priority; new authored lessons are available without a seed or import.
- **Contextual tutor:** lesson/section-grounded prompts, SSE streaming, stop/retry controls, and per-topic history. Groq defaults to `openai/gpt-oss-20b` with `openai/gpt-oss-120b` as fallback; model selection, retries, and structured-response validation are centralized. Missing credentials produce an unavailable error, not pretend successful AI output.
- **Assessment feedback:** server-graded lesson checks and server-verified coding evidence inform transparent mastery/review heuristics. These scores are **not scientifically calibrated learning probabilities, proof of retention, or employment guarantees**.
- **Remote coding:** topic submissions use stored test cases; the playground accepts bounded user-authored cases. Neither executes submitted code in the browser. Both require a trusted Piston-compatible HTTPS service. **`PISTON_EXECUTE_URL` is intentionally empty; live execution is unavailable until configured.**
- **Interview and resume:** authenticated interviews with persisted sessions and structured feedback; two-stage resume planning/drafting with safe frontend rendering. Generated advice and resumes still require human review.
- **Accounts and tracking:** bcrypt password hashing, bearer access tokens, refresh cookies, password recovery, progress, activity, analytics, roadmap, cheatsheets, and aptitude views. Frontend auth storage also contains tokens; this is not a cookie-only authentication design.

## Stack and layout

| Layer | Current implementation |
| --- | --- |
| Backend | FastAPI `0.143.0`, Pydantic 2, Uvicorn |
| Database | MongoDB via Motor/PyMongo, bounded connectivity checks and TLS verification |
| Frontend | HTML, CSS, vanilla JavaScript; no npm build required |
| AI | Groq HTTPS API, configurable primary/fallback models |
| Email | SMTP with verified TLS, or HTTPS Resend/Brevo |
| Code runner | Explicitly configured remote Piston-compatible sandbox |
| Validation | pytest including unittest cases, Node built-in smoke tests, JS syntax checks, secret-pattern scan |

```text
backend/                  API routes, auth, AI/email providers, curriculum/mastery logic
frontend/                 Public and authenticated pages, CSS, JavaScript
curriculum/               Authored lessons, practice tasks, interview benchmark data
scripts/                  Maintained importer, live smoke, secret-pattern checker
scripts/legacy/           Historical archive; NOT a supported setup pipeline
tests/                    Backend tests and frontend-smoke.test.js
docs/                     Architecture, deployment, mastery, database recovery
.github/workflows/        Automated checks
.env.example              Non-secret configuration template
requirements.txt          Runtime dependencies
requirements-dev.txt      Runtime dependencies plus pytest
runtime.txt               Unchanged deployment pin: python-3.11.9
```

## Local setup

Use an isolated environment and a **disposable local/test database**, never production credentials. Python `3.11.9` remains the deployment target; an isolated local Python 3.13 environment with the current FastAPI stack is also being validated. Do not assume the machine's global Python/dependencies match either environment.

From the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

On Linux/macOS, use `python3.11 -m venv .venv` and `.venv/bin/python` instead. Create your own untracked `.env` from `.env.example` **only if one does not already exist**; do not overwrite another contributor's configuration or backups. Set a fresh random `JWT_SECRET`, your test `MONGO_URI`, and the correct origin. The app requires a nonempty JWT secret even locally.

```dotenv
APP_ENV=development
APP_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:8000
COOKIE_SECURE=false
MONGO_URI=mongodb://localhost:27017/placement_mentor_dev
JWT_SECRET=<fresh-random-secret-at-least-32-characters>
GROQ_API_KEY=
PISTON_EXECUTE_URL=
EMAIL_PROVIDER=auto
RESET_PASSWORD_BASE_URL=http://localhost:8000
```

Local MongoDB must be running. Atlas requires a database user, an explicitly selected database, TLS, and approved network access. Add optional AI/email credentials only when you intend to make real external requests.

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

Open [the local app](http://localhost:8000). Launch from the repository root because static/page paths are relative to it. See [deployment instructions](docs/deployment.md) for exact Render commands, environment settings, and email troubleshooting.

## Configuration and safety

- `APP_URL`, `ALLOWED_ORIGINS`, and `RESET_PASSWORD_BASE_URL` must match your trusted application origin. Production uses HTTPS and secure refresh cookies.
- `GROQ_PRIMARY_MODEL` and `GROQ_FALLBACK_MODEL` default to `openai/gpt-oss-20b` and `openai/gpt-oss-120b`. AI requests may incur costs.
- `EMAIL_PROVIDER` accepts `auto`, `smtp`, `resend`, or `brevo`. All transports use `SMTP_FROM_EMAIL` as the sender. HTTPS providers use `RESEND_API_KEY` or canonical `BREVO_API_KEY`.
- The current Brevo 401 was confirmed as an **IP authorization block**, not an invalid key. Authorizing the user's trusted source IP is pending; sender verification and actual delivery remain unverified. See [email troubleshooting](docs/deployment.md#email-on-render-free-and-brevo-troubleshooting).
- `PISTON_EXECUTE_URL` must identify an operator-approved HTTPS sandbox; optional `PISTON_API_KEY` authenticates to it. Do not point the app at an untrusted runner or execute untrusted code in the web-service process.
- Built-in authored content is distinct from existing Atlas content. The maintained importer previews domains/topics and requires explicit, journaled insert-only application. It is not an automatic production migration; consult [tool safety](scripts/README.md).

## Validation

```text
python -m pytest tests
node --test tests/frontend-smoke.test.js
python scripts/check_secrets.py
```

Run these inside the chosen virtual environment. CI uses Python 3.11, installs `requirements-dev.txt`, and runs pytest, the Node suite, all frontend JavaScript syntax checks, and the tracked-file secret scan. After staging changes locally, use `python scripts/check_secrets.py --staged`; a pre-stage scan does not cover untracked files.

**Verified locally (2026-10-12):** 325 backend tests and 381 subtests passed; 35 Node behavior tests passed. All twelve free-library destinations passed bounded live checks, including PDF signatures and chapter anchors. Real Edge checks cover desktop/mobile layout and theme/tutor controls. Local checks do not establish that the upgraded revision is deployed. Node tests use isolated VM/fake-DOM behavior checks; browser checks are separate.

Real Groq 20b/120b completions and streaming passed. Read-only Atlas checks passed with 10 users, 10 domains, 71 topics, and 41 progress records at that checkpoint. No production database writes were made; service connectivity does not prove all features are ready. Email remains IP-blocked and remote execution remains unconfigured.

Optional maintained smoke checks require explicit approval of their targets and side effects. Do not substitute archived scripts for tests. See [contributor guidance](CONTRIBUTING.md), [architecture](docs/architecture.md), [mastery limitations](docs/mastery.md), and [database recovery](docs/database-recovery.md).

## Pages and APIs

Public pages: `/`, `/learn`, `/topic/{slug}`, `/login`, `/signup`, `/forgot-password`, `/reset-password`.

Personal views: `/dashboard`, `/playground`, `/mock-interview`, `/resume`, `/analytics`, `/profile`, `/roadmap`, `/cheatsheets`, `/aptitude`.

API groups include `/auth`, `/curriculum`, `/domains`, `/topics`, `/learning`, `/ai`, `/practice`, `/progress`, `/activity`, `/analytics`, `/mock-interview`, and `/resume`. `/health/live` checks process liveness; `/health/ready` checks MongoDB connectivity.
