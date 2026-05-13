from __future__ import annotations

import re
from calendar import month_name, monthrange
from datetime import date, timedelta

_WEEKDAYS = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
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

_NUMBERS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
}


def _normalize(text: str) -> str:
    text = text.strip().lower()
    text = text.replace(",", "").replace(".", "")
    text = re.sub(r"(?<=[a-z])-", " ", text)
    text = re.sub(r"\bof\b", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _strip_ordinal_suffixes(text: str) -> str:
    return re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", text)


def _to_int(value: str) -> int:
    value = value.strip().lower()

    if value.isdigit():
        return int(value)

    if value in _NUMBERS:
        return _NUMBERS[value]

    parts = value.split()
    if len(parts) == 2 and parts[0] in _NUMBERS and parts[1] in _NUMBERS:
        return _NUMBERS[parts[0]] + _NUMBERS[parts[1]]

    raise ValueError(f"Unknown number: {value!r}")


def _add_months(value: date, months: int) -> date:
    year = value.year + (value.month - 1 + months) // 12
    month = (value.month - 1 + months) % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def _add_years(value: date, years: int) -> date:
    return _add_months(value, years * 12)


def _shift(value: date, amount: int, unit: str) -> date:
    if unit.startswith("day"):
        return value + timedelta(days=amount)

    if unit.startswith("week"):
        return value + timedelta(weeks=amount)

    if unit.startswith("month"):
        return _add_months(value, amount)

    if unit.startswith("year"):
        return _add_years(value, amount)

    raise ValueError(f"Unknown unit: {unit!r}")


def _shift_weekday(reference: date, target_weekday: int, direction: int) -> date:
    if direction > 0:
        delta = (target_weekday - reference.weekday()) % 7
        return reference + timedelta(days=delta or 7)

    delta = (reference.weekday() - target_weekday) % 7
    return reference - timedelta(days=delta or 7)


def _parse_duration(text: str) -> list[tuple[int, str]]:
    number_pattern = (
        r"\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
        r"twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|"
        r"nineteen|twenty|thirty|twenty one|twenty two|twenty three|"
        r"twenty four|twenty five|twenty six|twenty seven|twenty eight|"
        r"twenty nine|thirty one"
    )

    unit_pattern = r"days?|weeks?|months?|years?"
    pattern = rf"({number_pattern}) ({unit_pattern})"

    matches = re.findall(pattern, text)
    if not matches:
        raise ValueError(f"Could not parse duration: {text!r}")

    consumed = re.sub(pattern, "", text)
    consumed = consumed.replace("and", "").strip()

    if consumed:
        raise ValueError(f"Could not parse duration: {text!r}")

    return [(_to_int(amount), unit) for amount, unit in matches]


def _apply_duration(base: date, duration: list[tuple[int, str]], sign: int) -> date:
    result = base
    for amount, unit in duration:
        result = _shift(result, sign * amount, unit)
    return result


def _parse_absolute(text: str, today: date) -> date | None:
    text = _strip_ordinal_suffixes(text)

    if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", text):
        year, month, day = map(int, text.split("-"))
        return date(year, month, day)

    if re.fullmatch(r"\d{4}/\d{1,2}/\d{1,2}", text):
        year, month, day = map(int, text.split("/"))
        return date(year, month, day)

    if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", text):
        month, day, year = map(int, text.split("/"))
        return date(year, month, day)

    parts = text.split()

    if len(parts) in {2, 3} and parts[0] in _MONTHS and parts[1].isdigit():
        month = _MONTHS[parts[0]]
        day = int(parts[1])
        year = int(parts[2]) if len(parts) == 3 else today.year
        return date(year, month, day)

    if len(parts) == 3 and parts[0].isdigit() and parts[1] in _MONTHS:
        day = int(parts[0])
        month = _MONTHS[parts[1]]
        year = int(parts[2])
        return date(year, month, day)

    return None


def parse(s: str, today: date | None = None) -> date:
    if today is None:
        today = date.today()

    text = _normalize(s)

    if not text:
        raise ValueError("Could not parse date: empty input")

    if text in {"now", "today"}:
        return today

    if text == "tomorrow":
        return today + timedelta(days=1)

    if text == "yesterday":
        return today - timedelta(days=1)

    absolute = _parse_absolute(text, today)
    if absolute is not None:
        return absolute

    weekday_match = re.fullmatch(r"(next|last|this)? ?([a-z]+)", text)
    if weekday_match is not None:
        modifier, weekday_name = weekday_match.groups()
        if weekday_name in _WEEKDAYS:
            target = _WEEKDAYS[weekday_name]

            if modifier == "last":
                return _shift_weekday(today, target, -1)

            if modifier == "next":
                return _shift_weekday(today, target, 1)

            delta = (target - today.weekday()) % 7
            return today + timedelta(days=delta)

    relative_match = re.fullmatch(r"in (.+)", text)
    if relative_match is not None:
        duration = _parse_duration(relative_match.group(1))
        return _apply_duration(today, duration, 1)

    relative_match = re.fullmatch(r"(.+) ago", text)
    if relative_match is not None:
        duration = _parse_duration(relative_match.group(1))
        return _apply_duration(today, duration, -1)

    relative_match = re.fullmatch(r"(.+) (from|after) (.+)", text)
    if relative_match is not None:
        duration_text, _, base_text = relative_match.groups()
        duration = _parse_duration(duration_text)
        base = today if base_text in {"now", "today"} else parse(base_text, today)
        return _apply_duration(base, duration, 1)

    relative_match = re.fullmatch(r"(.+) before (.+)", text)
    if relative_match is not None:
        duration_text, base_text = relative_match.groups()
        duration = _parse_duration(duration_text)
        base = today if base_text in {"now", "today"} else parse(base_text, today)
        return _apply_duration(base, duration, -1)

    raise ValueError(f"Could not parse date: {s!r}")
