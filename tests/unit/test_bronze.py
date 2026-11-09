"""Unit test for the Bronze client"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from energy_lakehouse.bronze import bronze_rows
from energy_lakehouse.smard import parse_chunk

FIXTURES = Path(__file__).parent.parent / "fixtures"

# What the caller stamps onto every row of a run. Fixed here so the asserts can
# name them exactly; SOURCE_CHUNK is the real chunk id of the saved week.
SOURCE_CHUNK = 1789336800000
LOAD_ID = "test-load"
FETCHED_AT = datetime(2026, 11, 9, tzinfo=UTC)

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
