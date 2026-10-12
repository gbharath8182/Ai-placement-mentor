# V2 checkpoint — 12 October 2026

## Implemented increment

| Phase | Root cause and implementation | Verification |
| --- | --- | --- |
| 0 — Investigation | Audited FastAPI, MongoDB schemas, vanilla frontend and deployment assumptions; preserved the original stack and records. | Intended remote verified; production collection counts read only. |
| 1 — Groq | Replaced duplicated deprecated-model clients with configurable 20b/120b routing, bounded retries, structured schemas and safe SSE errors. | Real account model access, both completions and streaming passed; mocked failures and fallback passed. |
| 2 — Reliability | Bounded MongoDB operations, verified TLS, reconnectable lifecycle, liveness/readiness and curated content fallback. | Database recovery tests and real Atlas ping passed. |
| 3 — Design | Public home/catalog, restrained navy/teal design, consistent branding, readable themes, keyboard focus and collapsible mobile tutor. | Twelve real Edge page/viewport checks passed, including theme and mobile-panel behavior. |
| 4 — Curriculum | Fifteen original Python lessons, prerequisites, examples, diagrams and thirty server-graded checks; fifteen linked coding tasks. | Strict schema/reference validation passed; final example/reference-solution tests are reported in the final test run. |
| 5 — Mastery | User-scoped bounded evidence, distinct quiz/coding sources, missed-concept feedback and fourteen-day review. Reading never counts as mastery. | Thirty-six isolated mastery tests; practice and API integration tests. |
| 6 — AI quality | Selected-lesson grounding, scoped persistent chat, structured interview rubrics, persisted sessions and a twelve-case benchmark. | Mocked tutoring/interview/resume tests; benchmark is deterministic contract testing, not a live-model consistency study. |
| 7 — Security | Validated JWTs, single-use hashed reset tokens, reset revocation, secure production cookies, origin checks, rate limits, sanitized Markdown and remote-only code execution. | Authentication, isolation, hostile-response and execution-boundary tests. |
| 8 — Verification | Backend/API/frontend tests, CI, optional live-service diagnostics and real browser smoke tooling. | Final local run: 325 tests and 381 subtests; 35 Node behavior tests. |
| Contributor cleanup | Archived 95 historical root scripts under scripts/legacy; kept their contents for reference and warned against execution. Added contributor, architecture, recovery and deployment guidance. | Diff/secret-pattern checks before commit. |

## Data safety

Existing Atlas inspection found 10 users, 10 domains, 71 topics and 41 progress records. These were read-only checks, not exports. No historical seed, collection replacement, index application or production curriculum migration was performed.

The authored curriculum and practice tasks are served directly from version-controlled files when their slugs are absent from MongoDB. Database documents retain priority. New mastery/interview records are written lazily by authenticated workflows. No deployment migration is required to browse the new lessons. The insert-only importer defaults to dry-run; any later import needs a verified backup, an exclusive maintenance window and an external recovery receipt. See database-recovery.md and curriculum.md.

## External configuration still required

- Local Groq credentials work; set the valid key separately in the existing Render service. Local .env changes are never pushed.
- Brevo's active API key was confirmed, but API requests returned 401 due to blocked source IPs. Authorize only recognized development and Render outbound addresses. SMTP_FROM_EMAIL must be a verified sender. Delivery to the owner's authorized mailbox has not yet been demonstrated.
- Free Render requires HTTPS transactional email rather than its blocked SMTP ports. The Brevo/Resend implementation is tested with mocked responses; provider acceptance is not proof of inbox delivery.
- Configure a trusted HTTPS PISTON_EXECUTE_URL and any required PISTON_API_KEY. No public endpoint is silently assumed. Until configured, execution returns an explicit unavailable response rather than running code on the app server.
- Set production APP_URL, RESET_PASSWORD_BASE_URL and ALLOWED_ORIGINS to the real HTTPS deployment origin, or use the Render external URL defaults. Review docs/deployment.md.

## Honest validation boundaries

Local isolated tests use Python 3.13 with updated dependencies. CI targets Python 3.11, matching the deployed runtime family, but its remote result must be checked after push. No automatic Render deployment, Render logs or deployed authenticated workflow is implied by a successful Git push.

Rate limiting is per-process and requires a shared store for multi-worker enforcement. Refresh tokens are not backed by a rotating replay-detection session store. Browser access tokens remain susceptible to any future same-origin XSS. Reset mail uses in-process background delivery, not a durable queue. The Motor driver is retained for compatibility; a separately tested migration to PyMongo's async API remains future work.

## Resume next session

## Recovery from the interrupted session

The local source survived the usage limit. Restricted pytest discovery to tests/ to avoid collecting an operational helper with the same basename. Restored scoped tutor history in the UI and fixed legacy quiz identity and normalized coding-source identity. Added the missing curriculum guide. All fifteen lessons' trusted worked examples and all fifteen tasks' reference outputs are checked offline.

Replaced commercial publisher/companion cards with actual legal open resources, corrected the Algorithms PDF filename, replaced a misleading HTTP-200 security-error PDF destination, updated Eloquent JavaScript's edition, and verified all twelve library destinations. The link checker validates PDF signatures, chapter fragments and readable content without storing books. Reset-test mailboxes are now private environment configuration rather than hardcoded personal data.

## Resume next session

1. Check git status, recent commits, CI and the existing Render deployment before making changes.
2. Resolve Brevo authorized IPs, verify sender and send exactly one authorized reset test; never log its link or change the owner's password as part of testing.
3. Configure and live-test the trusted remote sandbox using the authored reference tasks.
4. Validate the production homepage, public curriculum, readiness and authenticated tutoring after deployment; inspect Render logs through an authorized connection.
5. Run a live interview grading benchmark with explicitly approved cost; expand other domains after reviewing the flagship curriculum.
6. Consider shared rate limits, refresh replay detection and a durable email queue as follow-up security work.
