import logging
import os
import sys
from typing import Literal

# Get the absolute path to the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import (
    ENABLE_AUTO_BACKUP,
    OPENROUTER_API_KEY,
    SMALL_CONTENT_THRESHOLD,
    TINY_CONTENT_THRESHOLD,
)
from db import ChromaManager, SQLiteManager
from utils import create_memory_id, format_response, timestamp
from utils.backup import create_backup_if_due
from utils.summarizer import Summarizer

logger = logging.getLogger(__name__)


def _determine_summary_strategy(
    content: str,
) -> tuple[
    Literal["direct_tiny", "extractive_short", "abstractive_medium"],
    Literal["abstractive", "extractive", "query_focused"],
    Literal["short", "medium", "detailed"],
]:
    """Return (summary_type_used, summary_type_arg, length_arg) for the given content size."""
    size = len(content)
    if size < TINY_CONTENT_THRESHOLD:
        return "direct_tiny", "extractive", "short"  # summary_type_arg unused for direct_tiny
    elif size < SMALL_CONTENT_THRESHOLD:
        return "extractive_short", "extractive", "short"
    else:
        return "abstractive_medium", "abstractive", "medium"


# Initialize database managers
sqlite_manager = SQLiteManager()
chroma_manager = ChromaManager()

# Initialize summarizer
summarizer = Summarizer(api_key=OPENROUTER_API_KEY or "")

# Validate API key and warn if missing
if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.strip() == "":
    logger.warning(
        "OPENROUTER_API_KEY is not set. Memory storage will work, but automatic "
        "summarization will be disabled. Set OPENROUTER_API_KEY in .env to enable summarization."
    )


def initialize_memory(reset: bool) -> dict:
    """Initialize or reset the memory system databases.

    Args:
        reset: Whether to reset existing memory databases.

    Returns:
        dict: Initialization status
    """
    try:
        # Initialize SQLite
        sqlite_success = sqlite_manager.initialize(reset)

        # Initialize ChromaDB
        chroma_success = chroma_manager.initialize(reset)

        if sqlite_success and chroma_success:
            return format_response(
                success=True,
                message="Memory system initialized successfully",
                data={"reset": reset},
            )
        else:
            return format_response(
                success=False,
                message="Error initializing memory system",
                data={"sqlite_success": sqlite_success, "chroma_success": chroma_success},
            )

    except Exception as e:
        return format_response(success=False, message=f"Error initializing memory system: {str(e)}")


def store_memory(content: str, topic: str, tags: list[str] | None = None) -> dict:
    """Store new information in the persistent memory system.

    Args:
        content: The text content to store in memory.
        topic: The primary topic or category for this content.
        tags: Optional list of tags for better retrieval.

    Returns:
        dict: Status and ID of the stored content
    """
    if tags is None:
        tags = []
    try:
        # Automatic backup check (if enabled)
        if ENABLE_AUTO_BACKUP:
            backup_file = create_backup_if_due()
            if backup_file:
                logger.info(f"Automatic backup created: {backup_file}")

        memory_id = create_memory_id()
        now = timestamp()
        content_size = len(content)

        # Store in SQLite
        sqlite_success = sqlite_manager.store_memory(memory_id, content, topic, tags)

        # Store in ChromaDB with content_size metadata
        chroma_success = chroma_manager.store_memory(memory_id, content, topic, tags, content_size)

        # Update topic in ChromaDB
        topic_success = chroma_manager.update_topic(topic, tags)

        # Size-based summarization strategy
        summary_type_used, summary_type_arg, length_arg = _determine_summary_strategy(content)

        generated_summary: str | None
        if summary_type_used == "direct_tiny":
            generated_summary = content
            logger.info(
                f"Using content directly for tiny content ({content_size} chars) - no LLM summarization"
            )
        else:
            generated_summary = summarizer.generate_summary(
                content, summary_type=summary_type_arg, length=length_arg
            )
            logger.info(f"Using {summary_type_used} summary for content ({content_size} chars)")

        summary_stored = False
        summary_embedding_stored = False
        summary_id = create_memory_id()

        if generated_summary:
            summary_stored = sqlite_manager.store_summary(
                summary_id, memory_id, summary_type_used, generated_summary
            )
            summary_embedding_stored = chroma_manager.store_summary_embedding(
                summary_id,
                generated_summary,
                {"memory_id": memory_id, "summary_type": summary_type_used, "topic": topic},
            )
        else:
            # Warn if we tried to generate a summary but failed
            logger.warning(
                f"Failed to generate summary for memory_id {memory_id}. Original content stored without summary."
            )

        if sqlite_success and chroma_success:
            return format_response(
                success=True,
                message="Content stored successfully",
                data={
                    "memory_id": memory_id,
                    "topic": topic,
                    "tags": tags,
                    "timestamp": now,
                    "content_size": content_size,
                    "summary": {
                        "summary_generated": bool(generated_summary),
                        "summary_type": summary_type_used,
                        "summary_stored": summary_stored,
                        "summary_embedding_stored": summary_embedding_stored,
                        "summary_id": summary_id,
                    },
                },
            )
        else:
            return format_response(
                success=False,
                message="Error storing content",
                data={
                    "sqlite_success": sqlite_success,
                    "chroma_success": chroma_success,
                    "topic_success": topic_success,
                    "content_size": content_size,
                    "summary": {
                        "summary_generated": bool(generated_summary),
                        "summary_type": summary_type_used,
                        "summary_stored": summary_stored,
                        "summary_embedding_stored": summary_embedding_stored,
                        "summary_id": summary_id,
                    },
                },
            )

    except Exception as e:
        return format_response(success=False, message=f"Error storing content: {str(e)}")


def retrieve_memory(
    query: str,
    max_results: int = 5,
    topic: str | None = None,
    return_type: Literal["full_text", "summary", "both"] = "full_text",
) -> list[dict]:
    """Retrieve information from memory using semantic search.

    Args:
        query: The search query to find relevant information.
        max_results: Maximum number of results to return.
        topic: Optional topic to restrict search to.
        return_type: The type of content to return (full_text, summary, or both).

    Returns:
        List[dict]: List of matching memory items with content and metadata
    """
    try:
        # Prioritize semantic search on summaries for efficiency
        summary_ids = chroma_manager.search_summary_embeddings(query, max_results, topic)
        memory_items = []
        for summary_id in summary_ids:
            summary_item = sqlite_manager.get_summary_by_id(summary_id)
            if summary_item:
                memory_id = summary_item["memory_id"]
                full_memory_item = sqlite_manager.get_memory(memory_id)

                if full_memory_item:
                    result_data = {
                        "id": memory_id,
                        "topic": full_memory_item["topic_name"],
                        "tags": full_memory_item["tags"],
                        "created_at": full_memory_item["created_at"],
                        "updated_at": full_memory_item["updated_at"],
                    }

                    if return_type == "full_text":
                        result_data["content"] = full_memory_item["content"]
                    elif return_type == "summary":
                        result_data["summary"] = summary_item["summary_text"]
                    elif return_type == "both":
                        result_data["content"] = full_memory_item["content"]
                        result_data["summary"] = summary_item["summary_text"]

                    memory_items.append(result_data)
            else:
                logger.warning(f"Summary ID {summary_id} not found in SQLite.")

        return memory_items

    except Exception as e:
        logger.error(f"Error retrieving from memory: {str(e)}")
        return []


def update_memory(
    memory_id: str,
    content: str | None = None,
    topic: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Update an existing memory item.

    Args:
        memory_id: ID of the memory item to update.
        content: New content (if updating content).
        topic: New topic (if changing).
        tags: New tags (if updating).

    Returns:
        dict: Status and updated memory details
    """
    if not any([content, topic, tags]):
        return format_response(
            success=False, message="At least one of content, topic, or tags must be provided"
        )

    try:
        # Get current memory item
        current_item = sqlite_manager.get_memory(memory_id)

        if not current_item:
            return format_response(
                success=False, message=f"Memory item with ID {memory_id} not found"
            )

        # Update in SQLite
        sqlite_success = sqlite_manager.update_memory(
            memory_id=memory_id, content=content, topic=topic, tags=tags
        )

        # Get updated item for ChromaDB update
        updated_item = sqlite_manager.get_memory(memory_id)
        if updated_item is None:
            return format_response(
                success=False, message=f"Memory {memory_id} not found after update"
            )

        # Update in ChromaDB
        chroma_success = chroma_manager.update_memory(
            memory_id=memory_id,
            content=updated_item["content"],
            topic=updated_item["topic_name"],
            tags=updated_item["tags"],
        )

        # Update topic in ChromaDB if topic changed
        if topic is not None:
            chroma_manager.update_topic(topic, updated_item["tags"])

        # Regenerate and update summary if content changed
        summary_updated = False
        if content is not None:
            summary_type_used, summary_type_arg, length_arg = _determine_summary_strategy(
                updated_item["content"]
            )
            generated_summary: str | None
            if summary_type_used == "direct_tiny":
                generated_summary = updated_item["content"]
            else:
                generated_summary = summarizer.generate_summary(
                    updated_item["content"], summary_type=summary_type_arg, length=length_arg
                )
            if generated_summary:
                existing_summary = sqlite_manager.get_any_summary(memory_id)
                if existing_summary:
                    summary_updated = sqlite_manager.update_summary(
                        existing_summary["id"], generated_summary, summary_type_used
                    )
                    chroma_manager.store_summary_embedding(
                        existing_summary["id"],
                        generated_summary,
                        {
                            "memory_id": memory_id,
                            "summary_type": summary_type_used,
                            "topic": updated_item["topic_name"],
                        },
                    )
                else:
                    logger.info(
                        f"Creating new summary for memory_id {memory_id} after content update."
                    )
                    summary_id = create_memory_id()
                    summary_updated = sqlite_manager.store_summary(
                        summary_id, memory_id, summary_type_used, generated_summary
                    )
                    chroma_manager.store_summary_embedding(
                        summary_id,
                        generated_summary,
                        {
                            "memory_id": memory_id,
                            "summary_type": summary_type_used,
                            "topic": updated_item["topic_name"],
                        },
                    )
            else:
                logger.warning(
                    f"Failed to regenerate summary for memory_id {memory_id} during update."
                )

        if sqlite_success and chroma_success:
            return format_response(
                success=True,
                message="Memory item updated successfully",
                data={
                    "memory_id": memory_id,
                    "updated_fields": {
                        "content": content is not None,
                        "topic": topic is not None,
                        "tags": tags is not None,
                    },
                    "timestamp": timestamp(),
                    "summary_updated": summary_updated,
                },
            )
        else:
            return format_response(
                success=False,
                message="Error updating memory item",
                data={
                    "sqlite_success": sqlite_success,
                    "chroma_success": chroma_success,
                    "summary_updated": summary_updated,
                },
            )

    except Exception as e:
        return format_response(success=False, message=f"Error updating memory item: {str(e)}")


def delete_memory(memory_id: str) -> dict:
    """Delete a memory item from the system.

    Args:
        memory_id: ID of the memory item to delete.

    Returns:
        dict: Status of the deletion operation.
    """
    try:
        # Step 1: Get all summaries BEFORE deleting (to retrieve IDs for Chroma)
        all_summaries = sqlite_manager.list_summary_types_by_memory_id(memory_id)

        # Step 2: Delete Chroma summary embeddings using the retrieved IDs
        chroma_summary_delete_success = True
        if all_summaries:
            for summary_info in all_summaries:
                summary = sqlite_manager.get_summary(memory_id, summary_info["summary_type"])
                if summary:
                    result = chroma_manager.delete_summary_embeddings(summary["id"])
                    chroma_summary_delete_success = chroma_summary_delete_success and result

        # Step 3: Delete memory from SQLite (will cascade delete summaries)
        sqlite_success = sqlite_manager.delete_memory(memory_id)

        # Step 4: Delete memory embedding from Chroma
        chroma_success = chroma_manager.delete_memory(memory_id)

        # Note: sqlite_manager.delete_summaries() is now redundant (cascade handles it)

        if sqlite_success and chroma_success and chroma_summary_delete_success:
            return format_response(
                success=True,
                message=f"Memory item {memory_id} and its summaries deleted successfully",
            )
        else:
            return format_response(
                success=False,
                message=f"Error deleting memory item {memory_id} or its summaries",
                data={
                    "sqlite_success": sqlite_success,
                    "chroma_success": chroma_success,
                    "chroma_summary_delete_success": chroma_summary_delete_success,
                },
            )
    except Exception as e:
        return format_response(success=False, message=f"Error deleting memory item: {str(e)}")
