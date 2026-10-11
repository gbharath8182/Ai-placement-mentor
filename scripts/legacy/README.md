# Historical scripts — archive only

> **Do NOT run these scripts against production. Do NOT import them into the application or a test suite.** This directory preserves historical work for maintainers; it is not a supported toolchain, bootstrap procedure, or ordered migration sequence.

The tracked Python and PowerShell scripts formerly in the repository root, plus `dsa_template_dump.json` and `seed_history.txt`, were relocated here. Application files, deployment requirements, and backend/frontend code remain in their original locations. Historical script logic was not modernized or validated for execution during this cleanup.

## What is here

| File family | Historical purpose | Important risk |
| --- | --- | --- |
| `add_*.py`, `insert_sde.py` | Add curriculum cards, topics, domain details, and practice problems. | Writes, upserts, and in some cases delete-then-reinsert operations; not a safe incremental importer. |
| `seed_*.py` | Populate older curriculum schemas or richer domain/topic content. | Some delete whole domain topic sets before insertion; rerunning can replace curated material. |
| `deepen_*.py`, `expand_webdev_existing.py` | Enrich previously populated topic content. | Assumes historical slugs, schemas, and database contents; overwrites selected records. |
| `convert_domain_topics.py`, `dedupe_topics.py`, `final_migration.py`, `migrate_*.py` | Reshape, deduplicate, or copy database records. | Deletes or updates data; `migrate_users.py` includes user, progress, activity, chat, and streak collections. Labels such as `local` and `atlas` do not verify the actual target. |
| `fix_intro_ml_*.py`, `fix_stray_emoji.py` | Repair selected content and practice records. | Mutates database documents based on historical assumptions. |
| `check_*.py`, `verify_*.py`, `full_audit.py` | Inspect specific collections or content shapes. | Usually connects directly to MongoDB and prints records; these are not maintained automated tests or production diagnostics. Review each file before considering reuse. |
| `dump_dsa_template.py`, `show_one_topic.py`, `show_remaining_shapes.py` | Export or inspect a historical DSA detail shape. | The dump helper writes a file; consumers assume a working-directory-relative JSON path. |
| `append_mi_css.py`, `patch_*.py`, `fix_submodel.py`, `apply_*.ps1`, `fix_domain_query.ps1` | One-off edits to mock interview, resume, roadmap, styles, and backend source. | Writes to application files using exact text/line-ending anchors or machine-specific paths; can overwrite or corrupt newer code. `v2` variants are not a supported patch ordering. |
| `dsa_template_dump.json` | Historical DSA domain-details export. | Reference shape only: not a canonical curriculum dataset, complete backup, or import contract. |
| `seed_history.txt` | Captured Git history/diffs about old seed behavior and changes. | Contains removed code, including destructive seeding. Read as history, never as instructions to replay. |

`apply_mi_css_fix.ps1` is an empty historical placeholder, retained rather than silently removed.

## Why relocation does not make these runnable

- Some files connect to a hard-coded MongoDB URI; others load `backend.config.settings`, which may read environment configuration. Neither pattern guarantees a disposable target.
- Many scripts run their work at module scope or call `asyncio.run(...)` unconditionally. Importing them can perform writes immediately.
- Source patchers reference paths such as `backend/main.py` and `frontend/roadmap.html` relative to the current working directory. Others embed absolute Windows paths and `sys.path` modifications from a particular machine.
- `dump_dsa_template.py` still writes `dsa_template_dump.json` relative to the working directory; the two `show_*` consumers still read that same relative name. Moving the files together does not resolve this dependency automatically.
- Paths, imports, schema assumptions, execution order, connection settings, idempotency, and failure recovery have **not** been repaired or certified. Changing directory or running from the repository root is not a safety fix.

## Maintainer investigation

Read the source and Git history without executing it. If historical content is needed, extract and review the useful data or logic into a new maintained tool under `scripts/`, with validated inputs and explicit targets. Any experimental reproduction requires a disposable checkout and database, a full review of side effects and path resolution, and no production credentials. Database-changing workflows need a recovery plan and preview before writes.

See [the maintained tool guide](../README.md) and [contributor guidance](../../CONTRIBUTING.md) for the supported direction. This cleanup did not execute archived scripts or modify the deprecated backend seed file.
