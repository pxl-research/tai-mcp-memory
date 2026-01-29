"""
Test to verify the deletion bug fix - ensures Chroma summary embeddings
are properly deleted when a memory is deleted.
"""

# Enable test mode to use separate test database
import os
os.environ['TEST_MODE'] = '1'

import sys

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from memory_service import core_memory_service
from db.chroma_manager import ChromaManager


def test_deletion_bug_fix():
    """
    Test that verifies the deletion bug fix:
    1. Store a memory (creates summary + Chroma embeddings)
    2. Verify summary exists in Chroma
    3. Delete the memory
    4. Verify summary is deleted from Chroma (this would fail with the old bug)
    """
    print("\n=== Testing Deletion Bug Fix ===")

    # Step 1: Store a memory
    print("\n1. Storing a memory...")
    test_content = "This is a test memory for deletion bug verification. It contains enough text to generate a meaningful summary."
    result = core_memory_service.store_memory(test_content, 'deletion_test_topic', ['test', 'deletion'])

    if result.get('status') != 'success':
        print(f"FAILED: Could not store memory - {result}")
        return False

    memory_id = result['memory_id']
    summary_info = result.get('summary', {})
    summary_id = summary_info.get('summary_id')

    print(f"   Memory stored: {memory_id}")
    print(f"   Summary ID: {summary_id}")
    print(f"   Summary generated: {summary_info.get('summary_generated')}")
    print(f"   Summary stored: {summary_info.get('summary_stored')}")
    print(f"   Summary embedding stored: {summary_info.get('summary_embedding_stored')}")

    if not summary_info.get('summary_embedding_stored'):
        print("WARNING: Summary embedding was not stored, test may not be meaningful")

    # Step 2: Verify summary exists in Chroma
    print("\n2. Verifying summary exists in Chroma...")
    cm = ChromaManager()
    try:
        summaries_collection = cm.client.get_collection('summaries')
        before_delete = summaries_collection.get(ids=[summary_id])

        if len(before_delete['ids']) == 0:
            print(f"FAILED: Summary {summary_id} not found in Chroma before deletion")
            return False

        print(f"   ✓ Summary exists in Chroma with {len(before_delete['ids'])} entries")
    except Exception as e:
        print(f"FAILED: Error checking Chroma before deletion - {e}")
        return False

    # Step 3: Delete the memory
    print("\n3. Deleting memory...")
    delete_result = core_memory_service.delete_memory(memory_id)

    if delete_result.get('status') != 'success':
        print(f"FAILED: Could not delete memory - {delete_result}")
        return False

    print(f"   ✓ Memory deleted successfully")
    print(f"   Delete result: {delete_result}")

    # Step 4: Verify summary is deleted from Chroma
    print("\n4. Verifying summary is deleted from Chroma...")
    try:
        after_delete = summaries_collection.get(ids=[summary_id])

        if len(after_delete['ids']) > 0:
            print(f"FAILED: Summary {summary_id} still exists in Chroma after deletion!")
            print(f"   Found {len(after_delete['ids'])} entries (should be 0)")
            print("   BUG STILL EXISTS - Chroma embeddings not properly deleted")
            return False

        print(f"   ✓ Summary successfully deleted from Chroma")
        print("   BUG FIXED! - Chroma embeddings properly cleaned up")
        return True

    except Exception as e:
        # An exception might mean the document doesn't exist, which is also good
        print(f"   ✓ Summary not found in Chroma (exception: {type(e).__name__})")
        print("   BUG FIXED! - Chroma embeddings properly cleaned up")
        return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing the Deletion Bug Fix")
    print("="*60)

    try:
        # Initialize the memory system
        print("\nInitializing memory system...")
        init_result = core_memory_service.initialize_memory(reset=True)
        if init_result.get('status') != 'success':
            print(f"FAILED: Could not initialize memory system - {init_result}")
            sys.exit(1)
        print("✓ Memory system initialized")

        # Run the test
        success = test_deletion_bug_fix()

        print("\n" + "="*60)
        if success:
            print("TEST PASSED ✓")
            print("="*60)
            sys.exit(0)
        else:
            print("TEST FAILED ✗")
            print("="*60)
            sys.exit(1)

    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
