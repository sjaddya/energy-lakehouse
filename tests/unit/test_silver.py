"""Unit tests for the silver lookups. No network, no Spark: these are plain dicts."""

import pytest

from energy_lakehouse.dwd import STATION_IDS
from energy_lakehouse.silver import (
    MIN_STATIONS,
    NIGHT_HOURS_UTC,
    SERIES_NAMES,
    STATIONS,
    night_hours_sql,
    series_group_for,
    series_lookup,
    series_name_for,
    station_for,
    station_lookup,
)

PRICE_ID = 4169
WIND_ONSHORE_ID = 4067
LIGNITE_ID = 1223
GRID_LOAD_ID = 410


def test_every_configured_station_has_a_name() -> None:
    assert set(STATIONS) == set(STATION_IDS)


def test_the_station_names_are_spelled_as_the_dwd_catalogue_spells_them() -> None:
    assert station_for("04928") == ("Stuttgart (Schnarrenberg)", "Baden-Württemberg")
    assert station_for("05404") == ("Weihenstephan-Dürnast", "Bayern")


def test_the_station_lookup_has_one_row_per_station() -> None:
    rows = station_lookup()

    assert len(rows) == len(STATION_IDS)
    assert {row["station_id"] for row in rows} == set(STATION_IDS)


def test_the_series_lookup_has_one_row_per_series() -> None:
    rows = series_lookup()

    assert len(rows) == len(SERIES_NAMES)
    assert {row["filter_id"] for row in rows} == set(SERIES_NAMES)


def test_every_series_has_a_name_a_group_and_a_unit() -> None:
    for row in series_lookup():
        assert row["series_name"]
        assert row["series_group"]
        assert row["unit"]


def test_only_the_price_series_is_in_euro_per_megawatt_hour() -> None:
    units = {row["filter_id"]: row["unit"] for row in series_lookup()}

    assert units[PRICE_ID] == "EUR/MWh"
    assert all(unit == "MWh" for id_, unit in units.items() if id_ != PRICE_ID)


def test_the_groups_put_wind_with_renewables_and_lignite_with_conventionals() -> None:
    assert series_group_for(WIND_ONSHORE_ID) == "renewable"
    assert series_group_for(LIGNITE_ID) == "conventional"
    assert series_group_for(PRICE_ID) == "price"
    assert series_group_for(GRID_LOAD_ID) == "load"


def test_the_price_series_is_not_counted_as_generation() -> None:
    groups = {row["filter_id"]: row["series_group"] for row in series_lookup()}

    generation = [id_ for id_, group in groups.items() if group in {"renewable", "conventional"}]
    assert PRICE_ID not in generation
    assert GRID_LOAD_ID not in generation


def test_an_unknown_filter_id_is_an_error_not_a_blank_name() -> None:
    with pytest.raises(ValueError, match="9999"):
        series_name_for(9999)

    with pytest.raises(ValueError, match="9999"):
        series_group_for(9999)


def test_an_unknown_station_is_an_error() -> None:
    with pytest.raises(ValueError, match="99999"):
        station_for("99999")


def test_the_night_hours_are_the_six_sunshine_hours_dwd_never_published() -> None:
    assert len(NIGHT_HOURS_UTC) == 6
    assert set(NIGHT_HOURS_UTC) == {0, 1, 20, 21, 22, 23}

    # 02:00 and 19:00 are the first and last hours the 18-hour files did carry,
    # so imputing either of them would overwrite a measurement with a zero.
    assert 2 not in NIGHT_HOURS_UTC
    assert 19 not in NIGHT_HOURS_UTC


def test_night_hours_sql_is_a_sql_in_list_of_the_same_hours() -> None:
    assert night_hours_sql() == "(0, 1, 20, 21, 22, 23)"


def test_the_station_floor_is_six_of_eight() -> None:
    assert MIN_STATIONS == 6
    assert 0 < MIN_STATIONS <= len(STATION_IDS)
