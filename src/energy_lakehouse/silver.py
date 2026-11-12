"""Project facts the silver models need, in one tested place.

The silver tables are built in SQL, but two of the things they need are project
decisions rather than query logic: which series name belongs to a SMARD filter
id, and which station belongs to a DWD station id. They live here with tests,
and the notebook turns each one into a lookup view that the SQL joins to, so
the mapping exists exactly once and is never retyped inside a query.
"""

from typing import Any

from energy_lakehouse.dwd import STATION_IDS
from energy_lakehouse.smard import (
    CONSUMPTION_SERIES,
    CONVENTIONAL_IDS,
    GENERATION_SERIES,
    MARKET_AREA_SERIES,
    PRICE_IDS,
    RENEWABLE_IDS,
    unit_for,
)

SERIES_NAMES: dict[int, str] = {
    **GENERATION_SERIES,
    **MARKET_AREA_SERIES,
    **CONSUMPTION_SERIES,
}

GROUP_RENEWABLE = "renewable"
GROUP_CONVENTIONAL = "conventional"
GROUP_PRICE = "price"
GROUP_LOAD = "load"

SERIES_GROUPS: dict[int, str] = {
    **{filter_id: GROUP_RENEWABLE for filter_id in RENEWABLE_IDS},
    **{filter_id: GROUP_CONVENTIONAL for filter_id in CONVENTIONAL_IDS},
    **{filter_id: GROUP_PRICE for filter_id in PRICE_IDS},
    **{filter_id: GROUP_LOAD for filter_id in CONSUMPTION_SERIES},
}

# Name and federal state exactly as the DWD station catalogue spells them,
# copied from the saved FF_ and SD_ lists (both agree on all eight).
STATIONS: dict[str, tuple[str, str]] = {
    "04393": ("Sankt Peter-Ording", "Schleswig-Holstein"),
    "03631": ("Norderney", "Niedersachsen"),
    "00183": ("Arkona", "Mecklenburg-Vorpommern"),
    "03987": ("Potsdam", "Brandenburg"),
    "00662": ("Braunschweig", "Niedersachsen"),
    "01303": ("Essen-Bredeney", "Nordrhein-Westfalen"),
    "05404": ("Weihenstephan-Dürnast", "Bayern"),
    "04928": ("Stuttgart (Schnarrenberg)", "Baden-Württemberg"),
}

# Sunshine files carried 18 hours a day until 31.07.2026: published 03:00-20:00
# UTC, which is 02:00-19:00 after the hour shift. These six are the hours that
# were never published. They are night at every station in the set all year, so
# a missing sunshine value here becomes 0 with sun_is_imputed = true.
NIGHT_HOURS_UTC: tuple[int, ...] = (0, 1, 20, 21, 22, 23)

# An hourly station average needs at least this many of the eight stations
# before it may be called reliable. Two coastal stations are not Germany.
MIN_STATIONS = 6


def series_name_for(filter_id: int) -> str:
    """The readable name of a SMARD series, or an error if it is not configured."""
    try:
        return SERIES_NAMES[filter_id]
    except KeyError:
        raise ValueError(f"filter id {filter_id} has no series name") from None


def series_group_for(filter_id: int) -> str:
    """Which group a SMARD series belongs to: renewable, conventional, price or load."""
    try:
        return SERIES_GROUPS[filter_id]
    except KeyError:
        raise ValueError(f"filter id {filter_id} has no series group") from None


def station_for(station_id: str) -> tuple[str, str]:
    """The name and federal state of a configured DWD station."""
    try:
        return STATIONS[station_id]
    except KeyError:
        raise ValueError(f"station {station_id} has no name") from None


def series_lookup() -> list[dict[str, Any]]:
    """One row per SMARD series, for the notebook's lookup view."""
    return [
        {
            "filter_id": filter_id,
            "series_name": series_name_for(filter_id),
            "series_group": series_group_for(filter_id),
            "unit": unit_for(filter_id),
        }
        for filter_id in sorted(SERIES_NAMES)
    ]


def station_lookup() -> list[dict[str, Any]]:
    """One row per configured DWD station, for the notebook's lookup view."""
    rows = []
    for station_id in sorted(STATION_IDS):
        name, state = station_for(station_id)
        rows.append({"station_id": station_id, "station_name": name, "state": state})
    return rows


def night_hours_sql() -> str:
    """The night-hour set as a SQL IN list, so no query has to retype it."""
    return "(" + ", ".join(str(hour) for hour in NIGHT_HOURS_UTC) + ")"
