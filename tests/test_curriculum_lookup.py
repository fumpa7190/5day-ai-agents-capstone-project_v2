from services.curriculum_store import get_store


def test_exact_topic_match_via_dropdown():
    store = get_store()
    match = store.match_selection(grade=9, subject="Mathematics", topic="Linear Relations")
    assert match.match_status == "exact"
    assert match.record_id == "png_math_g9_9_3_3_3"
    assert match.curriculum_record["benchmark_code"] == "9.3.3.3"


def test_lookup_by_benchmark_code_via_get_record():
    store = get_store()
    record_id = store.indexes["by_benchmark_code"]["9.1.1.1"]
    record = store.get_record(record_id)
    assert record["topic"] == "Factors, Multiples, Primes and Composites"


def test_get_selection_tree_has_all_strands():
    store = get_store()
    tree = store.get_selection_tree()
    strands = tree["9"]["Mathematics"].keys()
    assert "Patterns and Algebra" in strands
    assert "Statistics and Probability" in strands


def test_unknown_topic_without_manual_fallback_is_custom():
    store = get_store()
    match = store.match_selection(grade=9, subject="Mathematics", topic="Not A Real Topic")
    assert match.match_status == "custom"
