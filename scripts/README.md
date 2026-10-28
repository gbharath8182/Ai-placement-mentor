# Repository tools

This directory separates maintained tools from one-off historical scripts. The running application is in `backend/` and `frontend/`; operational helpers are not application startup hooks.

## Maintained tool roles

The following tools are maintained separately from the archive. Review their implementation and `--help` before selecting a live target. Commands below assume the repository root and deliberately do not execute a live check by themselves.

| Workflow | Purpose | Required safety boundary |
| --- | --- | --- |
| `scripts/import_curriculum.py` | Validate and insert reviewed domains/topics from versioned curriculum JSON. | Read-only preview by default; insert missing slugs, skip identical content, and reject conflicts. Applying requires an expected database name, an exclusive-write confirmation, and a new recovery receipt outside the repository. No blanket wipes, updates, or deletes. |
| `scripts/live_smoke.py` | Explicitly selected AI, database, or deployment checks. | `--database` reads a ping, counts, and sampled schema shapes; `--deployment` performs page/API GETs; `--ai` makes minimal real model/completion/streaming requests and may incur costs. It does not deploy or write MongoDB. |

```text
python -m scripts.import_curriculum --help
python -m scripts.live_smoke --help
```

The importer loads `MONGO_URI` from application configuration; `--database` checks the database name but does not replace the URI or verify the host. After confirming the configured target is disposable, use `python -m scripts.import_curriculum --dry-run --database YOUR_TEST_DATABASE` for a read-only preview. Applying additionally requires `--apply`, `--receipt`, and `--exclusive-writes-confirmed`; coordinate with a maintainer rather than copying a production write command. A partially applied import is not automatically rolled back: inspect its journal before any retry or recovery.

Use `python -m scripts.live_smoke --database`, `--ai`, or `--deployment https://YOUR_APPROVED_TEST_HOST` only after approving that check and target. AI/database checks use environment configuration, independently of the deployment URL. Do not use archived scripts to extend these workflows.

## Before using a maintained tool

1. Review its implementation, documented configuration, target, and read/write scope. Run from the repository root unless the tool explicitly documents otherwise.
2. Use an isolated development database or an approved staging application. Do not inherit an unknown production target from shell variables or a local environment file.
3. Preview curriculum changes before requesting a write. Verify the database and affected collections, input validation, duplicate/upsert policy, and recovery plan.
4. For live smoke checks, review which requests mutate state and whether Groq or SMTP will be contacted. Avoid real accounts and redact credentials from reports.
5. Report failures accurately. Do not repeatedly retry a partially applied import without understanding its idempotency and recovery behavior.

Add new supported utilities directly here with clear usage and safety documentation. Keep secrets and private exports out of the repository. Scripts must not execute database writes merely on import or while displaying help.

## Backed-up content synchronization

`python -m scripts.sync_curriculum` previews missing authored topics, tasks and domains on the configured MongoDB target. It prints a credential-free target fingerprint and action counts. Existing differing or duplicate content is a conflict, not an invitation to overwrite it.

Applying requires the reviewed `--expected-target`, `--apply` and `--exclusive-writes-confirmed`. It exports all affected content collections under ignored backups/, verifies canonical BSON/JSON round trips and unchanged snapshots, then inserts only missing documents with a flushed recovery journal outside the repository. Users, progress and private histories are never written. Reference solutions are excluded from persisted practice documents. Partial errors do not trigger automatic deletion; inspect the receipt and backup before any retry. The backup covers content only, not the entire Atlas database, and is not a substitute for a full disaster-recovery backup.

## Resource and email verification

`python -m scripts.check_resources` makes bounded, read-only HTTPS requests to the twelve free-library destinations. It checks status, readable content type, PDF signatures and chapter anchors without storing books. A passing result is a point-in-time check, not a guarantee that an external host will never change.

`python -m scripts.live_smoke --email-config` checks Brevo account and verified-sender access without sending mail. If it reports `ip_not_authorized`, authorize only recognized source IPs in Brevo before retrying.

`python -m scripts.test_reset_delivery --to YOUR_CONTROLLED_MAILBOX --confirm-send --base-url YOUR_TRUSTED_APP_ORIGIN` is an explicitly mutating test: it requests exactly one real reset email for an existing account and stores that account's reset digest. First set the private `RESET_TEST_RECIPIENT` environment variable to the same explicitly authorized mailbox. Without that match and confirmation it fails closed. It does not reset the password, disclose the link or prove inbox delivery; check the mailbox yourself after provider acceptance. Never put a personal mailbox in source code or run the helper against another user's account.

## Secret-pattern checks

`python scripts/check_secrets.py --staged` scans indexed contents of staged additions/modifications before a commit. `python scripts/check_secrets.py` scans all tracked working-tree files and is the CI command after checkout. Neither default scanning nor an empty staged scan validates untracked new files. Findings report filenames rather than credential values; this is a basic guard, not a replacement for a dedicated scanner or key rotation. Any intentional fixture allowance must be narrow and reviewed.

## Workspace browser verification

`node scripts/workspace_smoke.cjs PATH_TO_PLAYWRIGHT LOCAL_APP_URL` checks eleven authenticated workspace pages and four authentication/recovery pages at desktop/mobile sizes. It uses isolated browser contexts, a fake account and intercepted API fixtures; it never writes to a real account. Microsoft Edge and Playwright must be available locally. Screenshots stay in ignored artifacts/workspace/. Checks cover the left navigation, mobile opening/Escape/focus behavior, theme switching, safe domain-card navigation, search, preserved forms and horizontal overflow.

Node unit tests also cover safe domain-card and topic-link rendering; pytest checks shared-shell inclusion, fallback navigation, preserved dashboard control IDs and an unchanged public homepage. Browser fixtures are not a live AI, email or sandbox execution test.

## Resume preview and PDF verification

Run `python -m tests.resume_preview` from the repository root to start a fixture-only service bound to 127.0.0.1:8881. It uses synthetic candidate details, overridden authentication and mocked AI; it never connects to MongoDB or a live AI provider. Do not expose it publicly or use it as the application server.

In a separate terminal, run `node scripts/resume_smoke.cjs PATH_TO_PLAYWRIGHT http://127.0.0.1:8881`. Desktop/mobile checks generate a structured preview without CDN libraries, validate profile destinations and download real PDFs through the authenticated export handler. PDF and screenshot artifacts stay in ignored artifacts/resume/. Stop the fixture server when finished. Python regressions additionally verify selectable PDF text, link annotations, pagination, escaped input, authentication and export limits.

## Spoken interview verification

`python -m tests.spoken_preview` starts an isolated loopback fixture on port 8882 with mocked authentication, AI, audio and in-memory sessions. It must never be exposed publicly or used as the production server. `node scripts/spoken_smoke.cjs PATH_TO_PLAYWRIGHT http://127.0.0.1:8882` uses synthetic Edge camera/microphone devices to exercise consent, recording, transcript retry, follow-ups, feedback, deletion and permission/audio-failure fallback. Screenshots stay in ignored artifacts/spoken/. Stop the fixture server when finished.

`python -m scripts.check_interview_audio --confirm-provider-call` performs one billable synthetic Groq TTS/STT round-trip using server-side configuration. It does not use a real microphone, send candidate details, write to MongoDB or save audio. Run only with an explicitly approved provider/account. See [spoken interview operations](../docs/spoken-interviews.md).

## Historical archive

[`legacy/README.md`](legacy/README.md) explains the archived file families and their risks. **Do NOT run archived scripts against production.** They are reference material, not supported imports, migrations, smoke checks, or a reproducible setup pipeline. Their old relative paths, absolute paths, and database assumptions have intentionally not been repaired.
