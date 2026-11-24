"""The numbers dbt uses in SQL must be the numbers Python uses.

`night_hours_utc` and `min_stations` are decisions, not data. The Python
ingestion reads them from silver.py; the dbt models read them from
dbt_project.yml. Two copies of a decision drift silently - the SQL keeps
running, it just answers a slightly different question than the Python does.
This test is the thing that makes them one decision again.
"""

from pathlib import Path
from typing import Any

import yaml

from energy_lakehouse.dwd import STATION_IDS
from energy_lakehouse.silver import MIN_STATIONS, NIGHT_HOURS_UTC

DBT_PROJECT = Path(__file__).resolve().parents[2] / "dbt" / "dbt_project.yml"


def dbt_vars() -> dict[str, Any]:
    parsed: dict[str, Any] = yaml.safe_load(DBT_PROJECT.read_text(encoding="utf-8"))
    variables: dict[str, Any] = parsed["vars"]
    return variables


def test_the_dbt_project_declares_both_variables() -> None:
    assert set(dbt_vars()) == {"night_hours_utc", "min_stations"}


def test_the_night_hours_match_the_python_constant() -> None:
    assert tuple(dbt_vars()["night_hours_utc"]) == NIGHT_HOURS_UTC


def test_the_station_threshold_matches_the_python_constant() -> None:
    assert dbt_vars()["min_stations"] == MIN_STATIONS


def test_the_night_hours_are_real_hours_of_a_day() -> None:
    assert all(0 <= hour <= 23 for hour in dbt_vars()["night_hours_utc"])


def test_the_threshold_cannot_exceed_the_stations_that_exist() -> None:
    assert 1 <= dbt_vars()["min_stations"] <= len(STATION_IDS)
