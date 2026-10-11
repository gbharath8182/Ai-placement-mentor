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

## Secret-pattern checks

`python scripts/check_secrets.py --staged` scans indexed contents of staged additions/modifications before a commit. `python scripts/check_secrets.py` scans all tracked working-tree files and is the CI command after checkout. Neither default scanning nor an empty staged scan validates untracked new files. Findings report filenames rather than credential values; this is a basic guard, not a replacement for a dedicated scanner or key rotation. Any intentional fixture allowance must be narrow and reviewed.

## Historical archive

[`legacy/README.md`](legacy/README.md) explains the archived file families and their risks. **Do NOT run archived scripts against production.** They are reference material, not supported imports, migrations, smoke checks, or a reproducible setup pipeline. Their old relative paths, absolute paths, and database assumptions have intentionally not been repaired.
