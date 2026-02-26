"""
Test to verify the deletion bug fix - ensures Chroma summary embeddings
are properly deleted when a memory is deleted.
"""

# Enable test mode to use separate test database
import os

os.environ["TEST_MODE"] = "1"

import sys

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import SUMMARY_COLLECTION
from memory_service import core_memory_service


def test_deletion_bug_fix():
    """
    Verify that deleting a memory also removes its Chroma summary embeddings.

    Regression test for a bug where summary embeddings were left in ChromaDB
    after the memory item was deleted from SQLite.
    """
    test_content = (
        "This is a test memory for deletion bug verification. "
        "It contains enough text to generate a meaningful summary."
    )
    result = core_memory_service.store_memory(
        test_content, "deletion_test_topic", ["test", "deletion"]
    )

    assert result.get("status") == "success", f"Could not store memory: {result}"

    memory_id = result["memory_id"]
    summary_info = result.get("summary", {})
    summary_id = summary_info.get("summary_id")

    # Verify the summary embedding exists in Chroma before deletion
    summaries_collection = core_memory_service.chroma_manager.client.get_collection(
        SUMMARY_COLLECTION
    )
    before_delete = summaries_collection.get(ids=[summary_id])
    assert (
        len(before_delete["ids"]) > 0
    ), f"Summary {summary_id} not found in Chroma before deletion"

    # Delete the memory
    delete_result = core_memory_service.delete_memory(memory_id)
    assert delete_result.get("status") == "success", f"Could not delete memory: {delete_result}"

    # Verify the summary embedding was also removed from Chroma
    after_delete = summaries_collection.get(ids=[summary_id])
    assert len(after_delete["ids"]) == 0, (
        f"Summary {summary_id} still exists in Chroma after memory deletion "
        f"(found {len(after_delete['ids'])} entries)"
    )
