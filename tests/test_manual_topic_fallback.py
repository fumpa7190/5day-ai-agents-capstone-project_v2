from services.curriculum_store import get_store


def test_manual_topic_near_miss_suggests_match():
    store = get_store()
    match = store.match_selection(grade=9, subject="Mathematics", manual_topic="Linear Relation")
    assert match.match_status == "suggested"
    assert any(s.topic == "Linear Relations" for s in match.suggestions)


def test_manual_topic_nonsense_is_custom():
    store = get_store()
    match = store.match_selection(grade=9, subject="Mathematics", manual_topic="Underwater basket weaving")
    assert match.match_status == "custom"
    assert match.curriculum_record is None


def test_force_custom_skips_suggestion():
    store = get_store()
    match = store.match_selection(
        grade=9, subject="Mathematics", manual_topic="Linear Relation", force_custom=True
    )
    assert match.match_status == "custom"
    assert match.suggestions == []


def test_manual_topic_exact_match_is_case_insensitive():
    store = get_store()
    match = store.match_selection(grade=9, subject="Mathematics", manual_topic="linear relations")
    assert match.match_status == "exact"
    assert match.record_id == "png_math_g9_9_3_3_3"
