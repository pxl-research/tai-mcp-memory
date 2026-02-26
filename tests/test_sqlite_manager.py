import uuid

import pytest

from db.sqlite_manager import SQLiteManager


@pytest.fixture(scope="module")
def db():
    mgr = SQLiteManager()
    mgr.initialize(reset=True)
    return mgr


def test_initialize(db):
    assert db.initialize() is True


def test_store_and_get_memory(db):
    memory_id = str(uuid.uuid4())
    content = "This is a test memory."
    topic = "test_topic"
    tags = ["test", "memory"]

    assert db.store_memory(memory_id, content, topic, tags) is True

    memory = db.get_memory(memory_id)
    assert memory is not None
    assert memory["content"] == content
    assert memory["topic_name"] == topic
    assert memory["tags"] == tags


def test_update_memory(db):
    memory_id = str(uuid.uuid4())
    db.store_memory(memory_id, "Original content", "topic_a", ["tag1"])

    assert (
        db.update_memory(memory_id, content="Updated content", topic="topic_b", tags=["tag2"])
        is True
    )

    updated = db.get_memory(memory_id)
    assert updated is not None
    assert updated["content"] == "Updated content"
    assert updated["topic_name"] == "topic_b"
    assert updated["tags"] == ["tag2"]


def test_list_topics(db):
    memory_id = str(uuid.uuid4())
    db.store_memory(memory_id, "content", "list_topics_test_topic", [])

    topics = db.list_topics()
    assert topics is not None
    assert any(t["name"] == "list_topics_test_topic" for t in topics)


def test_get_status(db):
    status = db.get_status()
    assert status is not None
    assert status["total_memories"] >= 1
    assert status["total_topics"] >= 1


def test_summary_crud(db):
    memory_id = str(uuid.uuid4())
    db.store_memory(memory_id, "summary test content", "summary_topic", [])

    summary_id = str(uuid.uuid4())
    summary_type = "abstractive_medium"
    summary_text = "Test summary."

    assert db.store_summary(summary_id, memory_id, summary_type, summary_text) is True

    types = db.list_summary_types_by_memory_id(memory_id)
    assert types is not None
    assert any(s["summary_type"] == summary_type for s in types)

    summary = db.get_summary(memory_id, summary_type)
    assert summary is not None
    assert summary["summary_text"] == summary_text

    summary_by_id = db.get_summary_by_id(summary_id)
    assert summary_by_id is not None
    assert summary_by_id["summary_text"] == summary_text

    new_text = "Updated summary."
    assert db.update_summary(summary_id, new_text) is True

    updated = db.get_summary_by_id(summary_id)
    assert updated is not None
    assert updated["summary_text"] == new_text


def test_delete_memory_cascades(db):
    memory_id = str(uuid.uuid4())
    db.store_memory(memory_id, "content to delete", "delete_cascade_topic", [])
    summary_id = str(uuid.uuid4())
    db.store_summary(summary_id, memory_id, "test_type", "summary text")

    assert db.delete_memory(memory_id) is True
    assert db.get_memory(memory_id) is None
    assert db.get_summary(memory_id, "test_type") is None


def test_topic_cleanup_after_delete(db):
    memory_id = str(uuid.uuid4())
    unique_topic = f"orphan_topic_{uuid.uuid4().hex[:8]}"
    db.store_memory(memory_id, "content", unique_topic, [])
    db.delete_memory(memory_id)

    topics = db.list_topics()
    assert not any(t["name"] == unique_topic for t in topics)


def test_get_memory_nonexistent(db):
    result = db.get_memory(str(uuid.uuid4()))
    assert result is None


def test_get_summary_nonexistent(db):
    result = db.get_summary(str(uuid.uuid4()), "nonexistent_type")
    assert result is None
