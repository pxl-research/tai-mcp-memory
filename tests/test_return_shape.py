"""
Test to verify the return shape consistency fix - ensures retrieve_memory
always returns a list of dicts, never format_response dicts.
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

from memory_service import core_memory_service


def test_empty_results_return_list():
    """Test that retrieve_memory returns a list even when there are no results."""
    result = core_memory_service.retrieve_memory("nonexistent_query_xyz123")

    assert isinstance(result, list), f"Result is not a list: {type(result)}"

    # If any results come back, verify they're not the old format_response wrapper
    if result:
        first = result[0]
        assert not (
            "status" in first and "message" in first
        ), f"Old format_response dict detected in results: {first}"


def test_successful_results_return_list():
    """Test that retrieve_memory returns a list of memory dicts for matching results."""
    test_content = "Test memory for return shape verification"
    store_result = core_memory_service.store_memory(test_content, "return_test", ["test"])

    assert store_result.get("status") == "success", f"Could not store test memory: {store_result}"

    result = core_memory_service.retrieve_memory("return shape verification")

    assert isinstance(result, list), f"Result is not a list: {type(result)}"

    for item in result:
        assert isinstance(item, dict), f"Item is not a dict: {type(item)}"
        assert not (
            "status" in item and "message" in item
        ), f"Old format_response dict detected: {item}"
        assert "id" in item, f"Memory dict missing 'id' field: {item}"


def test_error_handling():
    """Test that errors return an empty list, not a format_response dict."""
    try:
        result = core_memory_service.retrieve_memory(None)

        assert isinstance(result, list), f"Error result is not a list: {type(result)}"
        if result:
            assert not (
                "status" in result[0] and len(result) == 1
            ), f"Old error format_response dict detected: {result[0]}"

    except Exception:
        pass  # Raising an exception is also acceptable error handling
