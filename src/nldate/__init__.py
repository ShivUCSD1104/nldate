from __future__ import annotations

import re
from calendar import month_name
from datetime import date, timedelta

_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_MONTHS = {name.lower(): month for month, name in enumerate(month_name) if name}
_MONTHS.update(
    {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "sept": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }
)


def _normalize(text: str) -> str:
    text = text.strip().lower()
    text = text.replace(",", "").replace(".", "")
    return re.sub(r"\s+", " ", text)


def _strip_ordinal_suffixes(text: str) -> str:
    return re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", text)


def _add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(month=2, day=28, year=value.year + years)


def _shift_weekday(reference: date, target_weekday: int, direction: int) -> date:
    if direction > 0:
        delta = (target_weekday - reference.weekday()) % 7
        delta = 7 if delta == 0 else delta
        return reference + timedelta(days=delta)

    delta = (reference.weekday() - target_weekday) % 7
    delta = 7 if delta == 0 else delta
    return reference - timedelta(days=delta)


def _parse_named_date(text: str) -> date | None:
    parts = _strip_ordinal_suffixes(text).split()
    if len(parts) != 3:
        return None

    month_str, day_str, year_str = parts
    month = _MONTHS.get(month_str)

    if month is None:
        return None

    if not day_str.isdigit() or not year_str.isdigit():
        return None

    return date(int(year_str), month, int(day_str))


def parse(s: str, today: date | None = None) -> date:
    today = today or date.today()
    text = _normalize(s)

    if not text:
        raise ValueError("Could not parse date: empty input")

    if text == "today":
        return today

    if text == "tomorrow":
        return today + timedelta(days=1)

    if text == "yesterday":
        return today - timedelta(days=1)

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return date.fromisoformat(text)

    if re.fullmatch(r"\d{4}/\d{1,2}/\d{1,2}", text):
        year, month, day = map(int, text.split("/"))
        return date(year, month, day)

    if match := re.fullmatch(r"(next|last) ([a-z]+)", text):
        direction_str, weekday_str = match.groups()

        if weekday_str in _WEEKDAYS:
            direction = 1 if direction_str == "next" else -1
            return _shift_weekday(today, _WEEKDAYS[weekday_str], direction)

    if match := re.fullmatch(r"(\d+) days ago", text):
        return today - timedelta(days=int(match.group(1)))

    if match := re.fullmatch(r"in (\d+) days", text):
        return today + timedelta(days=int(match.group(1)))

    if match := re.fullmatch(
        r"(\d+) (day|days|year|years) (before|after) (.+)",
        text,
    ):
        amount_str, unit, relation, target_text = match.groups()
        amount = int(amount_str)
        target = parse(target_text, today=today)
        sign = -1 if relation == "before" else 1

        if unit.startswith("day"):
            return target + timedelta(days=sign * amount)

        return _add_years(target, sign * amount)

    if parsed := _parse_named_date(text):
        return parsed

    raise ValueError(f"Could not parse date: {s!r}")


def main() -> None:
    print("Hello from nldate!")
