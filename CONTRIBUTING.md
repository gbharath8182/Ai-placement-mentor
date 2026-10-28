# Contributing

## Permission and review

Read [LICENSE.md](LICENSE.md) before reusing code. This is a public, source-available project with prior-permission requirements, not an open-source license. GitHub's rights to view/fork and third-party licenses remain unchanged.

Before starting a substantial contribution, open an issue describing the proposed work and obtain maintainer approval. Submit changes from your own fork through a pull request; acceptance, deployment and repository access remain maintainer decisions. Do not force-push to shared branches, alter access settings or delete content without explicit authorization. Public visibility never grants deletion or administrator rights.

Only contribute code and assets you have the right to submit. Identify third-party sources and licenses; do not include another person's name, image, voice or likeness as branding or an endorsement without appropriate permission. Discuss contribution licensing with the maintainer before submission; submitting a patch is not a transfer of another author's copyright. Use [SECURITY.md](SECURITY.md) for vulnerabilities rather than public exploit details. See [repository protection](docs/repository-protection.md) for the distinction between policy files and enforced GitHub settings.

## Find the active code

- `backend/`: FastAPI application, request models, authentication, and API routes.
- `frontend/`: HTML pages, shared CSS, and vanilla JavaScript served by FastAPI.
- `scripts/`: maintained operational tools; start with [the tool guide](scripts/README.md).
- `scripts/legacy/`: historical scripts and reference artifacts, **not supported tools**.
- `docs/architecture.md`: [current architecture and boundaries](docs/architecture.md).
- `requirements.txt`, `runtime.txt`, and `README.md`: dependency pins, deployment Python version, and setup overview.

Keep new utilities out of the repository root. Do not restore archived scripts to the active workflow or treat them as a migration sequence.

## Local development

1. Read `README.md` and any applicable `AGENTS.md` instructions. Use the Python version pinned in `runtime.txt` and a virtual environment.
2. Install dependencies with `python -m pip install -r requirements.txt` from the repository root.
3. Configure your own development environment with a separate, disposable MongoDB database and a development-only JWT secret. Check the database client's TLS requirements before choosing a local MongoDB instance.
4. Start the development app from the repository root with `python -m uvicorn backend.main:app --reload --port 8000`. Static paths currently depend on this working directory.

Never use production database credentials for local development. AI calls can use paid external services when configured; use mocked responses or explicitly approved test credentials for validation. Missing AI credentials are not a guarantee of demonstration mode. SMTP and HTTPS email-provider testing must use controlled mailboxes, not real users.

## Data and operational safety

**Do NOT run anything in `scripts/legacy/` against production.** Some scripts delete or replace curriculum, migrate user data, or overwrite application source immediately when executed or imported. Names such as `check`, `verify`, and `seed` are not safety guarantees. Read the [archive warning](scripts/legacy/README.md) before investigating historical behavior.

The deprecated backend seed file is not a bootstrap procedure either. Ask a maintainer for the supported curriculum import workflow before populating a database. New maintained tools belong directly in `scripts/` and must document their target, read/write scope, dry-run behavior, explicit write approval, and failure handling. Never substitute archived scripts for a missing maintained tool.

Do not commit `.env` files, secret-bearing backups, credentials, database exports containing personal data, or test account tokens. Do not modify or delete another contributor's local environment or backups. Check that staged files contain no secrets, even when ignore rules are present.

After staging your intended changes, run `python scripts/check_secrets.py --staged` to inspect their indexed contents. CI uses `python scripts/check_secrets.py` without `--staged` to scan all tracked checkout files. The default scan does not include untracked files; a clean pre-stage result is not validation of newly created files. This basic pattern check does not replace credential rotation or a dedicated secret scanner. Intentional non-secret fixtures require a narrowly scoped, reviewed allowance; do not weaken scanning broadly or remove a redaction regression test to make it pass.

## Automated checks

Use Python 3.11 with an isolated environment and `python -m pip install -r requirements-dev.txt`. Run `python -m pytest tests` to collect both pytest fixtures/functions and unittest cases, then `node --test tests/frontend-smoke.test.js`. No npm packages or browser installation are required. CI also syntax-checks each `frontend/js/*.js` file with `node --check`.

Frontend smoke tests execute the actual auth, AI sidebar, and resume scripts in isolated Node VM contexts with mocked storage, network, streams, and a minimal DOM. They validate behavior and rendering sinks, not browser layout or the internals of third-party sanitizer libraries. They require no production credentials or live services. Do not treat results from a different local Python/dependency stack as validation of the pinned CI environment.

## Changes and validation

- Keep changes focused; coordinate ownership when other contributors or agents are editing concurrently. Do not overwrite unrelated changes or generated artifacts.
- For backend changes, check affected request/response models, authentication requirements, and MongoDB collection usage. For frontend changes, check the corresponding page and JavaScript API calls together.
- Validate changed behavior against an isolated development app and database. Do not import archived scripts for test discovery or execute them as checks.
- Use the maintained live smoke tool only after reviewing its documented operations and selecting an approved test target. A live smoke check is not automatically read-only; authentication, progress, activity, or AI requests can have side effects.
- Document validation performed, what was not tested, and any external-service requirements. Never claim live checks passed when only source inspection was performed.
- Include architecture or tooling documentation changes when public behavior, configuration, or operational workflows change. Review the diff before proposing a pull request; exclude unrelated work.
