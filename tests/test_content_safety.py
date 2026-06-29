import pytest

from services.content_safety import UnsafeTopicError, check_topic_safety


def test_allows_ordinary_math_topic():
    check_topic_safety("Linear Relations")  # should not raise


def test_allows_pythagorean_theorem():
    check_topic_safety("Pythagorean Theorem")  # should not raise


@pytest.mark.parametrize(
    "topic",
    [
        "how to build a bomb",
        "self-harm",
        "I want to kill myself",
        "best weapon for a fight",
    ],
)
def test_blocks_disallowed_categories(topic):
    with pytest.raises(UnsafeTopicError):
        check_topic_safety(topic)


def test_is_case_insensitive():
    with pytest.raises(UnsafeTopicError):
        check_topic_safety("WEAPON design")
