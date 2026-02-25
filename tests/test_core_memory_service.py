# Enable test mode to use separate test database
import os

os.environ["TEST_MODE"] = "1"

import sys

# Get the absolute path to the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest

from memory_service.core_memory_service import (
    delete_memory,
    initialize_memory,
    retrieve_memory,
    store_memory,
    update_memory,
)

_MEMORY_STR = (
    "Mind uploading is a speculative process of whole brain emulation in which a brain scan "
    "is used to completely emulate the mental state of the individual in a digital computer. "
    "The computer would then run a simulation of the brain's information processing, such that "
    "it would respond in essentially the same way as the original brain and experience having "
    "a sentient conscious mind."
)


@pytest.fixture
def store_result():
    """Store a test memory in a fresh DB and return the store response."""
    initialize_memory(reset=True)
    wordlist = _MEMORY_STR.split(" ")
    topic = wordlist[0]
    tags = [topic, wordlist[1], wordlist[2]]
    result = store_memory(content=_MEMORY_STR, topic=topic, tags=tags)
    assert result["status"] == "success", f"Fixture failed to store memory: {result}"
    return result


def test_initialization():
    result = initialize_memory(reset=False)
    assert result["status"] == "success", f"initialize without reset failed: {result}"

    result = initialize_memory(reset=True)
    assert result["status"] == "success", f"initialize with reset failed: {result}"


def test_store_memory():
    initialize_memory(reset=True)
    wordlist = _MEMORY_STR.split(" ")
    topic = wordlist[0]
    tags = [topic, wordlist[1], wordlist[2]]

    result = store_memory(content=_MEMORY_STR, topic=topic, tags=tags)

    assert result["status"] == "success", f"store_memory failed: {result.get('message')}"
    assert "memory_id" in result


def test_retrieve_memory(store_result):
    memory_id = store_result["memory_id"]
    topic = store_result["topic"]

    results = retrieve_memory(query=topic, max_results=1, topic=None, return_type="both")

    assert len(results) > 0, "retrieve_memory returned no results"
    assert (
        results[0]["id"] == memory_id
    ), f"Retrieved wrong memory: {results[0]['id']} != {memory_id}"


def test_update_memory(store_result):
    memory_id = store_result["memory_id"]

    new_content = (
        "Substantial mainstream research in related areas is being conducted in neuroscience "
        "and computer science, including animal brain mapping and simulation."
    )
    result = update_memory(memory_id=memory_id, content=new_content)
    assert result["status"] == "success", f"update content failed: {result.get('message')}"

    wordlist = new_content.split(" ")
    new_topic = wordlist[0]
    new_tags = [new_topic, wordlist[1], wordlist[2]]
    result = update_memory(memory_id=memory_id, topic=new_topic, tags=new_tags)
    assert result["status"] == "success", f"update topic/tags failed: {result.get('message')}"

    result = update_memory(memory_id="non_existent_id", content="Invalid update")
    assert result["status"] != "success", "Expected failure for non-existent memory_id"


def test_delete_memory(store_result):
    memory_id = store_result["memory_id"]

    result = delete_memory(memory_id=memory_id)
    assert result["status"] == "success", f"delete_memory failed: {result.get('message')}"

    result = delete_memory(memory_id="non_existent_id")
    assert result["status"] != "success", "Expected failure for non-existent memory_id"


def test_size_based_summarization():
    initialize_memory(reset=True)

    # Tiny content (<500 chars) — should use content directly, no LLM call
    tiny_content = "User prefers snake_case for variable names"
    result = store_memory(content=tiny_content, topic="preferences", tags=["coding_style"])

    assert result["status"] == "success", f"store tiny content failed: {result.get('message')}"
    assert result.get("content_size", 0) < 500
    assert result.get("summary", {}).get("summary_type") == "direct_tiny"
    assert result.get("summary", {}).get("summary_generated")

    # Small content (500–2000 chars) — extractive/short
    small_content = (
        "Quantum computing is a rapidly evolving field that leverages quantum mechanics principles "
        "to perform computations. Unlike classical computers that use bits, quantum computers use "
        "qubits which can exist in superposition. This allows them to process multiple states "
        "simultaneously, potentially solving certain problems exponentially faster than classical "
        "computers. Key applications include cryptography, drug discovery, and optimization problems. "
        "However, building stable quantum computers remains challenging due to decoherence and error rates."
    )
    result = store_memory(content=small_content, topic="quantum_computing", tags=["technology"])

    assert result["status"] == "success", f"store small content failed: {result.get('message')}"
    assert 500 <= result.get("content_size", 0) < 2000
    assert result.get("summary", {}).get("summary_type") == "extractive_short"

    # Large content (>=2000 chars) — abstractive/medium
    large_content = """
    Mind uploading is a speculative process of whole brain emulation in which a brain scan is used
    to completely emulate the mental state of the individual in a digital computer. The computer would
    then run a simulation of the brain's information processing, such that it would respond in essentially
    the same way as the original brain and experience having a sentient conscious mind.

    The fundamental premise of mind uploading relies on the philosophical assumption that consciousness
    and personal identity are substrate-independent — meaning that the essence of who you are could
    theoretically exist on any sufficiently complex computational system, not just biological neurons.
    This controversial idea challenges traditional notions of what it means to be human and raises
    profound questions about the nature of consciousness itself.

    Proponents argue that mind uploading could offer a form of digital immortality, allowing human
    consciousness to persist beyond the biological limitations of the physical body. The uploaded mind
    could potentially exist in virtual environments, operate robotic bodies, or even be copied and
    distributed across multiple platforms. This could revolutionize our understanding of life, death,
    and personal identity in ways we can scarcely imagine today.

    However, significant technical and philosophical challenges remain. From a technical standpoint,
    we would need to map every neuron, synapse, and neurotransmitter in a human brain — estimated at
    around 86 billion neurons and trillions of connections. Current brain imaging technology is nowhere
    near capable of this level of detail while preserving the living brain. Additionally, we would need
    computational systems powerful enough to simulate this complexity in real-time.

    Philosophically, questions persist about whether an upload would truly be the same person or merely
    a copy. The continuity of consciousness problem asks: if your brain is scanned and simulated, is
    the digital version really you, or just a replica that thinks it's you? What happens to your
    subjective experience during the transition? These questions touch on deep issues in the philosophy
    of mind and personal identity that remain unresolved even today.
    """
    result = store_memory(content=large_content, topic="mind_uploading", tags=["neuroscience"])

    assert result["status"] == "success", f"store large content failed: {result.get('message')}"
    assert result.get("content_size", 0) >= 2000
    assert result.get("summary", {}).get("summary_type") == "abstractive_medium"


if __name__ == "__main__":
    test_initialization()
    test_store_memory()
    test_size_based_summarization()
