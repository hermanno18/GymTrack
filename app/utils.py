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
