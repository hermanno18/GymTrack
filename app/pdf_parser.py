"""
Best-effort heuristic parser for coach PDFs formatted like:

    Day1: Squat 4x8 @60kg; Bench Press 3x10; Row 5km
    Day2: Deadlift 3x5 @80kg; Plank 3 sets

This is intentionally forgiving, not perfect -- every result from here
flows into the program builder review screen where the user confirms or
hand-corrects it before anything is saved. If parsing finds nothing
recognizable, it returns an empty list and the caller falls back to a
blank manual-entry builder. That fallback path is the real safety net,
not this regex.
"""
import re

DAY_HEADER_RE = re.compile(r"(?im)^[ \t]*(day[ \t]*\d+[a-z]?)[ \t]*[:\-]?[ \t]*(.*)$")
SETS_REPS_RE = re.compile(r"(\d+)\s*(?:x|\*|sets?\s*of)\s*(\d+)", re.I)
SETS_ONLY_RE = re.compile(r"(\d+)\s*sets?\b", re.I)
REPS_ONLY_RE = re.compile(r"(\d+)\s*reps?\b", re.I)
WEIGHT_RE = re.compile(r"@?\s*(\d+(?:\.\d+)?)\s*(kg|lbs?)\b", re.I)
DISTANCE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(km|mi|miles|m)\b", re.I)
STRIP_CHARS_RE = re.compile(r"[@x×*,\-]+", re.I)


def parse_program_text(raw_text: str):
    """
    Returns a list of {"label": str, "exercises": [ {...} ]} dicts, or []
    if no "Day N" headers were recognizable at all.
    """
    text = (raw_text or "").replace("\r\n", "\n")
    matches = list(DAY_HEADER_RE.finditer(text))
    if not matches:
        return []

    days = []
    for i, match in enumerate(matches):
        label = match.group(1).strip().title().replace(" ", " ")
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = (match.group(2) + "\n" + text[start:end]).strip()
        exercises = _parse_exercise_chunks(body)
        if exercises:
            days.append({"label": label, "exercises": exercises})
    return days


def _parse_exercise_chunks(body: str):
    chunks = re.split(r"[;\n]", body)
    exercises = []
    for chunk in chunks:
        chunk = chunk.strip(" ,.-\t")
        if not chunk:
            continue
        exercise = _parse_single_exercise(chunk, order_index=len(exercises))
        if exercise:
            exercises.append(exercise)
    return exercises


def _parse_single_exercise(chunk: str, order_index: int):
    sets = reps = weight_kg = distance_km = None

    sets_reps = SETS_REPS_RE.search(chunk)
    if sets_reps:
        sets, reps = int(sets_reps.group(1)), int(sets_reps.group(2))
    else:
        sets_match = SETS_ONLY_RE.search(chunk)
        if sets_match:
            sets = int(sets_match.group(1))
        reps_match = REPS_ONLY_RE.search(chunk)
        if reps_match:
            reps = int(reps_match.group(1))

    weight_match = WEIGHT_RE.search(chunk)
    if weight_match:
        value, unit = float(weight_match.group(1)), weight_match.group(2).lower()
        weight_kg = value if unit == "kg" else round(value * 0.45359237, 3)

    distance_match = DISTANCE_RE.search(chunk)
    if distance_match:
        value, unit = float(distance_match.group(1)), distance_match.group(2).lower()
        if unit == "km":
            distance_km = value
        elif unit in ("mi", "miles"):
            distance_km = round(value * 1.609344, 3)
        elif unit == "m":
            distance_km = round(value / 1000, 4)

    name = chunk
    for pattern in (SETS_REPS_RE, WEIGHT_RE, DISTANCE_RE, SETS_ONLY_RE, REPS_ONLY_RE):
        name = pattern.sub(" ", name)
    name = STRIP_CHARS_RE.sub(" ", name)
    name = re.sub(r"\s+", " ", name).strip()

    if not name:
        return None

    return {
        "name": name,
        "sets": sets,
        "reps": reps,
        "weight_kg": weight_kg,
        "distance_km": distance_km,
        "order_index": order_index,
    }
