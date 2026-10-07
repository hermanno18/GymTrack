"""
Unit tests for the day/exercise text parser -- built directly against the
real sample PDF text ("My 2-Day Gym Programme For Hermann") rather than
an invented format, since that's what actually needs to work.
"""
from app.pdf_parser import parse_program_text

# Trimmed-but-faithful excerpt of the real PDF's extracted text (pdfplumber
# output), covering both days' key structural patterns: bullet warm-ups,
# "Name" + "3 x 12" strength pairs, narrative running instructions, and a
# HYROX-style circuit block with quantity+name lines.
SAMPLE_TEXT = """My 2-Day Gym Programme For Hermann
My Goals
\u25cf Build strength
Training: 2 days per week
DAY 1 \u2014 Upper Body + Running
1. Warm-up \u2014 10-15 minutes
\u25cf 5-10 minutes easy treadmill jogging
\u25cf Arm circles x 10 each direction
Start easy and gradually increase the intensity.
2. Strength
Dumbbell or Barbell Bench Press
3 x 12
Lat Pulldown
3 x 12
Seated Cable Row
3 x 12
3. Running \u2014 20-30 minutes
Run at a comfortable, sustainable pace.
If 20-30 minutes of continuous running is difficult, I can use:
3 minutes running + 1 minute walking
4. Cool-down \u2014 5-10 minutes
\u25cf Easy walking
\u25cf Gentle stretching
DAY 2 \u2014 Full Body + HYROX
3. Farmer's Carry
Farmer's Carry
3 x 30-60 seconds
4. HYROX-Style Conditioning \u2014 3 Rounds
Complete:
500 m Row
10-15 Kettlebell Swings
10-15 Burpees
2-3 Minutes Incline Treadmill Walk
400 m Run
Rest: 1-2 minutes between rounds if needed.
"""


def test_finds_both_days():
    days = parse_program_text(SAMPLE_TEXT)
    assert len(days) == 2
    assert days[0]["label"].startswith("Day 1")
    assert days[1]["label"].startswith("Day 2")


def test_extracts_strength_pairs_not_warmup_bullets():
    days = parse_program_text(SAMPLE_TEXT)
    day1_names = [ex["name"] for ex in days[0]["exercises"]]

    assert "Dumbbell or Barbell Bench Press" in day1_names
    assert "Lat Pulldown" in day1_names
    assert "Seated Cable Row" in day1_names

    # Warm-up bullets and narrative sentences must NOT become exercises
    assert not any("treadmill jogging" in n for n in day1_names)
    assert not any("Start easy" in n for n in day1_names)
    assert not any("Run at a comfortable" in n for n in day1_names)
    assert not any("running + 1 minute walking" in n for n in day1_names)


def test_strength_pair_captures_sets_and_reps():
    days = parse_program_text(SAMPLE_TEXT)
    bench = next(ex for ex in days[0]["exercises"] if ex["name"] == "Dumbbell or Barbell Bench Press")
    assert bench["sets"] == 3
    assert bench["reps"] == 12


def test_time_based_target_goes_to_notes_not_reps():
    days = parse_program_text(SAMPLE_TEXT)
    farmers_carry = next(ex for ex in days[1]["exercises"] if ex["name"] == "Farmer's Carry")
    assert farmers_carry["sets"] == 3
    assert farmers_carry["reps"] is None
    assert "30-60 seconds" in farmers_carry["notes"]


def test_hyrox_circuit_quantity_lines_captured():
    days = parse_program_text(SAMPLE_TEXT)
    day2_names = [ex["name"] for ex in days[1]["exercises"]]
    assert "Row" in day2_names
    assert "Kettlebell Swings" in day2_names
    assert "Burpees" in day2_names
    assert "Run" in day2_names


def test_hyrox_distance_lines_convert_to_km():
    days = parse_program_text(SAMPLE_TEXT)
    row = next(ex for ex in days[1]["exercises"] if ex["name"] == "Row")
    assert row["distance_km"] == 0.5
    run = next(ex for ex in days[1]["exercises"] if ex["name"] == "Run")
    assert run["distance_km"] == 0.4


def test_hyrox_rep_range_uses_first_number():
    days = parse_program_text(SAMPLE_TEXT)
    swings = next(ex for ex in days[1]["exercises"] if ex["name"] == "Kettlebell Swings")
    assert swings["reps"] == 10


def test_hyrox_time_based_line_goes_to_notes():
    days = parse_program_text(SAMPLE_TEXT)
    walk = next(ex for ex in days[1]["exercises"] if "Treadmill Walk" in ex["name"])
    assert walk["reps"] is None
    assert walk["distance_km"] is None
    assert "minutes" in walk["notes"]


def test_running_narrative_line_does_not_leak_into_circuit_section():
    days = parse_program_text(SAMPLE_TEXT)
    day2_names = [ex["name"] for ex in days[1]["exercises"]]
    assert not any("Rest" in n for n in day2_names)


def test_returns_empty_list_when_no_day_headers():
    assert parse_program_text("Just some random notes with no structure at all.") == []


def test_returns_empty_list_for_blank_text():
    assert parse_program_text("") == []
    assert parse_program_text(None) == []
