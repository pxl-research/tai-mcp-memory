"""
MCP Server for Persistent Memory.

This server provides a set of tools for storing, retrieving, and managing
persistent memory for LLMs through the Model Context Protocol (MCP).
"""

import os
import sys
from typing import List, Optional, Annotated, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import Field

# Get the absolute path to the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from memory_service import core_memory_service, auxiliary_memory_service

# Initialize the MCP server
mcp = FastMCP("memory_server")


# -------------------------
# Prompts (discovery helpers)
# -------------------------

@mcp.prompt()
def store_memory_prompt(
        content: Annotated[
            str,
            Field(
                description="Exact text to store (unaltered)",
                examples=[
                    "Reminder: Standup moved to 10:15 Mon–Thu.",
                    "Postgres uses MVCC for concurrency."
                ]
            )
        ],
        topic: Annotated[
            Optional[str],
            Field(
                description="Short topic/category (e.g., 'project/roadmap')",
                default=None,
                examples=["project/roadmap", "databases", None]
            )
        ] = None
) -> str:
    """Guide the model to store a memory using minimal fields.

    Returns a concise instruction prompt for the assistant to either ask one
    short clarification for missing topic or call the memory_store tool.
    """
    return (
        "Store memory (minimal)\n\n"
        "Goal\n- Persist information for future use with minimal friction.\n\n"
        f"Content to store:\n{content}\n\n"
        f"Topic provided: {topic if topic else 'None'}\n\n"
        "Instructions\n"
        "- If topic is missing, ask exactly ONE short clarifying question (<= 15 words) to get it, then proceed.\n"
        "- Call memory_store with:\n"
        "  - content: the exact text above (unaltered)\n"
        "  - topic: a short topic string\n"
        "  - tags: OPTIONAL list of 1–5 concise tags (omit if unsure)\n"
        "- Do not add commentary or rewrite the content.\n\n"
        "Output\n- Only emit the tool call with its arguments (no prose).\n"
    )


@mcp.prompt()
def recall_memory_prompt(
        query: Annotated[
            str,
            Field(
                description="What to retrieve (natural language)",
                examples=[
                    "What did we decide about release timing?",
                    "Key points about MVCC"
                ]
            )
        ],
        topic: Annotated[
            Optional[str],
            Field(
                description="Optional topic filter",
                default=None,
                examples=["project/roadmap", None]
            )
        ] = None
) -> str:
    """Guide the model to recall the most relevant memories.

    Returns a compact instruction prompt for calling memory_retrieve and
    formatting the results succinctly.
    """
    return (
        "Recall memory (minimal)\n\n"
        "Goal\n- Retrieve the most relevant stored memories for the current task.\n\n"
        f"Query:\n{query}\n\n"
        f"Topic filter: {topic if topic else 'None'}\n\n"
        "Instructions\n"
        "- Build a concise semantic query from the request.\n"
        "- Call memory_retrieve with:\n"
        "  - query: the brief query above\n"
        "  - max_results: 5\n"
        "  - topic: OMIT if not provided\n"
        "  - return_type: 'both'\n"
        "- If no good results, ask exactly ONE short follow-up (<= 15 words).\n"
        "- After results, present a compact list: [memory_id] topic — brief snippet (score).\n\n"
        "Output\n- First emit the tool call. After tool results, output a 3–5 item bullet list as above (no extra prose).\n"
    )


@mcp.tool()
def memory_initialize(
        reset: Annotated[
            bool,
            Field(
                description="Whether to reset existing memory",
                default=False,
                examples=[False, True]
            )
        ] = False
) -> dict:
    """Initialize or reset the memory system databases.
    
    Args:
        reset: Whether to reset existing memory databases.
        
    Returns:
        dict: Initialization status
    """
    return core_memory_service.initialize_memory(reset=reset)


@mcp.tool()
def memory_store(
        content: Annotated[
            str,
            Field(
                description="The content to store in memory",
                examples=["Quantum computing uses qubits which can exist in multiple states simultaneously."]
            )
        ],
        topic: Annotated[
            str,
            Field(
                description="Primary topic/category for this content",
                examples=["quantum_computing", "machine_learning", "history"]
            )
        ],
        tags: Annotated[
            List[str],
            Field(
                description="Optional tags for better retrieval",
                default=[],
                examples=[["physics", "computing", "technology"], ["ai", "neural_networks"]]
            )
        ] = []
) -> dict:
    """Store new information in the persistent memory system.
    
    Args:
        content: The text content to store in memory.
        topic: The primary topic or category for this content.
        tags: Optional list of tags for better retrieval.
        
    Returns:
        dict: Status and ID of the stored content
    """
    return core_memory_service.store_memory(content=content, topic=topic, tags=tags)


@mcp.tool()
def memory_retrieve(
        query: Annotated[
            str,
            Field(
                description="The query to search for in memory",
                examples=["How do quantum computers work?", "Tell me about machine learning"]
            )
        ],
        max_results: Annotated[
            int,
            Field(
                description="Maximum number of results to return",
                default=5,
                examples=[3, 5, 10]
            )
        ] = 5,
        topic: Annotated[
            Optional[str],
            Field(
                description="Optional topic to restrict search to",
                default=None,
                examples=["quantum_computing", "machine_learning"]
            )
        ] = None,
        return_type: Annotated[
            Literal["full_text", "summary", "both"],
            Field(
                description="The type of content to return: full_text, summary, or both",
                default="full_text",
                examples=["full_text", "summary", "both"]
            )
        ] = "full_text"
) -> List[dict]:
    """Retrieve information from memory using semantic search.
    
    Args:
        query: The search query to find relevant information.
        max_results: Maximum number of results to return.
        topic: Optional topic to restrict search to.
        return_type: The type of content to return (full_text, summary, or both).
        
    Returns:
        List[dict]: List of matching memory items with content and metadata
    """
    return core_memory_service.retrieve_memory(query=query, max_results=max_results, topic=topic,
                                               return_type=return_type)


@mcp.tool()
def memory_update(
        memory_id: Annotated[
            str,
            Field(
                description="ID of the memory item to update",
                examples=["550e8400-e29b-41d4-a716-446655440000"]
            )
        ],
        content: Annotated[
            Optional[str],
            Field(
                description="New content (if updating content)",
                default=None,
                examples=["Updated information about quantum computing"]
            )
        ] = None,
        topic: Annotated[
            Optional[str],
            Field(
                description="New topic (if changing)",
                default=None,
                examples=["quantum_physics"]
            )
        ] = None,
        tags: Annotated[
            Optional[List[str]],
            Field(
                description="New tags (if updating)",
                default=None,
                examples=[["updated", "revised", "quantum"]]
            )
        ] = None
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
    return core_memory_service.update_memory(memory_id=memory_id, content=content, topic=topic, tags=tags)


@mcp.tool()
def memory_list_topics() -> List[dict]:
    """List all available topics/knowledge domains in the memory system.
    
    Returns:
        List[dict]: Available topics with counts and descriptions
    """
    return auxiliary_memory_service.list_topics()


@mcp.tool()
def memory_status() -> dict:
    """Get memory system status and statistics.
    
    Returns:
        dict: Statistics about memory usage, counts, etc.
    """
    return auxiliary_memory_service.get_status()


@mcp.tool()
def memory_delete(
        memory_id: Annotated[
            str,
            Field(
                description="ID of the memory item to delete",
                examples=["550e8400-e29b-41d4-a716-446655440000"]
            )
        ]
) -> dict:
    """Delete a memory item from the system.

    Args:
        memory_id: ID of the memory item to delete.

    Returns:
        dict: Status of the deletion operation.
    """
    return core_memory_service.delete_memory(memory_id=memory_id)


@mcp.tool()
def memory_summarize(
        memory_id: Annotated[
            Optional[str],
            Field(
                description="ID of the memory item to summarize",
                examples=["550e8400-e29b-41d4-a716-446655440000"]
            )
        ] = None,
        query: Annotated[
            Optional[str],
            Field(
                description="A query to find relevant memories to summarize",
                examples=["key points of quantum computing"]
            )
        ] = None,
        topic: Annotated[
            Optional[str],
            Field(
                description="A topic to find relevant memories to summarize",
                examples=["quantum_computing"]
            )
        ] = None,
        summary_type: Annotated[
            Literal["abstractive", "extractive", "query_focused"],
            Field(
                description="The type of summary to generate",
                default="abstractive",
                examples=["abstractive", "extractive", "query_focused"]
            )
        ] = "abstractive",
        length: Annotated[
            Literal["short", "medium", "detailed"],
            Field(
                description="The desired length of the summary",
                default="medium",
                examples=["short", "medium", "detailed"]
            )
        ] = "medium"
) -> dict:
    """Generate a summary of memory items.

    Args:
        memory_id: ID of a specific memory item to summarize.
        query: A query to find relevant memories to summarize.
        topic: A topic to find relevant memories to summarize.
        summary_type: The type of summary to generate ["abstractive", "extractive", "query_focused"].
        length: The desired length of the summary ["short", "medium", "detailed"].

    Returns:
        dict: The generated summary or an error message.
    """
    return auxiliary_memory_service.summarize_memory(
        memory_id=memory_id,
        query=query,
        topic=topic,
        summary_type=summary_type,
        length=length
    )


if __name__ == "__main__":
    print('Initializing memory server...')

    # Initialize the memory system on startup
    init_result = memory_initialize()
    print(f"Initialization result: {init_result['status']}")

    # Run the MCP server
    mcp.run(transport='stdio')
