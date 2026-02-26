# Enable test mode to use separate test database
import os

os.environ["TEST_MODE"] = "1"

import json
import sys
import uuid

import pytest

# Get the absolute path to the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from db.chroma_manager import ChromaManager


@pytest.fixture(scope="module")
def chroma_man():
    """Module-scoped ChromaManager fixture.

    Reuses the singleton from core_memory_service to avoid opening a second
    PersistentClient on the same ChromaDB path. A second client on live
    SQLite+WAL files (e.g. after backups) causes 'readonly database' errors.
    """
    from memory_service.core_memory_service import chroma_manager

    chroma_manager.initialize(reset=True)
    return chroma_manager


def test_store_memory(chroma_man):
    memory_id = str(uuid.uuid4())
    content = "This is a test memory."
    topic = "test_topic"
    tags = ["test", "memory"]

    assert chroma_man.store_memory(memory_id, content, topic, tags), "store_memory failed"

    results = chroma_man.search_memories(content, topic=topic)
    assert memory_id in results, "Stored memory not found in search results"


def test_update_memory(chroma_man):
    memory_id = str(uuid.uuid4())
    content = "This is a test memory."
    topic = "test_topic"
    tags = ["test", "memory"]

    assert chroma_man.store_memory(memory_id, content, topic, tags), "store_memory failed"

    new_content = "This is an updated test memory."
    new_topic = "updated_topic"
    new_tags = ["updated", "memory"]

    assert chroma_man.update_memory(
        memory_id, new_content, new_topic, new_tags
    ), "update_memory failed"

    results = chroma_man.search_memories(new_content, topic=new_topic)
    assert memory_id in results, "Updated memory not found in search results"


def test_update_memory_preserves_metadata(chroma_man):
    from config import MEMORY_COLLECTION

    memory_id = str(uuid.uuid4())
    content = "Original content for metadata preservation test."
    topic = "meta_topic"
    tags = ["meta", "test"]
    content_size = len(content)

    assert chroma_man.store_memory(memory_id, content, topic, tags, content_size)

    # Capture metadata before update
    collection = chroma_man.client.get_collection(name=MEMORY_COLLECTION)
    before = collection.get(ids=[memory_id], include=["metadatas"])["metadatas"][0]

    assert chroma_man.update_memory(memory_id, "Updated content.", "new_topic", ["new"])

    after = collection.get(ids=[memory_id], include=["metadatas"])["metadatas"][0]

    assert after["created_at"] == before["created_at"], "created_at was overwritten by update"
    assert after["content_size"] == content_size, "content_size was lost after update"
    assert after["id"] == memory_id, "id was lost after update"
    assert (
        after["updated_at"] != before["updated_at"] or after["updated_at"] >= before["updated_at"]
    )


def test_update_topic(chroma_man):
    topic = "updated_topic"
    tags = ["test", "topic"]

    assert chroma_man.update_topic(topic, tags), "update_topic failed"

    retrieved_topic = chroma_man.get_topic(topic)
    assert retrieved_topic is not None, "Topic not found after update"
    assert json.loads(retrieved_topic["tags"]) == tags, "Topic tags not updated correctly"


def test_get_status(chroma_man):
    status = chroma_man.get_status()
    assert isinstance(status, dict), f"get_status returned {type(status)}, expected dict"


def test_store_summary_embedding(chroma_man):
    summary_id = str(uuid.uuid4())
    summary_text = "This is a test summary."
    metadata = {"test": "metadata"}

    assert chroma_man.store_summary_embedding(
        summary_id, summary_text, metadata
    ), "store_summary_embedding failed"

    retrieved = chroma_man.get_summary_by_id(summary_id)
    assert retrieved is not None, "Summary not found after storing"
    assert retrieved["summary_text"] == summary_text
    assert retrieved["test"] == "metadata"


def test_summary_embeddings(chroma_man):
    summary_id = str(uuid.uuid4())
    summary_text = "This is a test summary for embeddings."
    metadata = {"test": "embeddings"}

    assert chroma_man.store_summary_embedding(
        summary_id, summary_text, metadata
    ), "store_summary_embedding failed"

    results = chroma_man.search_summary_embeddings(summary_text)
    assert results and summary_id in results, "Summary not found in search results"

    assert chroma_man.delete_summary_embeddings(summary_id), "delete_summary_embeddings failed"

    results = chroma_man.search_summary_embeddings(summary_text)
    assert not results or summary_id not in results, "Summary still found after deletion"


def test_delete_memory(chroma_man):
    memory_id = str(uuid.uuid4())
    content = "This is a test memory for deletion."
    topic = "test_topic"
    tags = ["test", "deletion"]

    assert chroma_man.store_memory(memory_id, content, topic, tags), "store_memory failed"
    assert chroma_man.delete_memory(memory_id), "delete_memory failed"

    results = chroma_man.search_memories(content, topic=topic)
    assert not results or memory_id not in results, "Memory still found after deletion"


if __name__ == "__main__":
    manager = ChromaManager()
    manager.initialize(reset=False)
    manager.initialize()
