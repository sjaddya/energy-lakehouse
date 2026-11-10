"""
Bronze layer of the energy lakehouse.
This layer contains raw data ingested from various sources, including structured,
semi-structured, and unstructured data formats.
The bronze layer serves as the foundation for further processing and transformation in the silver
and gold layers of the lakehouse architecture.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from energy_lakehouse.smard import SeriesPoint, chunks_for_window


@dataclass(frozen=True)
class LoadWindow:
    start: datetime
    end: datetime
    is_backfill: bool


def load_window(
    backfill_start: str | None, backfill_end: str | None, now: datetime, days_back: int
) -> LoadWindow:
    """Which window this run loads, and whether it is a backfill.

    Both dates or neither. A date is "YYYY-MM-DD" and is read as UTC. The end
    date is inclusive, so one day is added to it: "2026-01-31" covers all of
    31 January. With no dates the window is the last `days_back` days, which is
    the normal scheduled run.
    """
    if not backfill_start and not backfill_end:
        return LoadWindow(start=now - timedelta(days=days_back), end=now, is_backfill=False)

    if not backfill_start or not backfill_end:
        raise ValueError("give both backfill_start and backfill_end, or neither")

    start = datetime.fromisoformat(backfill_start).replace(tzinfo=UTC)
    end = datetime.fromisoformat(backfill_end).replace(tzinfo=UTC) + timedelta(days=1)

    if start >= end:
        raise ValueError(f"backfill_start {backfill_start} is not before {backfill_end}")

    return LoadWindow(start=start, end=end, is_backfill=True)


def bronze_rows(
    points: list[SeriesPoint],
    source_chunk: int,
    load_id: str,
    fetched_at: datetime,
) -> list[dict[str, Any]]:
    """One dictionary per point, with the ingestion metadata attached."""
    data: list[dict[str, Any]] = [
        {
            "filter_id": point.filter_id,
            "timestamp_utc": point.timestamp,
            "value": point.value,
            "source_chunk": source_chunk,
            "load_id": load_id,
            "fetched_at": fetched_at,
        }
        for point in points
    ]
    return data


def chunks_to_fetch(
    index: list[int], high_water_mark: int | None, start: datetime, end: datetime
) -> list[int]:
    """Given a list of chunk ids, return the ones that need to be fetched.

    The caller has already fetched all chunks up to high_water_mark, so we only
    need to fetch chunks with id > high_water_mark. If high_water_mark is None,
    we have never fetched anything, so we need to fetch everything.

    We also filter out chunks that are outside the requested time range.
    """
    if high_water_mark is None:
        return chunks_for_window(index, start, end)
    else:
        return [chunk for chunk in index if chunk >= high_water_mark]
