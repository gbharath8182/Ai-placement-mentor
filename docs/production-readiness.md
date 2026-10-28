# Product quality and launch readiness

The application is a working placement-preparation product, not a certified production platform. A passing test suite does not establish availability, scalability, security certification or educational efficacy. Use this checklist as a release gate rather than describing every deployed revision as production-ready.

## Product experience

- The homepage demonstrates study, spoken interview and resume workflows with clearly labeled examples. It does not invent testimonials, success rates, placement guarantees or personal activity.
- The dashboard prioritizes unfinished lessons and reassessment over a catalog of interchangeable cards. `/workspace/overview` derives its queue from the authenticated learner's existing progress and mastery evidence; it does not write or migrate data.
- Review suggestions reuse the actual mastery policy. They are not a new AI score, and reading does not establish mastery. Completed topics and fresh mastery are displayed separately.
- The overview reads at most 100 recent progress records and 100 recent mastery records, with an extra sentinel record to disclose truncation. Counts are for that window, not lifetime totals. Removed or malformed lessons are disclosed and not linked.
- Search is available from the workspace header and Ctrl/Cmd+K. Tools work locally; lesson search uses bounded, escaped queries and metadata-only responses. Built-in-only results are explicitly labeled during a live catalog outage. The modal supports keyboard navigation, Escape and focus restoration.
- Empty, loading, unavailable and offline states are distinct. Missing runner configuration is not shown as a working execution service. Configuration flags are not live provider health checks.
- Transient token-refresh failures preserve local sign-in and fail the request for retry. An explicit invalid-credential response clears sign-in. Refresh is single-flight, time-bounded and cannot restore browser tokens after a local logout. This is not server-side refresh-token replay protection; signing out offline cannot guarantee the server cookie was cleared.

## Changes that do not require a database migration

This release adds read-only overview and catalog-search endpoints. It reads the existing `topics`, `user_progress` and `user_mastery` collections in the configured database. No seed scripts, content replacements, user edits, migrations or production index changes are needed. Index review should be based on measured query plans and a separately approved change, not an automatic startup migration.

## Release checks

1. Both GitHub Actions jobs must pass: `test` and `product-browser`. The latter uses synthetic users and an isolated local fixture server, not real credentials, devices, MongoDB, email or AI services.
2. Deploy the exact reviewed commit to staging or the existing Render service. Verify the commit in Render, not just the health endpoint. Local `.env` is never uploaded by Git.
3. Check `/health/live` and `/health/ready`. Readiness proves database connectivity only, not email delivery or AI/runner availability.
4. With a dedicated test account, verify login, reload, session refresh, a lesson check, dashboard continuation/review, transcript submission, PDF links and logout. Avoid unsolicited reset emails or testing on somebody else's account.
5. Check wide and narrow layouts, both themes, keyboard-only navigation, 200% zoom, reduced motion, no results, provider failure, slow network, denied microphone permission and interrupted recording. Automated checks do not replace screen-reader and real-device review.
6. Keep the previous known-good commit available for rollback. A UI rollout must not run destructive database setup or remove existing content.

## Operational gates before a broader launch

| Priority | Gate | Current limitation / completion evidence |
| --- | --- | --- |
| P0 | Predictable availability | The existing free Render service can sleep after inactivity. The owner must approve an always-on hosting budget or explicitly accept cold starts. Do not mask this with a fake “live” badge. |
| P0 | Remote code execution | An approved, isolated runner and quotas are still required. Never execute untrusted code in the web process. Verify resource limits and hostile-code isolation before enabling it. |
| P0 | Account/session hardening | Access and refresh tokens remain browser-readable; refresh tokens lack a persisted rotating session/replay store. Plan a separately tested cookie/session migration, revocation and logout-all-devices flow before high-trust use. |
| P0 | Backups and recovery | Confirm the Atlas backup policy, restore into a separate database and record recovery time. A local content export is not a complete recurring backup strategy. |
| P0 | Private vulnerability channel | Repository owner/admin must enable private reporting and enforce reviewed branch rules. A policy file alone does not enforce permissions. |
| P1 | Durable reset delivery | Reset email runs in process. Introduce a reviewed durable outbox/worker with bounded retry, deduplication and delivery visibility before promising reliable delivery through restarts. |
| P1 | Shared quotas | Rate limits are per process. Multi-worker deployment needs shared enforcement, per-user/provider budget controls and concurrency limits. |
| P1 | Monitoring and incidents | Completed API responses carry a generated request ID; safe structured log fields include route template, method, status and duration. Add external availability alerts, error-rate/latency dashboards, provider-cost alerts and an incident owner. Do not log tokens, raw URLs/query strings, transcripts or resumes. |
| P1 | Capacity evidence | Load-test a staging environment at a declared concurrency target. Record p50/p95 latency, error rate, saturation and recovery with realistic AI latency, without spending uncontrolled provider quotas. No such benchmark is claimed here. |
| P1 | Privacy and retention | Publish a reviewed retention/deletion policy covering MongoDB, backups and speech/AI providers. Session deletion in the app does not establish deletion from provider logs or backups. |
| P2 | Dependency lifecycle | Review driver/runtime support and pin migrations deliberately. Existing Motor and Python deployment choices were not silently replaced in this UI release. |

## What to build next

Prioritize usefulness over more pages:

1. **A configurable preparation plan:** target role and interview date, a realistic weekly workload, clear prerequisites and explicit rescheduling. Validate recommendations against real learner outcomes rather than calling them optimized.
2. **Interview practice history:** compare the learner's own prior answers and specific improvement tasks, without gaze, emotion, accent or personality scores. Use human-reviewed rubrics before claiming score comparability across sessions.
3. **A project evidence portfolio:** attach factual project notes and permitted repository links, reuse approved facts in interviews and resumes, and distinguish user claims from independently verified evidence.
4. **Resume revision history:** explicit drafts, compare changes, restore a prior version and keep edits through interruptions. Avoid collecting more personal data than necessary.
5. **Content quality operations:** scheduled review of resource links, reporting broken content, editorial ownership and tested lesson prerequisites. A large catalog is not a substitute for trustworthy explanations.

## References

- [Render free service limits](https://render.com/docs/free): free web services spin down after inactivity and have operational constraints.
- [W3C modal dialog guidance](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/): keyboard focus, accessible labeling and dismissal behavior.
- [Deployment guide](deployment.md), [repository protections](repository-protection.md), [security policy](../SECURITY.md), [database recovery](database-recovery.md).
