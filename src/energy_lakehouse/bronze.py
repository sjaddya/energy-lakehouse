"""
Bronze layer of the energy lakehouse.
This layer contains raw data ingested from various sources, including structured,
semi-structured, and unstructured data formats.
The bronze layer serves as the foundation for further processing and transformation in the silver
and gold layers of the lakehouse architecture.
"""

from datetime import datetime
from typing import Any

from energy_lakehouse.smard import SeriesPoint


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
