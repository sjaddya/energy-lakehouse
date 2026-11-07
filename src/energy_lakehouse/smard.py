"""
index:  https://www.smard.de/app/chart_data/{filterId}/{region}/index_{resolution}.json
data:   https://www.smard.de/app/chart_data/{filterId}/{region}/{filterId}_{region}_{resolution}_{chunk}.json

note the values: region = DE, resolution = hour, chunk = epoch milliseconds of Monday 00:00 Berlin

check docs/smard-notes.md for more details on the SMARD API and how to use it.

"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from energy_lakehouse.http_client import ApiError, get_json


@dataclass(frozen=True)
class SeriesPoint:
    filter_id: int
    timestamp: datetime
    value: float | None


BASE_URL = "https://www.smard.de"
REGION = "DE"
RESOLUTION = "hour"

GENERATION_SERIES = {
    4066: "biomass",
    1226: "hydro",
    1225: "wind_offshore",
    4067: "wind_onshore",
    4068: "solar_pv",
    1228: "other_renewable",
    1223: "lignite",
    4069: "hard_coal",
    4071: "natural_gas",
    4070: "pumped_storage",
    1227: "other_conventional",
}

MARKET_AREA_SERIES = {
    4169: "day_ahead_price_de_lu",
}

CONSUMPTION_SERIES = {
    410: "grid_load",
}

PRICE_IDS = (4169,)
RENEWABLE_IDS = (4066, 1226, 1225, 4067, 4068, 1228)
CONVENTIONAL_IDS = (1223, 4069, 4071, 4070, 1227)
PROJECT_INPUT_IDS = (4067, 1225, 4068, 4169, 410)


def unit_for(filter_id: int) -> str:
    """MWh for everything except the price series."""
    return "EUR/MWh" if filter_id in PRICE_IDS else "MWh"


def index_path(filter_id: int) -> str:
    return f"/app/chart_data/{filter_id}/{REGION}/index_{RESOLUTION}.json"


def chunk_path(filter_id: int, chunk: int) -> str:
    return f"/app/chart_data/{filter_id}/{REGION}/{filter_id}_{REGION}_{RESOLUTION}_{chunk}.json"


def fetch_index(client: httpx.Client, filter_id: int) -> list[int]:
    """Return a list of weekly chunk ids that exist for this series."""
    body = get_json(client, index_path(filter_id))
    timestamps = body.get("timestamps")
    if not timestamps:
        raise ApiError(f"index for {filter_id} is missing or no 'timestamps' key")
    return list(timestamps)


def fetch_chunk(client: httpx.Client, filter_id: int, chunk: int) -> dict[str, Any]:
    """Download one week of one series. Raises NotFoundError if the week is absent."""
    body: dict[str, Any] = get_json(client, chunk_path(filter_id, chunk))
    return body


def parse_chunk(body: dict[str, Any], filter_id: int) -> list[SeriesPoint]:
    """Turn one downloaded chunk into a list of series points."""
    points = []
    for entry in body["series"]:
        t = datetime.fromtimestamp(entry[0] / 1000, tz=UTC)
        points.append(SeriesPoint(filter_id=filter_id, timestamp=t, value=entry[1]))
    return points


def chunks_for_window(index: list[int], start: datetime, end: datetime) -> list[int]:
    """Return the chunk ids that overlap the window from start to end.

    A chunk id is the start of one week, in epoch milliseconds. A chunk is kept
    when it overlaps the window, not when its start falls inside it: the week
    straddling `start` begins earlier but still holds data we need, and dropping
    it loses the first days of the window with no error anywhere.
    """
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    picked = []
    for position, chunk in enumerate(index):
        # A chunk ends where the next one begins. Working it out as start + 7 days
        # would be wrong twice a year, because the weeks of the clock changes are
        # 167 and 169 hours long. The newest chunk has no successor and is still
        # being filled, so its end is left open.
        chunk_end = index[position + 1] if position + 1 < len(index) else None

        if chunk > end_ms:  # the week starts after the window ends
            continue

        if chunk_end is not None and chunk_end <= start_ms:  # the week ended before it began
            continue

        picked.append(chunk)

    return picked
