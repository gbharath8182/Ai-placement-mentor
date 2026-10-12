# Active architecture

This describes the active application source inspected during cleanup, including concurrent contributor changes, not the behavior of historical scripts or a guarantee of production hardening. Read route implementations when changing a contract.

## Request flow

```text
Browser: frontend HTML/CSS/JavaScript
  -> FastAPI: backend.main:app
     -> API routers + Pydantic models
        -> Motor -> MongoDB
        -> httpx -> Groq (AI features)
        -> SMTP or HTTPS Resend/Brevo (password recovery)
```

`backend/main.py` creates the FastAPI app, registers routers, serves friendly HTML page routes, and mounts `frontend/` at `/static`. Its lifespan connects, pings, and disconnects the shared database client. `/health/live` reports process liveness; `/health/ready` checks database connectivity and returns 503 when unavailable. Frontend scripts use same-origin APIs; there is no frontend framework build step. File serving currently uses repository-root-relative paths, so launch the app from that directory.

`/`, `/learn`, and `/topic/{slug}` are public learning entry points. The browser auth guard leaves them accessible without tokens; personal progress, assessments, practice submission, and tutor actions require authentication. `backend/middleware.py` enforces request-size/origin controls, bounded in-process rate limiting, and response safety headers; these are not a distributed rate-limit service.

## Backend boundaries

| Area | Modules and behavior |
| --- | --- |
| Configuration and storage | `backend/config.py` loads environment settings. `backend/database.py` owns the Motor client, collection access, bounded connectivity checks, and index helpers. TLS options depend on the URI; Atlas requires TLS and certificate verification. |
| Models and identity | `backend/models.py` defines shared Pydantic schemas; some routes define additional request schemas locally. `backend/auth.py` handles bcrypt and JWT validation with MongoDB-backed user lookup. |
| Authentication | `routes/auth.py`: signup, login, refresh, logout, current user, and password recovery under `/auth`. `backend/email_delivery.py` provides SMTP or HTTPS Resend/Brevo delivery. Protected routes use bearer access tokens. Refresh tokens are set as HttpOnly cookies and also returned in JSON; frontend auth helpers store tokens in localStorage and retry after a refresh. |
| Curriculum | `routes/content.py`: `/domains`, `/domains/{slug}/topics`, `/topics/{slug}`. `routes/domain_details.py`: extended domain metadata under `/domains`. |
| Learning AI | `routes/ai.py`: recommendations, explanations, and topic-grounded chat under `/ai`, with SSE chat streaming and persisted topic chat history. |
| Interview and resume | `routes/mock_interview.py`: interview generation/grading under `/mock-interview`, with MongoDB-backed interview sessions. `routes/resume.py`: two-stage resume generation plus authenticated PDF export. `resume_document.py` parses writer output into bounded document blocks, preserves supplied link destinations, and renders selectable A4 PDF text without fetching URLs. |
| Practice and progress | `routes/practice.py`: problem retrieval and server-side submission checking under `/practice`, through a configured remote sandbox. `routes/progress.py`: user learning status under `/progress`. |
| Checks and mastery | `routes/learning.py`: authenticated check retrieval, grading, and mastery under `/learning`. `backend/mastery.py` records assessment evidence and computes summaries; completion is not accepted as an unverified client assertion. |
| Activity and analytics | `routes/activity.py`: study activity, streaks, heatmap, and time reporting under `/activity`. `routes/analytics.py`: overview, domain time, solved trends, and skill coverage under `/analytics`. |

## Data ownership

MongoDB curriculum collections are `domains`, `domain_details`, `topics`, and `practice_problems`; slugs connect topic and domain content. User-facing state lives in `users`, `user_progress`, `user_mastery`, `activity_log`, `streaks`, `chat_sessions`, and `interview_sessions`, with BSON identifiers used in stored relationships. Analytics reads curriculum/progress/activity data rather than a separate analytics service.

`backend/curriculum.py` validates versioned authored curriculum from `curriculum/`. The maintained importer currently handles domains/topics only, with insert-only application and a recovery receipt; this is distinct from historical exporters and destructive seeds.

Curriculum import is an operational workflow, not an application startup action. Keep maintained import/smoke helpers in `scripts/`; `scripts/legacy/` is archival and must not be used against production.

## Frontend and external services

The HTML pages load shared `auth.js`, theme/activity helpers, and feature-specific JavaScript. `topic.js` renders dynamic content and practice; `ai-sidebar.js` handles learning chat; dashboard, roadmap, interview, resume, profile, and analytics scripts implement their respective views.

Topic practice submits code to `/practice/{problem_id}/submit`, which checks server-stored test cases through a trusted HTTPS Piston-compatible endpoint configured with `PISTON_EXECUTE_URL`. The standalone playground calls `/practice/run` with bounded user-authored test cases. Neither frontend path loads Pyodide or evaluates submitted JavaScript locally. Missing remote execution configuration returns an unavailable response. Stored-problem grading contributes server-verified coding evidence; user-authored playground cases are not proof of curriculum mastery.

`backend/ai_provider.py` centralizes Groq requests, bounded retries, primary/fallback selection, structured-response validation, and classified errors for learning/interview flows. Resume generation uses planning and drafting stages with different model choices. Missing AI credentials are reported as unavailable by the shared provider rather than successful simulated learning responses. Treat configured live AI/email and remote execution calls as external side effects when validating.

Password recovery queues background delivery through `backend/email_delivery.py`. `EMAIL_PROVIDER` accepts `smtp`, `resend`, `brevo`, or `auto`; auto selects Resend when its key is configured, otherwise Brevo when its key is configured, otherwise SMTP. All transports require a sender in `SMTP_FROM_EMAIL`. HTTPS transports use `RESEND_API_KEY` or `BREVO_API_KEY`; SMTP uses its host/port and optional authentication with verified TLS. Delivery is time-bounded, failures are logged without raw provider responses or credentials, and provider acceptance does not establish mailbox receipt. Use controlled recipients or mocks, never real users, in validation.

## Contributor entry points

See [CONTRIBUTING.md](../CONTRIBUTING.md) for local development and validation boundaries, [scripts/README.md](../scripts/README.md) for maintained operational tooling, and [the legacy warning](../scripts/legacy/README.md) for historical material. Dependency and deployment Python pins remain in `requirements.txt` and `runtime.txt`; `requirements-dev.txt` adds pytest. CI uses Python 3.11, scans tracked files for secret patterns, runs pytest (including unittest cases), executes dependency-free Node frontend smoke tests, and checks JavaScript syntax. These mocked checks are separate from optional real-service smoke checks.
