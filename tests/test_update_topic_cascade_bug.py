"""
Test to verify the cascade delete bug fix in update_memory.

This test ensures that when updating the topic of the last memory in a topic,
the memory is not cascade-deleted due to the foreign key constraint.
"""

# Enable test mode to use separate test database
import os

os.environ["TEST_MODE"] = "1"

import sys

# Get the absolute path to the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from memory_service import core_memory_service


def test_update_topic_on_last_item():
    """
    Test that updating the topic of the last memory in a topic
    doesn't cascade-delete the memory.

    This was a critical bug where:
    1. Memory is the last item in "OldTopic"
    2. update_memory() changes topic to "NewTopic"
    3. Old topic gets deleted (item_count = 0)
    4. CASCADE DELETE removes memory (before it was updated!)
    5. Memory is lost

    The fix: Update the memory record BEFORE managing topic counts.
    """
    print("\n=== Testing Cascade Delete Bug Fix ===")

    # Initialize
    print("Initializing memory service...")
    core_memory_service.initialize_memory(reset=True)

    # Store a memory (will be the only item in "TestTopic")
    print("Storing memory in 'TestTopic'...")
    result = core_memory_service.store_memory(
        "Test content for cascade bug", "TestTopic", ["tag1", "tag2"]
    )
    memory_id = result["memory_id"]
    print(f"Stored memory with ID: {memory_id}")

    # Verify memory exists in TestTopic
    print("Verifying memory exists in 'TestTopic'...")
    memories = core_memory_service.retrieve_memory("Test content")
    assert len(memories) > 0, "Memory not found after storing"
    assert memories[0]["topic"] == "TestTopic", "Memory not in correct topic"
    print(f"✓ Memory exists in 'TestTopic' (found {len(memories)} memory)")

    # Update the topic (this was causing cascade delete bug)
    print("Updating topic to 'NewTopic' (this was causing cascade delete)...")
    update_result = core_memory_service.update_memory(memory_id=memory_id, topic="NewTopic")

    # Verify update succeeded
    assert update_result["status"] == "success", f"Update failed: {update_result}"
    print(f"✓ Update succeeded: {update_result}")

    # Verify memory still exists (was getting cascade-deleted before fix)
    print("Verifying memory still exists after topic update...")
    memories = core_memory_service.retrieve_memory("Test content")
    assert len(memories) > 0, "Memory was cascade-deleted! Bug not fixed."
    print(f"✓ Memory survived topic update (found {len(memories)} memory)")

    # Verify topic was actually updated
    assert (
        memories[0]["topic"] == "NewTopic"
    ), f"Topic not updated correctly. Expected 'NewTopic', got '{memories[0]['topic']}'"
    print("✓ Topic correctly updated to 'NewTopic'")

    print("\n✅ Bug fixed - memory survived topic update on last item in topic")


def test_update_topic_on_one_of_many():
    """
    Test that updating the topic when there are multiple memories in a topic
    still works correctly (this should have always worked).
    """
    print("\n=== Testing Update Topic on One of Many Items ===")

    # Initialize
    print("Initializing memory service...")
    core_memory_service.initialize_memory(reset=True)

    # Store multiple memories in the same topic
    print("Storing multiple memories in 'SharedTopic'...")
    result1 = core_memory_service.store_memory("First memory content", "SharedTopic", ["tag1"])
    result2 = core_memory_service.store_memory("Second memory content", "SharedTopic", ["tag2"])
    memory_id_1 = result1["memory_id"]
    memory_id_2 = result2["memory_id"]
    print(f"Stored memories: {memory_id_1}, {memory_id_2}")

    # Update topic of first memory
    print("Updating topic of first memory to 'NewTopic'...")
    update_result = core_memory_service.update_memory(memory_id=memory_id_1, topic="NewTopic")
    assert update_result["status"] == "success", f"Update failed: {update_result}"
    print("✓ Update succeeded")

    # Verify first memory moved to NewTopic
    memories = core_memory_service.retrieve_memory("First memory")
    assert len(memories) > 0, "First memory not found"
    assert memories[0]["topic"] == "NewTopic", "First memory topic not updated"
    print("✓ First memory now in 'NewTopic'")

    # Verify second memory still in SharedTopic
    memories = core_memory_service.retrieve_memory("Second memory")
    assert len(memories) > 0, "Second memory not found"
    assert memories[0]["topic"] == "SharedTopic", "Second memory topic changed unexpectedly"
    print("✓ Second memory still in 'SharedTopic'")

    print("\n✅ Update topic on one of many items works correctly")


def test_update_content_only():
    """
    Test that updating only content (no topic change) still works correctly.
    """
    print("\n=== Testing Update Content Only ===")

    # Initialize
    print("Initializing memory service...")
    core_memory_service.initialize_memory(reset=True)

    # Store a memory
    print("Storing memory...")
    result = core_memory_service.store_memory("Original content", "TestTopic", ["tag1"])
    memory_id = result["memory_id"]

    # Update only content
    print("Updating content only (no topic change)...")
    update_result = core_memory_service.update_memory(
        memory_id=memory_id, content="Updated content"
    )
    assert update_result["status"] == "success", f"Update failed: {update_result}"
    print("✓ Update succeeded")

    # Verify content changed, topic stayed the same
    memories = core_memory_service.retrieve_memory("Updated content")
    assert len(memories) > 0, "Memory not found after content update"
    assert memories[0]["topic"] == "TestTopic", "Topic changed unexpectedly"
    print("✓ Content updated, topic unchanged")

    print("\n✅ Update content only works correctly")


if __name__ == "__main__":
    try:
        test_update_topic_on_last_item()
        test_update_topic_on_one_of_many()
        test_update_content_only()
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
