import os
import sys
import uuid

# Ensure project root on path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import normally
from db.sqlite_manager import SQLiteManager


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_topic_decrement_and_delete():
    db = SQLiteManager()
    # Reset DB
    db.initialize(reset=True)

    topic = "topicA"
    m1 = str(uuid.uuid4())
    m2 = str(uuid.uuid4())

    # Store two memories in same topic (count should become 2)
    assert_true(db.store_memory(m1, "content one", topic, ["a"]), "store m1 failed")
    assert_true(db.store_memory(m2, "content two", topic, ["b"]), "store m2 failed")

    topics = db.list_topics()
    t = next((x for x in topics if x["name"] == topic), None)
    assert_true(t is not None and t["item_count"] == 2, f"expected count=2, got {t}")

    # Delete one memory -> count should decrement to 1
    assert_true(db.delete_memory(m1), "delete m1 failed")
    topics = db.list_topics()
    t = next((x for x in topics if x["name"] == topic), None)
    assert_true(t is not None and t["item_count"] == 1, f"expected count=1, got {t}")

    # Delete last memory -> topic row should be removed
    assert_true(db.delete_memory(m2), "delete m2 failed")
    topics = db.list_topics()
    t = next((x for x in topics if x["name"] == topic), None)
    assert_true(t is None, f"expected topic to be deleted, got {t}")


def test_fk_cascade_on_delete():
    db = SQLiteManager()
    db.initialize(reset=True)

    topic = "topicB"
    m = str(uuid.uuid4())
    s = str(uuid.uuid4())

    # Create memory and an attached summary
    assert_true(db.store_memory(m, "content base", topic, ["x"]), "store memory failed")
    assert_true(db.store_summary(s, m, "abstractive_medium", "summary here"), "store summary failed")

    # Delete memory -> summary should cascade delete
    assert_true(db.delete_memory(m), "delete memory failed")
    summary = db.get_summary_by_id(s)
    assert_true(summary is None, f"expected summary to cascade delete, got {summary}")


if __name__ == "__main__":
    # Run tests sequentially; raise on first failure
    test_topic_decrement_and_delete()
    print("topic decrement/delete: PASSED")
    test_fk_cascade_on_delete()
    print("fk cascade on delete: PASSED")
