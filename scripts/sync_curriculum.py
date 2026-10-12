import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit
import uuid

from bson import ObjectId, json_util

from backend.curriculum import load_curriculum, load_practice, public_practice


ROOT = Path(__file__).resolve().parents[1]
COLLECTIONS = ("topics", "practice_problems", "domains")
MAX_DOCUMENTS = 10000


def canonical(documents):
    return json_util.dumps(documents, json_options=json_util.CANONICAL_JSON_OPTIONS, sort_keys=True, separators=(",", ":"))


def fingerprint(uri, database_name):
    host = urlsplit(uri).netloc.rsplit("@", 1)[-1].lower()
    return hashlib.sha256(f"{host}\n{database_name}".encode()).hexdigest()


def authored_documents():
    curriculum = load_curriculum()
    return {
        "topics": [{"_id": f"curriculum:v1:topics:{topic['slug']}", **topic} for topic in curriculum["topics"]],
        "domains": [{"_id": f"curriculum:v1:domains:{domain['slug']}", **domain} for domain in curriculum["domains"]],
        "practice_problems": [{"_id": ObjectId(problem["id"]), **public_practice(problem)} for problem in load_practice()],
    }


def identity(collection_name, document):
    return {"topic_slug": document["topic_slug"]} if collection_name == "practice_problems" else {"slug": document["slug"]}


def action(collection, collection_name, document):
    existing = list(collection.find(identity(collection_name, document)).limit(2).max_time_ms(5000))
    if not existing:
        return "conflict" if collection.find_one({"_id": document["_id"]}, max_time_ms=5000) else "insert"
    values = {key: value for key, value in document.items() if key != "_id"}
    return "skip" if len(existing) == 1 and all(existing[0].get(key) == value for key, value in values.items()) else "conflict"


def plan(database, authored):
    return [{"collection": name, "document": document, "action": action(database[name], name, document)}
            for name in COLLECTIONS for document in authored[name]]


def snapshot(database):
    result = {}
    for name in COLLECTIONS:
        documents = list(database[name].find({}).limit(MAX_DOCUMENTS + 1).max_time_ms(15000))
        if len(documents) > MAX_DOCUMENTS:
            raise ValueError("Content backup exceeds safety bounds")
        result[name] = sorted(documents, key=lambda document: str(document["_id"]))
    return result


def backup_content(documents, directory, target):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    manifest = {"target": target, "scope": "content-only", "collections": {}}
    for name in COLLECTIONS:
        raw = canonical(documents[name]).encode("utf-8")
        with (directory / f"{name}.json").open("xb") as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        restored = json_util.loads((directory / f"{name}.json").read_text(encoding="utf-8"))
        if canonical(restored) != canonical(documents[name]):
            raise ValueError("Backup round-trip verification failed")
        manifest["collections"][name] = {"count": len(restored), "sha256": hashlib.sha256(raw).hexdigest()}
    with (directory / "manifest.json").open("x", encoding="utf-8") as output:
        json.dump(manifest, output, indent=2)
    return manifest


def write_journal(path, report):
    with Path(path).open("w", encoding="utf-8") as journal:
        json.dump(report, journal, indent=2)
        journal.flush()
        os.fsync(journal.fileno())


def apply_plan(database, operations, backup_directory, receipt, target):
    if any(operation["action"] == "conflict" for operation in operations):
        raise ValueError("Conflicting content; nothing written")
    before = snapshot(database)
    backup_content(before, backup_directory, target)
    if canonical(snapshot(database)) != canonical(before):
        raise ValueError("Content changed during backup; nothing written")
    report = {"target": target, "status": "started", "backup": str(backup_directory), "insertions": []}
    write_journal(receipt, report)
    try:
        for operation in operations:
            name, document = operation["collection"], operation["document"]
            current = action(database[name], name, document)
            if current == "conflict":
                raise ValueError("Content changed during import; inspect recovery receipt")
            if current == "skip":
                continue
            insertion = {"collection": name, "id": str(document["_id"]), "status": "pending"}
            report["insertions"].append(insertion)
            write_journal(receipt, report)
            database[name].insert_one(document)
            insertion["status"] = "inserted"
            write_journal(receipt, report)
        after = snapshot(database)
        for name in COLLECTIONS:
            preserved = {str(document["_id"]): canonical(document) for document in after[name]}
            if any(preserved.get(str(document["_id"])) != canonical(document) for document in before[name]):
                raise ValueError("Existing content preservation check failed")
        if any(operation["action"] != "skip" for operation in plan(database, authored_documents())):
            raise ValueError("Imported content verification failed")
        report["status"] = "verified"
        report["counts"] = {name: len(documents) for name, documents in after.items()}
    except Exception:
        report["status"] = "incomplete"
        write_journal(receipt, report)
        raise
    write_journal(receipt, report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Preview by default; backed-up, insert-only authored content synchronization. Never writes users, progress or private history.")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-target", help="Target fingerprint from the reviewed preview; required for apply")
    parser.add_argument("--exclusive-writes-confirmed", action="store_true")
    args = parser.parse_args()
    if args.apply and not (args.expected_target and args.exclusive_writes_confirmed):
        parser.error("Apply requires reviewed --expected-target and --exclusive-writes-confirmed")
    from pymongo import MongoClient
    from backend.config import settings
    from backend.database import TIMEOUT_SETTINGS, _timeout, _tls_options
    options = {option: _timeout(setting, default) for setting, option, default in TIMEOUT_SETTINGS}
    options.update(_tls_options(settings.MONGO_URI))
    with MongoClient(settings.MONGO_URI, **options) as client:
        database = client.get_default_database(default="education_platform")
        target = fingerprint(settings.MONGO_URI, database.name)
        if args.expected_target and args.expected_target != target:
            raise ValueError("Configured database target differs from reviewed preview")
        operations = plan(database, authored_documents())
        summary = {"target": target, "mode": "preview", "actions": {}}
        for name in COLLECTIONS:
            summary["actions"][name] = {kind: sum(operation["collection"] == name and operation["action"] == kind for operation in operations)
                                        for kind in ("insert", "skip", "conflict")}
        print(json.dumps(summary))
        if not args.apply:
            return 1 if any(operation["action"] == "conflict" for operation in operations) else 0
        backup = ROOT / "backups" / (datetime.now(timezone.utc).strftime("curriculum-%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8])
        receipt = Path(tempfile.mkdtemp(prefix="placement-mentor-import-")) / "receipt.json"
        print(json.dumps({"check": "recovery_locations", "backup": str(backup), "receipt": str(receipt)}))
        report = apply_plan(database, operations, backup, receipt, target)
        print(json.dumps({"status": report["status"], "inserted": len(report["insertions"]), "counts": report["counts"], "backup": str(backup), "receipt": str(receipt)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print("Content synchronization failed. No updates or deletes attempted; review any backup and receipt before retrying.")
        raise SystemExit(1) from None
