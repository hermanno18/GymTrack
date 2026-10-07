"""
Best-effort parser for coach PDFs, built against real-world messiness
rather than a tidy single-line format.

Real coach PDFs (see the sample this was built against) look like:

    DAY 1 -- Upper Body + Running
    1. Warm-up -- 10-15 minutes
    (bullet list of warm-up notes -- not exercises, deliberately skipped)
    2. Strength
    Dumbbell or Barbell Bench Press
    3 x 12
    Lat Pulldown
    3 x 12
    3. Running -- 20-30 minutes
    (narrative paragraphs -- deliberately skipped)
    4. HYROX-Style Conditioning -- 3 Rounds
    500 m Row
    10-15 Kettlebell Swings

So instead of treating every line as a candidate exercise, this looks for
two specific structural patterns:

  1. "Name" line immediately followed by a "3 x 12" style line, anywhere
     in a day (covers standard strength blocks and one-off entries like
     "Farmer's Carry").
  2. Inside a subsection whose heading mentions "conditioning"/"circuit"/
     "round" (HYROX-style formats), single lines like "500 m Row" or
     "10-15 Kettlebell Swings" -- quantity + name on one line.

Bulleted lines (warm-up/cool-down notes) and plain narrative sentences
never match either pattern, so they're correctly left out. Anything this
still gets wrong is fixable on the review screen, or the user can just
build the program manually -- that fallback is the real safety net, not
this parser.
"""
import re

DAY_HEADER_RE = re.compile(r"(?im)^[ \t]*day[ \t]*(\d+)[ \t]*[:\-\u2013\u2014]?[ \t]*(.*)$")
SUBSECTION_RE = re.compile(r"^[ \t]*\d+\.[ \t]*(.*)$")
BULLET_RE = re.compile(r"^[ \t]*[\u25cf\u2022*\-][ \t]*")

SETS_REPS_LINE_RE = re.compile(
    r"^[ \t]*(\d+)[ \t]*[x\u00d7][ \t]*(\d+(?:[\u2013\-]\d+)?)"
    r"[ \t]*(seconds?|secs?|minutes?|mins?)?"
    r"[ \t]*(each[ \t]+(side|leg|arm))?[ \t]*$",
    re.I,
)
QUANTITY_NAME_LINE_RE = re.compile(
    r"^[ \t]*(\d+(?:[\u2013\-]\d+)?)\s+"
    r"(?:(m|km|meters?|min|mins?|minutes?|sec|secs?|seconds?)\s+)?"
    r"([A-Za-z][A-Za-z'\- ]*)$",
    re.I,
)
CIRCUIT_SECTION_HINT_RE = re.compile(r"conditioning|circuit|round", re.I)
KG_PER_LB = 0.45359237


def parse_program_text(raw_text: str):
    """Returns [{"label": str, "exercises": [...]}], or [] if no day headers found."""
    text = (raw_text or "").replace("\r\n", "\n")
    lines = text.split("\n")

    day_starts = [
        (i, m) for i, line in enumerate(lines)
        for m in [DAY_HEADER_RE.match(line)] if m
    ]
    if not day_starts:
        return []

    days = []
    for idx, (line_no, match) in enumerate(day_starts):
        label = f"Day {match.group(1)}"
        title = match.group(2).strip()
        if title:
            label = f"{label} - {title}"
        end_line = day_starts[idx + 1][0] if idx + 1 < len(day_starts) else len(lines)
        day_lines = lines[line_no + 1:end_line]
        exercises = _parse_day_lines(day_lines)
        if exercises:
            days.append({"label": label, "exercises": exercises})
    return days


def _parse_day_lines(day_lines):
    exercises = []
    consumed = set()

    _extract_name_plus_target_pairs(day_lines, consumed, exercises)
    _extract_circuit_quantity_lines(day_lines, consumed, exercises)

    for order_index, exercise in enumerate(exercises):
        exercise["order_index"] = order_index
    return exercises


def _extract_name_plus_target_pairs(day_lines, consumed, exercises):
    for i in range(len(day_lines) - 1):
        if i in consumed or (i + 1) in consumed:
            continue
        name_line = day_lines[i].strip()
        target_line = day_lines[i + 1].strip()
        if not name_line or BULLET_RE.match(name_line) or SUBSECTION_RE.match(name_line):
            continue
        target_match = SETS_REPS_LINE_RE.match(target_line)
        if not target_match:
            continue

        exercises.append(_build_exercise_from_pair(name_line, target_match))
        consumed.add(i)
        consumed.add(i + 1)


def _build_exercise_from_pair(name_line, target_match):
    sets = int(target_match.group(1))
    reps_raw, unit, side = target_match.group(2), target_match.group(3), target_match.group(5)

    reps = None
    notes_parts = []
    if unit:  # time-based target (e.g. "30-60 seconds") -- not a rep count
        notes_parts.append(f"{reps_raw} {unit}")
    else:
        reps = int(re.split(r"[\u2013\-]", reps_raw)[0])
    if side:
        notes_parts.append(f"each {side}")

    return {
        "name": name_line,
        "sets": sets,
        "reps": reps,
        "weight_kg": None,
        "distance_km": None,
        "notes": "; ".join(notes_parts) or None,
    }


def _extract_circuit_quantity_lines(day_lines, consumed, exercises):
    in_circuit_section = False
    for i, raw_line in enumerate(day_lines):
        line = raw_line.strip()
        if not line:
            continue

        subsection = SUBSECTION_RE.match(line)
        if subsection:
            in_circuit_section = bool(CIRCUIT_SECTION_HINT_RE.search(subsection.group(1)))
            continue

        if i in consumed or not in_circuit_section or BULLET_RE.match(line):
            continue

        quantity_match = QUANTITY_NAME_LINE_RE.match(line)
        if not quantity_match:
            continue

        exercises.append(_build_exercise_from_quantity_line(quantity_match))
        consumed.add(i)


def _build_exercise_from_quantity_line(match):
    quantity_raw, unit, name = match.group(1), match.group(2), match.group(3).strip()
    first_number = float(re.split(r"[\u2013\-]", quantity_raw)[0])
    unit = (unit or "").lower()

    reps = distance_km = None
    notes = None
    if unit in ("m", "meters", "meter"):
        distance_km = round(first_number / 1000, 4)
    elif unit == "km":
        distance_km = first_number
    elif unit in ("min", "mins", "minutes", "sec", "secs", "seconds"):
        notes = f"{quantity_raw} {unit}"
    else:
        reps = int(first_number)

    return {
        "name": name,
        "sets": None,
        "reps": reps,
        "weight_kg": None,
        "distance_km": distance_km,
        "notes": notes,
    }
