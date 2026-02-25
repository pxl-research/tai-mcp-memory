"""
Helper utilities for the MCP Memory Server.
"""

import datetime
import uuid
from typing import Any


def create_memory_id() -> str:
    """Generate a unique ID for a memory item.

    Returns:
        str: A UUID string
    """
    return str(uuid.uuid4())


def timestamp() -> str:
    """Get the current timestamp.

    Returns:
        str: Current time in ISO format
    """
    return datetime.datetime.now().isoformat()


def format_response(
    success: bool, message: str, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Format a standard response dictionary.

    Args:
        success: Whether the operation was successful
        message: A message describing the result
        data: Optional data to include in the response

    Returns:
        dict: A formatted response dictionary
    """
    response: dict[str, Any] = {"status": "success" if success else "error", "message": message}

    if data:
        if success:
            response.update(data)
        else:
            response["error_details"] = data

    return response
