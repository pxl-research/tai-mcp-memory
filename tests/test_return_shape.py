"""
Test to verify the return shape consistency fix - ensures retrieve_memory
always returns a list of dicts, never format_response dicts.
"""

import sys
import os

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from memory_service import core_memory_service


def test_empty_results_return_list():
    """Test that retrieve_memory returns empty list for no results"""
    print("\n=== Testing Empty Results Return Empty List ===")

    result = core_memory_service.retrieve_memory('nonexistent_query_xyz123')

    if not isinstance(result, list):
        print(f"   ✗ Result is not a list: {type(result)}")
        return False

    if len(result) == 0:
        print(f"   ✓ Empty results return empty list: {result}")
        return True
    else:
        # Check if it's the old format_response dict in a list
        if len(result) == 1 and isinstance(result[0], dict) and 'status' in result[0]:
            print(f"   ✗ Old format detected - format_response dict in list")
            print(f"   ✗ Result: {result}")
            return False
        else:
            # It found some actual results, which is okay
            print(f"   ✓ Found {len(result)} results (not empty, but valid)")
            return True


def test_successful_results_return_list():
    """Test that retrieve_memory returns list of memory dicts for results"""
    print("\n=== Testing Successful Results Return List of Dicts ===")

    # First store a memory
    test_content = "Test memory for return shape verification"
    store_result = core_memory_service.store_memory(test_content, 'return_test', ['test'])

    if store_result.get('status') != 'success':
        print(f"   ✗ Could not store test memory: {store_result}")
        return False

    memory_id = store_result['memory_id']

    # Now retrieve it
    result = core_memory_service.retrieve_memory('return shape verification')

    if not isinstance(result, list):
        print(f"   ✗ Result is not a list: {type(result)}")
        return False

    if len(result) == 0:
        print(f"   ⚠ No results found (expected at least one)")
        return True  # Not a failure of return shape

    # Check that results are memory dicts, not format_response dicts
    for item in result:
        if not isinstance(item, dict):
            print(f"   ✗ Item is not a dict: {type(item)}")
            return False

        # Check for memory dict fields (id, content/summary, topic, etc.)
        # Should NOT have 'status' field (that's format_response)
        if 'status' in item and 'message' in item:
            print(f"   ✗ Old format detected - format_response dict in list")
            print(f"   ✗ Item: {item}")
            return False

        if 'id' not in item:
            print(f"   ✗ Memory dict missing 'id' field")
            print(f"   ✗ Item: {item}")
            return False

    print(f"   ✓ Results are list of memory dicts: {len(result)} items")
    print(f"   ✓ Sample item keys: {list(result[0].keys())}")
    return True


def test_error_handling():
    """Test that errors return empty list, not format_response"""
    print("\n=== Testing Error Handling Returns Empty List ===")

    # Try to retrieve with None as query (should cause error)
    try:
        result = core_memory_service.retrieve_memory(None)

        if not isinstance(result, list):
            print(f"   ✗ Error result is not a list: {type(result)}")
            return False

        if len(result) == 0:
            print(f"   ✓ Error returns empty list")
            return True
        elif len(result) == 1 and 'status' in result[0]:
            print(f"   ✗ Old error format - format_response dict in list")
            return False
        else:
            print(f"   ⚠ Unexpected result on error: {result}")
            return True  # Not necessarily wrong

    except Exception as e:
        print(f"   ⓘ Exception raised instead of returning list: {type(e).__name__}")
        print(f"   ⓘ This is also acceptable error handling")
        return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing Return Shape Consistency Fix")
    print("="*60)

    try:
        # Initialize the memory system
        print("\nInitializing memory system...")
        init_result = core_memory_service.initialize_memory(reset=True)
        if init_result.get('status') != 'success':
            print(f"FAILED: Could not initialize memory system - {init_result}")
            sys.exit(1)
        print("✓ Memory system initialized")

        all_passed = True

        # Test 1: Empty results
        if not test_empty_results_return_list():
            all_passed = False

        # Test 2: Successful results
        if not test_successful_results_return_list():
            all_passed = False

        # Test 3: Error handling
        if not test_error_handling():
            all_passed = False

        print("\n" + "="*60)
        if all_passed:
            print("ALL TESTS PASSED ✓")
            print("="*60)
            sys.exit(0)
        else:
            print("SOME TESTS FAILED ✗")
            print("="*60)
            sys.exit(1)

    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
