"""
Small, focused helpers: unit conversion, name normalization, fuzzy matching.

Everything is stored internally in kg / km. Conversion only happens at the
display/input boundary so switching a user's preferred unit never mutates
historical data.
"""
import re
import difflib

KG_PER_LB = 0.45359237
KM_PER_MI = 1.609344


def normalize_name(name: str) -> str:
    """Case/whitespace-insensitive key used to link exercise history."""
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def kg_to_display(kg, unit="kg"):
    if kg is None:
        return None
    return round(kg, 2) if unit == "kg" else round(kg / KG_PER_LB, 2)


def display_to_kg(value, unit="kg"):
    if value in (None, ""):
        return None
    value = float(value)
    return value if unit == "kg" else round(value * KG_PER_LB, 3)


def km_to_display(km, unit="km"):
    if km is None:
        return None
    return round(km, 2) if unit == "km" else round(km / KM_PER_MI, 2)


def display_to_km(value, unit="km"):
    if value in (None, ""):
        return None
    value = float(value)
    return value if unit == "km" else round(value * KM_PER_MI, 3)


def find_similar_exercise(name, existing, threshold=0.85):
    """
    existing: iterable of (id, name, name_normalized) tuples for the
    current user's other exercises.

    Returns a dict {id, name, ratio, exact} for the closest match at/above
    threshold (or an exact normalized match regardless of threshold), else
    None. Used to power the "Did you mean X?" suggestion prompt.
    """
    target = normalize_name(name)
    if not target:
        return None

    best = None
    best_ratio = 0.0
    for ex_id, ex_name, ex_norm in existing:
        if ex_norm == target:
            return {"id": ex_id, "name": ex_name, "ratio": 1.0, "exact": True}
        ratio = difflib.SequenceMatcher(None, target, ex_norm).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best = {"id": ex_id, "name": ex_name, "ratio": round(ratio, 2), "exact": False}

    return best if best and best_ratio >= threshold else None


DURATION_RE = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")


def parse_duration_to_seconds(text):
    """
    Parses 'mm:ss' or 'hh:mm:ss' into total seconds. Returns None for
    blank input. Used for how long a run/row/timed exercise actually took.
    """
    if text in (None, ""):
        return None
    text = text.strip()
    if not DURATION_RE.match(text):
        raise ValueError(f"Unrecognized duration format: {text!r}")
    parts = text.split(":")
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + int(seconds)
    hours, minutes, seconds = parts
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def format_seconds_to_duration(total_seconds):
    """Formats total seconds back into 'mm:ss' (or 'h:mm:ss' if >= 1 hour)."""
    if total_seconds is None:
        return None
    total_seconds = int(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def format_full_date(value):
    """date/datetime -> 'July 18, 2026'. Deliberately avoids strftime's
    %-d/%e (day-without-leading-zero) since that flag isn't portable
    across Windows/Linux -- this app is developed on Windows but
    deployed on Linux (WHC/cPanel)."""
    if value is None:
        return ""
    return f"{value.strftime('%B')} {value.day}, {value.year}"


def format_short_date(value):
    """date/datetime -> 'Jul 18'. Used where space is tight (chart axes)."""
    if value is None:
        return ""
    return f"{value.strftime('%b')} {value.day}"


def format_time_12h(value):
    """'HH:MM' or 'HH:MM:SS' (24h) -> '6:00 PM'. Blank/None -> ''."""
    if not value:
        return ""
    parts = value.split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    period = "AM" if hour < 12 else "PM"
    hour_12 = hour % 12 or 12
    return f"{hour_12}:{minute:02d} {period}"


def format_full_datetime(date_value, time_value=None):
    """Combines a date and an optional 'HH:MM' time into
    'July 18, 2026 at 6:00 PM' (or just the date if no time given)."""
    full_date = format_full_date(date_value)
    if not time_value:
        return full_date
    return f"{full_date} at {format_time_12h(time_value)}"
