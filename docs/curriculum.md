# Authored Python curriculum

`curriculum/python-foundations.json` contains fifteen original lessons in a single ordered `python-foundations` domain. Each lesson supplies objectives, earlier-lesson prerequisites, substantive explanations, runnable worked examples, diagrams, common mistakes, progressive practice, interview questions and two knowledge checks. Official Python documentation links provide factual references, not copied lesson text.

`backend/curriculum.py` strictly validates JSON keys, block shapes, integer versions, unique IDs, contiguous order, resource URL safety and prerequisite references. `load_curriculum()` returns independent dictionaries and never runs example code. `curriculum/python-practice.json` contains fifteen linked tasks, stable SHA-256-derived identifiers, starter code, stored test cases and trusted reference solutions. Runtime responses strip reference solutions and quiz answers; the public source repository is not a hidden-exam bank.

## How the application reads content

Existing MongoDB documents have priority. Missing authored slugs fall back to these validated files, making the new public lessons available without importing or replacing production content. Personal checks, tutoring, interview sessions and mastery still require the database. During database outages, public authored lessons remain readable; private actions fail safely rather than fabricating success.

Submission comparison normalizes surrounding whitespace and CRLF, not arbitrary JSON formatting. Follow each task's documented compact JSON/key-order contract. Submitted code runs only at a configured trusted Piston-compatible HTTPS service, never on the application host. The reference solution is executed only in isolated tests of trusted version-controlled material.

## Review and tests

Run `python -m pytest tests/test_curriculum.py` in an isolated environment. Tests validate structure, depth, all thirty reviewed answer indices, all worked-example stdout, all authored reference solutions against their test cases and importer dry-run/recovery behavior. Tests of trusted examples use fresh temporary directories and a timeout. This is not a safe facility for executing learner submissions.

Content changes need human technical review in addition to tests. Check explanations, distractors, language-version assumptions, examples, output formatting, prerequisite order, accessibility of diagrams and linked official references.

## Optional MongoDB import

Browsing the catalog needs no migration. For a separately approved insert-only import, first follow `database-recovery.md`, verify a backup on a disposable restore target and establish an exclusive maintenance window.

```text
python -m scripts.import_curriculum --dry-run --database YOUR_EXPECTED_DATABASE
```

Dry-run reads candidate slugs without writing. Identical documents are skipped; conflicts stop the operation instead of overwriting. `--apply` additionally requires the expected database, an external new recovery receipt and `--exclusive-writes-confirmed`. Do not put import commands in Render startup/build scripts. A partial failure leaves a journal; inspect it before retrying. No automatic destructive rollback is provided.

That importer covers domain/topic documents, not practice documents, private reference solutions or user data. For the separate public-practice synchronization workflow, see below. Never replay `scripts/legacy/` against production.

For synchronizing all three authored content collections, `scripts.sync_curriculum` provides a separate backed-up insert-only workflow. It previews domains, topics and public practice documents, binds application to a reviewed target fingerprint, excludes reference solutions and verifies existing-document preservation after inserts. See [tool operations](../scripts/README.md#backed-up-content-synchronization). The owner-authorized 12 October synchronization is recorded in the maintainer checkpoint; it does not change the safety requirements for future imports.
