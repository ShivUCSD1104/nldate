from datetime import date

import pytest

from nldate import parse

TODAY = date(2025, 11, 20)


def test_today() -> None:
    assert parse("today", TODAY) == TODAY


def test_tomorrow() -> None:
    assert parse("tomorrow", TODAY) == date(2025, 11, 21)


def test_yesterday() -> None:
    assert parse("yesterday", TODAY) == date(2025, 11, 19)


def test_next_tuesday() -> None:
    assert parse("next tuesday", TODAY) == date(2025, 11, 25)


def test_last_monday() -> None:
    assert parse("last monday", TODAY) == date(2025, 11, 17)


def test_days_ago() -> None:
    assert parse("5 days ago", TODAY) == date(2025, 11, 15)


def test_in_days() -> None:
    assert parse("in 3 days", TODAY) == date(2025, 11, 23)


def test_before_date() -> None:
    assert parse(
        "5 days before december 1st 2025",
        TODAY,
    ) == date(2025, 11, 26)


def test_after_yesterday() -> None:
    assert parse(
        "1 year after yesterday",
        TODAY,
    ) == date(2026, 11, 19)


def test_iso_date() -> None:
    assert parse("2025-12-01", TODAY) == date(2025, 12, 1)


def test_invalid() -> None:
    with pytest.raises(ValueError):
        parse("banana", TODAY)
