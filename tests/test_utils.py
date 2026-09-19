"""Unit tests for unit conversion, name normalization, and fuzzy matching."""
from app.utils import (
    normalize_name, kg_to_display, display_to_kg,
    km_to_display, display_to_km, find_similar_exercise,
    parse_duration_to_seconds, format_seconds_to_duration,
)


def test_normalize_name_trims_and_lowercases():
    assert normalize_name("  Bench   Press  ") == "bench press"
    assert normalize_name("BENCH PRESS") == "bench press"
    assert normalize_name("Bench Press") == normalize_name("bench press")


def test_normalize_name_handles_empty():
    assert normalize_name("") == ""
    assert normalize_name(None) == ""


def test_weight_round_trip_kg():
    assert kg_to_display(60.0, "kg") == 60.0
    assert display_to_kg("60", "kg") == 60.0


def test_weight_round_trip_lb():
    kg_value = display_to_kg("100", "lb")
    assert round(kg_value, 2) == 45.36
    back_to_lb = kg_to_display(kg_value, "lb")
    assert round(back_to_lb) == 100


def test_distance_round_trip_km():
    assert km_to_display(5.0, "km") == 5.0
    assert display_to_km("5", "km") == 5.0


def test_distance_round_trip_miles():
    km_value = display_to_km("1", "mi")
    assert round(km_value, 3) == 1.609
    back_to_mi = km_to_display(km_value, "mi")
    assert round(back_to_mi, 1) == 1.0


def test_none_and_blank_values_convert_to_none():
    assert display_to_kg(None, "kg") is None
    assert display_to_kg("", "lb") is None
    assert display_to_km(None, "km") is None
    assert kg_to_display(None, "kg") is None


def test_find_similar_exercise_exact_match():
    existing = [(1, "Bench Press", "bench press")]
    match = find_similar_exercise("bench press", existing)
    assert match["exact"] is True
    assert match["id"] == 1


def test_find_similar_exercise_near_typo():
    existing = [(1, "Bench Press", "bench press")]
    match = find_similar_exercise("Bench Pres", existing, threshold=0.85)
    assert match is not None
    assert match["exact"] is False
    assert match["name"] == "Bench Press"


def test_find_similar_exercise_no_match_below_threshold():
    existing = [(1, "Bench Press", "bench press")]
    match = find_similar_exercise("Deadlift", existing, threshold=0.85)
    assert match is None


def test_find_similar_exercise_empty_existing_list():
    assert find_similar_exercise("Squat", [], threshold=0.85) is None


def test_parse_duration_mmss():
    assert parse_duration_to_seconds("24:30") == 24 * 60 + 30


def test_parse_duration_hhmmss():
    assert parse_duration_to_seconds("1:05:00") == 3600 + 5 * 60


def test_parse_duration_blank_returns_none():
    assert parse_duration_to_seconds("") is None
    assert parse_duration_to_seconds(None) is None


def test_parse_duration_rejects_garbage():
    import pytest
    with pytest.raises(ValueError):
        parse_duration_to_seconds("not a time")


def test_format_seconds_to_duration_under_an_hour():
    assert format_seconds_to_duration(1470) == "24:30"


def test_format_seconds_to_duration_over_an_hour():
    assert format_seconds_to_duration(3900) == "1:05:00"


def test_format_seconds_to_duration_none():
    assert format_seconds_to_duration(None) is None


def test_duration_round_trip():
    seconds = parse_duration_to_seconds("5:09")
    assert format_seconds_to_duration(seconds) == "5:09"
