"""Unit test for the Bronze client"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from energy_lakehouse.bronze import bronze_rows, chunks_to_fetch, load_window
from energy_lakehouse.smard import chunks_for_window, parse_chunk

FIXTURES = Path(__file__).parent.parent / "fixtures"

# What the caller stamps onto every row of a run. Fixed here so the asserts can
# name them exactly; SOURCE_CHUNK is the real chunk id of the saved week.
SOURCE_CHUNK = 1789336800000
LOAD_ID = "test-load"
FETCHED_AT = datetime(2026, 11, 9, tzinfo=UTC)

# Five consecutive weeks, built from a real chunk id so the dates are plausible:
# 2026-11-01 23:00 UTC is Monday 02.11 00:00 Berlin on winter time.
WEEK_MS = 7 * 24 * 60 * 60 * 1000
INDEX = [1793574000000 + week * WEEK_MS for week in range(5)]
WINDOW_START = datetime(2026, 11, 10, tzinfo=UTC)
WINDOW_END = datetime(2026, 11, 20, tzinfo=UTC)

NOW = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)

BRONZE_COLUMNS = {
    "filter_id",
    "timestamp_utc",
    "value",
    "source_chunk",
    "load_id",
    "fetched_at",
}


def load_fixture(name: str) -> dict[str, Any]:
    body: dict[str, Any] = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return body


@pytest.fixture
def rows() -> list[dict[str, Any]]:
    """One saved week of wind onshore, turned into bronze rows."""
    body = load_fixture("smard_4067_hour.json")
    return bronze_rows(
        parse_chunk(body, 4067),
        source_chunk=SOURCE_CHUNK,
        load_id=LOAD_ID,
        fetched_at=FETCHED_AT,
    )


def test_one_row_per_point(rows: list[dict[str, Any]]) -> None:
    """A weekly chunk holds 168 hourly points, so it must give 168 rows."""
    assert len(rows) == 168


def test_has_the_six_bronze_columns(rows: list[dict[str, Any]]) -> None:
    """Comparing the whole key set catches a typo, a missing and an extra column."""
    assert set(rows[0]) == BRONZE_COLUMNS


def test_first_timestamp_is_unchanged(rows: list[dict[str, Any]]) -> None:
    """Monday 00:00 Berlin in September is 22:00 UTC the evening before."""
    assert rows[0]["timestamp_utc"] == datetime(2026, 9, 13, 22, 0, tzinfo=UTC)


def test_first_value_is_unchanged(rows: list[dict[str, Any]]) -> None:
    """Bronze stores what the source sent, with no rounding or conversion."""
    assert rows[0]["value"] == 5997.52


def test_every_row_carries_the_filter_id(rows: list[dict[str, Any]]) -> None:
    assert all(row["filter_id"] == 4067 for row in rows)


def test_every_row_carries_the_source_chunk(rows: list[dict[str, Any]]) -> None:
    assert all(row["source_chunk"] == SOURCE_CHUNK for row in rows)


def test_every_row_carries_the_load_id(rows: list[dict[str, Any]]) -> None:
    """One id per run is what makes a bad number traceable back to its load."""
    assert all(row["load_id"] == LOAD_ID for row in rows)


def test_every_row_carries_fetched_at(rows: list[dict[str, Any]]) -> None:
    assert all(row["fetched_at"] == FETCHED_AT for row in rows)


def test_nulls_are_kept() -> None:
    """The saved week has no nulls, so the gap is built by hand here.

    SMARD sends null for an hour it has not published yet. Bronze keeps it as
    null; turning it into 0 would invent generation that never happened.
    """
    body: dict[str, Any] = {
        "series": [[1789336800000, 5997.52], [1789340400000, None]],
    }
    built = bronze_rows(
        parse_chunk(body, 4067),
        source_chunk=SOURCE_CHUNK,
        load_id=LOAD_ID,
        fetched_at=FETCHED_AT,
    )

    assert built[1]["value"] is None


def test_empty_input_gives_no_rows() -> None:
    """An empty series must not raise; it just contributes nothing to the table."""
    assert bronze_rows([], SOURCE_CHUNK, LOAD_ID, FETCHED_AT) == []


def test_first_run_uses_the_whole_window() -> None:
    """With no mark there is nothing to be incremental about."""
    assert chunks_to_fetch(INDEX, None, WINDOW_START, WINDOW_END) == INDEX[1:3]


def test_first_run_delegates_to_the_window_rule() -> None:
    """The overlap rule must live in one place, not be copied into this function."""
    assert chunks_to_fetch(INDEX, None, WINDOW_START, WINDOW_END) == chunks_for_window(
        INDEX, WINDOW_START, WINDOW_END
    )


def test_caught_up_fetches_only_the_newest_week() -> None:
    """The point of the step: 70 downloads a run become 5."""
    assert chunks_to_fetch(INDEX, INDEX[-1], WINDOW_START, WINDOW_END) == [INDEX[-1]]


def test_the_marked_week_is_fetched_again() -> None:
    """Its later hours were still null last time, so it is not finished with."""
    assert chunks_to_fetch(INDEX, INDEX[2], WINDOW_START, WINDOW_END)[0] == INDEX[2]


def test_every_week_after_the_mark_comes_too() -> None:
    """A run skipped for three weeks must catch up, not fetch only the newest."""
    assert chunks_to_fetch(INDEX, INDEX[2], WINDOW_START, WINDOW_END) == INDEX[2:]


def test_a_mark_that_is_not_a_chunk_id() -> None:
    """A mark one second past a week's start takes the weeks after it."""
    assert chunks_to_fetch(INDEX, INDEX[2] + 1000, WINDOW_START, WINDOW_END) == INDEX[3:]


def test_no_dates_gives_the_rolling_window() -> None:
    """The normal scheduled run: the last 90 days, ending now."""
    window = load_window(None, None, NOW, 90)

    assert window.start == NOW - timedelta(days=90)
    assert window.end == NOW
    assert window.is_backfill is False


def test_empty_strings_are_treated_as_no_dates() -> None:
    """A blank Databricks widget returns "", never None."""
    assert load_window("", "", NOW, 90).is_backfill is False


def test_both_dates_give_a_backfill() -> None:
    window = load_window("2026-01-01", "2026-01-31", NOW, 90)

    assert window.start == datetime(2026, 1, 1, tzinfo=UTC)
    assert window.is_backfill is True


def test_the_end_date_is_inclusive() -> None:
    """2026-01-31 must cover all of 31 January, so the window ends a day later."""
    assert load_window("2026-01-01", "2026-01-31", NOW, 90).end == datetime(2026, 2, 1, tzinfo=UTC)


def test_the_window_is_always_timezone_aware() -> None:
    """A naive datetime would be read as local time and shift the window silently."""
    window = load_window("2026-01-01", "2026-01-31", NOW, 90)

    assert window.start.tzinfo is not None
    assert window.end.tzinfo is not None


def test_only_a_start_date_is_rejected() -> None:
    """Loading a normal window instead would look like success."""
    with pytest.raises(ValueError, match="both"):
        load_window("2026-01-01", None, NOW, 90)


def test_only_an_end_date_is_rejected() -> None:
    with pytest.raises(ValueError, match="both"):
        load_window(None, "2026-01-31", NOW, 90)


def test_a_start_after_the_end_is_rejected() -> None:
    with pytest.raises(ValueError, match="not before"):
        load_window("2026-03-01", "2026-02-01", NOW, 90)
