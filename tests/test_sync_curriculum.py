import copy
from datetime import datetime
import json

from bson import ObjectId
import pytest

from scripts import sync_curriculum as sync


class Cursor(list):
    def limit(self, maximum):
        return Cursor(self[:maximum])

    def max_time_ms(self, maximum):
        return self


class Collection:
    def __init__(self, documents=()):
        self.documents = copy.deepcopy(list(documents))
        self.inserted = []
        self.fail_insert = False

    def find(self, query):
        return Cursor(copy.deepcopy([document for document in self.documents if all(document.get(key) == value for key, value in query.items())]))

    def find_one(self, query, **options):
        matches = self.find(query)
        return matches[0] if matches else None

    def insert_one(self, document):
        if self.fail_insert:
            raise RuntimeError("test interrupted insert")
        assert not any(existing["_id"] == document["_id"] for existing in self.documents)
        self.documents.append(copy.deepcopy(document))
        self.inserted.append(copy.deepcopy(document))


@pytest.fixture
def content(monkeypatch):
    authored = {
        "topics": [{"_id": "topic-new", "slug": "new-topic", "title": "Authored lesson"}],
        "practice_problems": [{"_id": ObjectId("a" * 24), "topic_slug": "new-topic", "title": "Practice"}],
        "domains": [{"_id": "domain-new", "slug": "new-domain", "topics": ["new-topic"]}],
    }
    monkeypatch.setattr(sync, "authored_documents", lambda: copy.deepcopy(authored))
    database = {name: Collection() for name in sync.COLLECTIONS}
    return database, authored


def test_preview_is_read_only_and_conflicts_fail_closed(content, tmp_path):
    database, authored = content
    database["topics"].documents.append({"_id": "existing", "slug": "new-topic", "title": "Keep this content"})
    operations = sync.plan(database, authored)
    assert operations[0]["action"] == "conflict"
    with pytest.raises(ValueError, match="Conflicting"):
        sync.apply_plan(database, operations, tmp_path / "backup", tmp_path / "receipt.json", "target")
    assert not (tmp_path / "backup").exists()
    assert all(not collection.inserted for collection in database.values())


def test_verified_insert_only_import_preserves_existing_bson_and_is_idempotent(content, tmp_path):
    database, authored = content
    old = {"_id": ObjectId("b" * 24), "slug": "existing-topic", "created_at": datetime(2020, 1, 1), "value": [1, 2]}
    database["topics"].documents.append(copy.deepcopy(old))
    report = sync.apply_plan(database, sync.plan(database, authored), tmp_path / "backup", tmp_path / "receipt.json", "target")
    assert report["status"] == "verified"
    assert len(report["insertions"]) == 3
    assert database["topics"].documents[0] == old
    restored = sync.json_util.loads((tmp_path / "backup" / "topics.json").read_text())
    assert restored == [old]
    assert sync.plan(database, authored)[0]["action"] == "skip"
    assert all(operation["action"] == "skip" for operation in sync.plan(database, authored))
    assert json.loads((tmp_path / "receipt.json").read_text())["status"] == "verified"


def test_partial_failure_keeps_backup_and_durable_pending_receipt(content, tmp_path):
    database, authored = content
    database["practice_problems"].fail_insert = True
    with pytest.raises(RuntimeError):
        sync.apply_plan(database, sync.plan(database, authored), tmp_path / "backup", tmp_path / "receipt.json", "target")
    report = json.loads((tmp_path / "receipt.json").read_text())
    assert report["status"] == "incomplete"
    assert [entry["status"] for entry in report["insertions"]] == ["inserted", "pending"]
    assert (tmp_path / "backup" / "manifest.json").exists()
    assert not database["domains"].inserted


def test_backup_never_overwrites_existing_directory(content, tmp_path):
    database, authored = content
    existing = tmp_path / "backup"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        sync.backup_content(sync.snapshot(database), existing, "target")


def test_real_authored_practice_projection_contains_no_reference_solutions():
    documents = sync.authored_documents()
    assert len(documents["topics"]) == 15
    assert len(documents["practice_problems"]) == 15
    assert len(documents["domains"]) == 1
    assert all("reference_solution" not in problem for problem in documents["practice_problems"])


def test_target_fingerprint_ignores_credentials_but_distinguishes_databases():
    first = sync.fingerprint("mongodb+srv://<user>:<password>@cluster.example.test/app", "app")
    assert first == sync.fingerprint("mongodb+srv://cluster.example.test/app", "app")
    assert first != sync.fingerprint("mongodb+srv://cluster.example.test/app", "different")
