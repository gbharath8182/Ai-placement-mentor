# V2 checkpoint — 12 October 2026

## Implemented increment

| Phase | Root cause and implementation | Verification |
| --- | --- | --- |
| 0 — Investigation | Audited FastAPI, MongoDB schemas, vanilla frontend and deployment assumptions; preserved the original stack and records. | Intended remote verified; production collection counts read only. |
| 1 — Groq | Replaced duplicated deprecated-model clients with configurable 20b/120b routing, bounded retries, structured schemas and safe SSE errors. | Real account model access, both completions and streaming passed; mocked failures and fallback passed. |
| 2 — Reliability | Bounded MongoDB operations, verified TLS, reconnectable lifecycle, liveness/readiness and curated content fallback. | Database recovery tests and real Atlas ping passed. |
| 3 — Design | Public home/catalog plus a shared text-led premium workspace sidebar, restrained surfaces, readable themes, keyboard focus and collapsible mobile navigation/tutor. | Thirty real Edge desktop/mobile workspace and authentication checks passed with isolated API fixtures. |
| 4 — Curriculum | Fifteen original Python lessons, prerequisites, examples, diagrams and thirty server-graded checks; fifteen linked coding tasks. | Strict schema/reference validation passed; final example/reference-solution tests are reported in the final test run. |
| 5 — Mastery | User-scoped bounded evidence, distinct quiz/coding sources, missed-concept feedback and fourteen-day review. Reading never counts as mastery. | Thirty-six isolated mastery tests; practice and API integration tests. |
| 6 — AI quality | Selected-lesson grounding, scoped persistent chat, structured interview rubrics, persisted sessions and a twelve-case benchmark. | Mocked tutoring/interview/resume tests; benchmark is deterministic contract testing, not a live-model consistency study. |
| 7 — Security | Validated JWTs, single-use hashed reset tokens, reset revocation, secure production cookies, origin checks, rate limits, sanitized Markdown and remote-only code execution. | Authentication, isolation, hostile-response and execution-boundary tests. |
| 8 — Verification | Backend/API/frontend tests, CI, optional live-service diagnostics and real browser smoke tooling. | Final local run: 359 tests and 381 subtests; 38 Node behavior tests; 30 workspace browser checks. |
| Contributor cleanup | Archived 95 historical root scripts under scripts/legacy; kept their contents for reference and warned against execution. Added contributor, architecture, recovery and deployment guidance. | Diff/secret-pattern checks before commit. |

## Data safety

Initial Atlas inspection found 10 users, 10 domains, 71 topics and 41 progress records. On 12 October, the owner explicitly requested synchronizing the new content to the same cluster. The backed-up insert-only import added 15 topics, 15 practice tasks and one domain, preserving every existing content document. Current totals: 86 topics, 109 practice tasks and 11 domains. Users remain 10 and progress records remain 41. No historical seed, collection replacement, index application or updates/deletes were performed.

All three affected content collections were exported locally as canonical Extended JSON, hashed and round-trip verified before writes. The generated backup is in ignored backups/; a durable recovery receipt is outside the repository. Neither was committed. Six isolated tests cover conflict rejection, preservation, BSON round trips, idempotency and partial-failure journaling. A subsequent read-only preview skipped all 31 authored documents with zero inserts or conflicts.

The authored curriculum and practice tasks still support file fallback when their slugs are absent from MongoDB. Database documents retain priority. New mastery/interview records are written lazily by authenticated workflows. Future content changes must use a reviewed insert-only preview or a separately approved migration; conflicts are not overwritten. See database-recovery.md and curriculum.md.

## External configuration still required

- Local Groq credentials work; set the valid key separately in the existing Render service. Local .env changes are never pushed.
- The owner configured Brevo on Render, verified the sender and authorized the actual Render outbound ranges while keeping API IP blocking enabled. The owner confirmed the subsequent password-reset attempt completed. Local development IPs require separate authorization; do not disable IP protection to make local diagnostics pass.
- Free Render uses HTTPS transactional email rather than its blocked SMTP ports. Provider acceptance alone is not proof of inbox delivery; the production reset confirmation here was supplied by the owner.
- Configure a trusted HTTPS PISTON_EXECUTE_URL and any required PISTON_API_KEY. No public endpoint is silently assumed. Until configured, execution returns an explicit unavailable response rather than running code on the app server.
- Set production APP_URL, RESET_PASSWORD_BASE_URL and ALLOWED_ORIGINS to the real HTTPS deployment origin, or use the Render external URL defaults. Review docs/deployment.md.

## Honest validation boundaries

Local isolated tests use Python 3.13 with updated dependencies. GitHub CI passed on Python 3.11 for commit 8822630. Follow-up changes need their own CI result. The owner confirmed Render revision 6d1947b was Live, and public readiness returned 200 with API version 2.0.0. The premium workspace redesign is validated locally; its production deployment requires a separate confirmation.

Rate limiting is per-process and requires a shared store for multi-worker enforcement. Refresh tokens are not backed by a rotating replay-detection session store. Browser access tokens remain susceptible to any future same-origin XSS. Reset mail uses in-process background delivery, not a durable queue. The Motor driver is retained for compatibility; a separately tested migration to PyMongo's async API remains future work.

## Recovery from the interrupted session

The local source survived the usage limit. Restricted pytest discovery to tests/ to avoid collecting an operational helper with the same basename. Restored scoped tutor history in the UI and fixed legacy quiz identity and normalized coding-source identity. Added the missing curriculum guide. All fifteen lessons' trusted worked examples and all fifteen tasks' reference outputs are checked offline.

Replaced commercial publisher/companion cards with actual legal open resources, corrected the Algorithms PDF filename, replaced a misleading HTTP-200 security-error PDF destination, updated Eloquent JavaScript's edition, and verified all twelve library destinations. The link checker validates PDF signatures, chapter fragments and readable content without storing books. Reset-test mailboxes are now private environment configuration rather than hardcoded personal data.

The public README now describes the product rather than internal release status, and includes Mermaid architecture and learning-loop diagrams. Internal progress remains in this checkpoint.

## Premium workspace redesign

The owner requested a high-priority redesign of authenticated pages after reviewing the live site. Replaced repeated horizontal icon-heavy navigation with a shared text-led left sidebar, active page state, account/appearance controls and a mobile drawer with Escape/focus behavior. Removed decorative SVG domain/stat cards rather than merely recoloring them. Added quiet matte/olive workspace surfaces, clearer density/spacing and consistent forms, charts and content panels. The public homepage remains unchanged; the authenticated catalog joins the workspace shell. Login/signup/recovery screens use an editorial split layout without the old logo illustration.

Dashboard cards now use native buttons and textContent; topic entries use encoded native links. Search filters real loaded domains, errors have retry controls, unavailable statistics remain unclaimed and singular streak/lesson labels are correct. Thirty real desktop/mobile page checks passed using isolated API fixtures. Node rendering regressions passed; final suite counts are reported with this release.

The deployed revision 6d1947b was confirmed by the owner in Render and public API readiness returned 200 with version 2.0.0. Brevo's verified sender was confirmed, and the owner authorized the two actual Render outbound ranges while keeping API IP blocking enabled. The owner subsequently confirmed the new reset attempt completed; no credentials or reset links were shared or committed.

## Resume studio PDF correction

Replaced the resume's CDN-dependent Markdown preview and .md download with server-parsed, bounded document blocks and an authenticated ReportLab PDF export. The frontend renders text through native DOM nodes, uses a white document surface in both themes, and presents grouped form sections. PDF text is selectable and supplied profile/project destinations are encoded and clickable. GitHub/LinkedIn fields reject app URLs and lookalike domains; the application preserves original contact facts, suppresses invented active links, never fetches user URLs, and rejects unformatted or oversized writer output rather than displaying a fake complete document. Export does not rerun AI or write to MongoDB.

Regressions cover PDF annotations, pagination, escaping, authentication, response type, download filenames, safe browser links, missing renderer libraries and malformed AI output. Thirty workspace checks and two full resume browser flows passed with synthetic fixtures. The rendered PDF and desktop/mobile previews were inspected visually. Latest local suites: 385 Python tests with 381 subtests and 43 Node tests. Production requires deploying this correction separately from c2144b0.

The shared shell now reads the existing local account safely even when deferred auth helpers have not loaded yet, preserving its initialization before older page handlers need shell control IDs. The reference library loads the auth helper for working account/sign-out controls.

## Resume next session

1. Check git status, recent commits, CI and the existing Render deployment before making changes.
2. Confirm the premium workspace revision is deployed on Render; repeat reset delivery only if needed and explicitly authorized, never logging its link or changing the owner's password as part of testing.
3. Configure and live-test the trusted remote sandbox using the authored reference tasks.
4. Validate the production homepage, public curriculum, readiness and authenticated tutoring after deployment; inspect Render logs through an authorized connection.
5. Run a live interview grading benchmark with explicitly approved cost; expand other domains after reviewing the flagship curriculum.
6. Consider shared rate limits, refresh replay detection and a durable email queue as follow-up security work.
