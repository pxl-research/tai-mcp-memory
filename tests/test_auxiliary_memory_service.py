import os

import pytest

from memory_service.auxiliary_memory_service import get_status, list_topics, summarize_memory
from memory_service.core_memory_service import initialize_memory, store_memory

memory_1 = "Mind uploading is a speculative process of whole brain emulation in which a brain scan is used to completely emulate the mental state of the individual in a digital computer. The computer would then run a simulation of the brain's information processing, such that it would respond in essentially the same way as the original brain and experience having a sentient conscious mind."
memory_2 = "Spyridon Marinatos (Greek: Σπυρίδων Μαρινάτος; 17 November [O.S. 4 November] 1901[a] – 1 October 1974) was a Greek archaeologist who specialised in the Minoan and Mycenaean civilizations of the Aegean Bronze Age. He is best known for the excavation of the Minoan site of Akrotiri on Thera,[b] which he conducted between 1967 and 1974. He received several honours in Greece and abroad, and was considered one of the most important Greek archaeologists of his day."


def _store_memory(memory_str: str) -> dict:
    wordlist = memory_str.split(" ")
    topic = wordlist[0]
    tags = [topic, wordlist[1], wordlist[2]]
    return store_memory(content=memory_str, topic=topic, tags=tags)


def test_list_topics():
    initialize_memory(reset=True)

    result = list_topics()
    assert isinstance(result, list)
    assert len(result) == 1
    assert "message" in result[0]
    assert result[0]["message"] == "No topics found"

    _store_memory(memory_1)
    _store_memory(memory_2)

    result = list_topics()
    assert isinstance(result, list)
    assert len(result) > 1


def test_get_status():
    initialize_memory(reset=True)

    result = get_status()
    assert result["status"] == "success"
    assert "stats" in result
    assert result["stats"]["total_memories"] == 0
    assert result["stats"]["total_topics"] == 0
    assert isinstance(result["stats"]["top_topics"], list)
    assert len(result["stats"]["top_topics"]) == 0

    _store_memory(memory_1)
    _store_memory(memory_2)

    result = get_status()
    assert result["status"] == "success"
    assert result["stats"]["total_memories"] >= 2
    assert result["stats"]["total_topics"] > 0
    assert len(result["stats"]["top_topics"]) > 0


@pytest.mark.skipif(
    not os.getenv("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set",
)
def test_summarize_memory():
    initialize_memory(reset=True)

    store_result = _store_memory(memory_1)
    assert (
        store_result["status"] == "success"
    ), f"store_memory failed: {store_result.get('message')}"
    memory_id = store_result["memory_id"]

    result = summarize_memory(memory_id=memory_id, summary_type="abstractive", length="medium")
    assert result["status"] == "success"
    assert "summary" in result

    result = summarize_memory(query="test memory", summary_type="query_focused", length="short")
    assert result["status"] == "success"
    assert "summary" in result

    topic = memory_1.split(" ")[0]
    result = summarize_memory(topic=topic, summary_type="extractive", length="detailed")
    assert result["status"] == "success"
    assert "summary" in result
