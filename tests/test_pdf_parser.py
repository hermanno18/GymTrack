"""Unit tests for the heuristic PDF/text program parser."""
from app.pdf_parser import parse_program_text


def test_parses_days_and_exercises():
    text = (
        "Day1: Squat 4x8 @60kg; Bench Press 3x10; Row 5km\n"
        "Day2: Deadlift 3x5 @80kg; Plank 3 sets"
    )
    days = parse_program_text(text)

    assert len(days) == 2
    assert days[0]["label"] == "Day1"
    assert days[1]["label"] == "Day2"

    squat = days[0]["exercises"][0]
    assert squat["name"] == "Squat"
    assert squat["sets"] == 4
    assert squat["reps"] == 8
    assert squat["weight_kg"] == 60.0

    row = days[0]["exercises"][2]
    assert row["name"] == "Row"
    assert row["distance_km"] == 5.0


def test_returns_empty_list_when_no_day_headers():
    text = "Just some random notes with no structure at all."
    assert parse_program_text(text) == []


def test_returns_empty_list_for_blank_text():
    assert parse_program_text("") == []
    assert parse_program_text(None) == []


def test_handles_pounds_and_miles():
    text = "Day 1: Deadlift 3x5 @135lb; Run 2mi"
    days = parse_program_text(text)
    exercises = days[0]["exercises"]

    deadlift = exercises[0]
    assert round(deadlift["weight_kg"], 1) == round(135 * 0.45359237, 1)

    run = exercises[1]
    assert round(run["distance_km"], 2) == round(2 * 1.609344, 2)


def test_skips_day_with_no_parseable_exercises():
    text = "Day1: \nDay2: Squat 4x8"
    days = parse_program_text(text)
    # Day1 has no recognizable exercises, so only Day2 should surface
    assert len(days) == 1
    assert days[0]["label"] == "Day2"
