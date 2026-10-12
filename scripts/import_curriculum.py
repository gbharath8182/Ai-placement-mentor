"""Read-only preview by default; explicit, journaled, insert-only application."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.curriculum import Curriculum, load_curriculum


class ImportConflict(ValueError):
    pass


def _matches(existing, authored):
    return all(existing.get(key) == value for key, value in authored.items())


def _existing(collection, document):
    found = list(collection.find({"slug": document["slug"]}))
    if not found:
        return "insert"
    if len(found) == 1 and _matches(found[0], document):
        return "skip"
    return "conflict"


def preview_import(database, curriculum):
    """Read only the candidate slugs; never create indexes or change documents."""
    validated = Curriculum.model_validate({"schema_version": 1, **curriculum})
    data = validated.model_dump(mode="json")
    operations = []
    for collection_name in ("topics", "domains"):
        for document in data[collection_name]:
            operations.append({
                "collection": collection_name,
                "slug": document["slug"],
                "action": _existing(database[collection_name], document),
            })
    return {"database": database.name, "mode": "dry-run", "operations": operations}


def import_curriculum(database, curriculum, *, apply=False, receipt_path=None, exclusive_writes=False):
    """Insert missing documents, skip identical ones, and fail closed on conflicts."""
    preview = preview_import(database, curriculum)
    if not apply:
        return preview
    if not exclusive_writes:
        raise ValueError("apply requires an exclusive maintenance window confirmation")
    if any(operation["action"] == "conflict" for operation in preview["operations"]):
        raise ImportConflict("conflicting or duplicate slugs; nothing written")
    if receipt_path is None:
        raise ValueError("apply requires a recovery receipt outside the repository")
    receipt = Path(receipt_path).resolve()
    if receipt.is_relative_to(ROOT):
        raise ValueError("recovery receipt must be outside the repository")
    report = {
        **preview, "mode": "apply", "status": "started",
        "source_sha256": hashlib.sha256(json.dumps(curriculum, sort_keys=True).encode()).hexdigest(),
        "recovery": "Insert-only: no before-images needed. Review recorded IDs before manual removal; no automatic rollback.",
        "insertions": [],
    }
    documents = {
        (collection_name, document["slug"]): document
        for collection_name in ("domains", "topics") for document in curriculum[collection_name]
    }

    with receipt.open("x", encoding="utf-8") as journal:
        def save_report():
            journal.seek(0)
            json.dump(report, journal, indent=2, ensure_ascii=False)
            journal.truncate()
            journal.flush()
            os.fsync(journal.fileno())

        save_report()
        try:
            for operation in preview["operations"]:
                collection_name, slug = operation["collection"], operation["slug"]
                document = documents[collection_name, slug]
                collection = database[collection_name]
                action = _existing(collection, document)
                if action == "conflict":
                    raise ImportConflict(f"slug changed during import: {collection_name}/{slug}")
                if action == "skip":
                    operation["action"] = "skip"
                    continue
                inserted_id = f"curriculum:v1:{collection_name}:{slug}"
                insertion = {
                    "collection": collection_name, "slug": slug,
                    "_id": inserted_id, "status": "pending",
                }
                report["insertions"].append(insertion)
                save_report()
                collection.insert_one({"_id": inserted_id, **document})
                insertion["status"] = "inserted"
                save_report()
            report["status"] = "complete"
        except Exception:
            report["status"] = "incomplete"
            save_report()
            raise
        save_report()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, help="Reviewed curriculum JSON (defaults to Python foundations)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Read-only preview (the default)")
    mode.add_argument("--apply", action="store_true", help="Opt in to insert-only writes")
    parser.add_argument("--database", help="Expected configured database name; required with --apply")
    parser.add_argument("--receipt", type=Path, help="New recovery JSON path outside this repository")
    parser.add_argument("--exclusive-writes-confirmed", action="store_true", help="Confirm other curriculum writers are paused")
    args = parser.parse_args(argv)
    if args.apply and not (args.database and args.receipt and args.exclusive_writes_confirmed):
        parser.error("--apply requires --database, --receipt and --exclusive-writes-confirmed")
    curriculum = load_curriculum(args.path)

    from pymongo import MongoClient
    from backend.config import settings
    from backend.database import TIMEOUT_SETTINGS, _timeout, _tls_options

    options = {option: _timeout(setting, default) for setting, option, default in TIMEOUT_SETTINGS}
    options.update(_tls_options(settings.MONGO_URI))
    with MongoClient(settings.MONGO_URI, **options) as client:
        database = client.get_default_database(default="education_platform")
        if args.database and args.database != database.name:
            raise ValueError("configured database differs from --database; nothing written")
        report = import_curriculum(
            database, curriculum, apply=args.apply, receipt_path=args.receipt,
            exclusive_writes=args.exclusive_writes_confirmed,
        )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print("Curriculum import failed. No updates/deletes attempted; inspect the preview and any receipt before retrying.", file=sys.stderr)
        raise SystemExit(1) from None
