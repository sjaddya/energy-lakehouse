"""The numbers dbt uses in SQL must be the numbers Python uses.

`night_hours_utc` and `min_stations` are decisions, not data. The Python
ingestion reads them from silver.py; the dbt models read them from
dbt_project.yml. Two copies of a decision drift silently - the SQL keeps
running, it just answers a slightly different question than the Python does.
This test is the thing that makes them one decision again.

Not every variable has a Python twin, and `headline_days` does not: no Python
reads it, because it is a property of one gold model's claim. So the variables
are split into two named sets below and the test asserts their union. Adding a
variable still fails this file until somebody says which set it belongs to,
which is the point - a variable nobody classified is a variable nobody decided
whether to mirror.
"""

from pathlib import Path
from typing import Any

import yaml

from energy_lakehouse.dwd import STATION_IDS
from energy_lakehouse.silver import MIN_STATIONS, NIGHT_HOURS_UTC

DBT_PROJECT = Path(__file__).resolve().parents[2] / "dbt" / "dbt_project.yml"

# Variables that exist in both places and must agree.
MIRRORED_IN_PYTHON = {"night_hours_utc", "min_stations"}

# Variables only SQL reads. Listing them is the decision being recorded.
SQL_ONLY = {"headline_days"}


def dbt_vars() -> dict[str, Any]:
    parsed: dict[str, Any] = yaml.safe_load(DBT_PROJECT.read_text(encoding="utf-8"))
    variables: dict[str, Any] = parsed["vars"]
    return variables


def test_every_variable_is_either_mirrored_or_deliberately_sql_only() -> None:
    assert set(dbt_vars()) == MIRRORED_IN_PYTHON | SQL_ONLY
    assert not MIRRORED_IN_PYTHON & SQL_ONLY


def test_the_night_hours_match_the_python_constant() -> None:
    assert tuple(dbt_vars()["night_hours_utc"]) == NIGHT_HOURS_UTC


def test_the_station_threshold_matches_the_python_constant() -> None:
    assert dbt_vars()["min_stations"] == MIN_STATIONS


def test_the_night_hours_are_real_hours_of_a_day() -> None:
    assert all(0 <= hour <= 23 for hour in dbt_vars()["night_hours_utc"])


def test_the_threshold_cannot_exceed_the_stations_that_exist() -> None:
    assert 1 <= dbt_vars()["min_stations"] <= len(STATION_IDS)


def test_the_headline_window_is_a_whole_number_of_days() -> None:
    # A quartile comparison over a window shorter than a week would be one
    # weather system rather than a pattern, and the var is substituted straight
    # into date_sub(), which needs an integer.
    days = dbt_vars()["headline_days"]
    assert isinstance(days, int)
    assert days >= 7
