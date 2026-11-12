"""Unit tests for the DWD source module. No network, and no binary fixture in the repo:
every archive is built in memory with `zipfile`."""

import io
import zipfile
from datetime import UTC, date, datetime

import httpx
import pytest
import respx

from energy_lakehouse.dwd import (
    SUN,
    WIND,
    WeatherReading,
    check_stations_alive,
    fetch_recent,
    fetch_station_list,
    parse_product,
    parse_station_list,
    product_member,
    read_product,
    recent_data_path,
    station_list_path,
)

BASE = "https://opendata.dwd.test"

WIND_PRODUCT = """STATIONS_ID;MESS_DATUM;QN_3;   F;   D;eor
        183;2025050400;   10;   8.7; 290;eor
        183;2025050401;    1;-999;-999;eor
"""

SUN_PRODUCT = """STATIONS_ID;MESS_DATUM;QN_7;SD_SO;eor
       4393;2025050403;   10;  0.00;eor
"""

METADATA_NAMES = [
    "Metadaten_Stationsname_Betreibername_00183.txt",
    "Metadaten_Parameter_ff_stunde_00183.txt",
    "Metadaten_Geographie_00183.txt",
]
PRODUCT_NAME = "produkt_ff_stunde_20250504_20261104_00183.txt"


def make_archive(members: dict[str, str]) -> bytes:
    """A ZIP archive built in memory, each member encoded the way DWD encodes it."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name, text in members.items():
            zf.writestr(name, text.encode("latin-1"))
    return buffer.getvalue()


@pytest.fixture
def client() -> httpx.Client:
    return httpx.Client(base_url=BASE, timeout=1.0)


def test_station_list_path_uses_the_folder_and_the_code() -> None:
    assert station_list_path(WIND).endswith(
        "/hourly/wind/recent/FF_Stundenwerte_Beschreibung_Stationen.txt"
    )


def test_recent_data_path_keeps_the_five_digit_station_id() -> None:
    assert recent_data_path(SUN, "00183").endswith(
        "/hourly/sun/recent/stundenwerte_SD_00183_akt.zip"
    )


@respx.mock
def test_fetch_recent_requests_the_archive_path(client: httpx.Client) -> None:
    archive = make_archive({PRODUCT_NAME: WIND_PRODUCT})
    route = respx.get(f"{BASE}{recent_data_path(WIND, '00183')}").mock(
        return_value=httpx.Response(200, content=archive)
    )

    assert fetch_recent(client, WIND, "00183") == archive
    assert route.call_count == 1


def test_product_member_picks_the_data_file() -> None:
    assert product_member([*METADATA_NAMES, PRODUCT_NAME]) == PRODUCT_NAME


def test_product_member_raises_when_there_is_no_data_file() -> None:
    with pytest.raises(ValueError, match="produkt_"):
        product_member(METADATA_NAMES)


def test_read_product_returns_the_data_member_from_the_archive() -> None:
    archive = make_archive(dict.fromkeys(METADATA_NAMES, "metadata") | {PRODUCT_NAME: WIND_PRODUCT})

    assert read_product(archive) == WIND_PRODUCT


def test_read_product_decodes_latin_1() -> None:
    text = WIND_PRODUCT + "# Station Großenkneten\n"
    archive = make_archive({PRODUCT_NAME: text})

    assert "Großenkneten" in read_product(archive)


def test_one_wind_row_becomes_one_reading_per_measurement() -> None:
    readings = parse_product(WIND_PRODUCT, WIND)

    assert len(readings) == 4
    assert [reading.parameter for reading in readings[:2]] == [
        "wind_speed_ms",
        "wind_direction_deg",
    ]


def test_one_sun_row_becomes_exactly_one_reading() -> None:
    readings = parse_product(SUN_PRODUCT, SUN)

    assert readings == [
        WeatherReading(
            station_id="04393",
            timestamp=datetime(2025, 5, 4, 3, tzinfo=UTC),
            parameter="sunshine_minutes",
            value=0.0,
            quality=10,
        )
    ]


def test_station_id_is_padded_back_to_five_digits() -> None:
    readings = parse_product(WIND_PRODUCT, WIND)

    assert {reading.station_id for reading in readings} == {"00183"}


def test_mess_datum_is_read_as_utc() -> None:
    readings = parse_product(WIND_PRODUCT, WIND)

    assert readings[0].timestamp == datetime(2025, 5, 4, 0, tzinfo=UTC)


def test_the_measurements_are_read_as_numbers() -> None:
    readings = parse_product(WIND_PRODUCT, WIND)

    assert readings[0].value == 8.7
    assert readings[1].value == 290.0


def test_minus_999_becomes_null_but_the_quality_is_kept() -> None:
    readings = parse_product(WIND_PRODUCT, WIND)

    assert [reading.value for reading in readings[2:]] == [None, None]
    assert {reading.quality for reading in readings[2:]} == {1}


def test_blank_trailing_lines_are_ignored() -> None:
    assert parse_product(SUN_PRODUCT + "\n\n", SUN) == parse_product(SUN_PRODUCT, SUN)


STATION_LIST = (
    "Stations_id von_datum bis_datum Stationshoehe geoBreite geoLa"
    "enge Stationsname Bundesland Abgabe\n"
    "----------- --------- --------- ------------- --------- -----"
    "---- ----------------------------------------- ---------- ------\n"
    "00183 19730101 20261104             42     54.6791   13.4344 "
    "Arkona                                   Mecklenburg-Vorpommern\n"
    "00044 19710101 20260302             44     52.9336    8.2370 "
    "Großenkneten                             Niedersachsen\n"
    "04393 19690101 20261104              5     54.3279    8.6031 "
    "Sankt Peter-Ording                       Schleswig-Holstein\n"
)

AS_OF = date(2026, 11, 6)


def test_parse_station_list_keys_by_five_digit_id() -> None:
    stations = parse_station_list(STATION_LIST)

    assert sorted(stations) == ["00044", "00183", "04393"]


def test_header_lines_are_skipped() -> None:
    assert "Stations_id" not in parse_station_list(STATION_LIST)


def test_a_name_containing_a_space_survives() -> None:
    assert parse_station_list(STATION_LIST)["04393"].name == "Sankt Peter-Ording"


def test_a_name_containing_an_umlaut_survives() -> None:
    assert parse_station_list(STATION_LIST)["00044"].name == "Großenkneten"


def test_the_other_fields_are_read_as_their_own_types() -> None:
    arkona = parse_station_list(STATION_LIST)["00183"]

    assert arkona.from_date == date(1973, 1, 1)
    assert arkona.to_date == date(2026, 11, 4)
    assert arkona.height_m == 42
    assert arkona.latitude == 54.6791
    assert arkona.longitude == 13.4344
    assert arkona.state == "Mecklenburg-Vorpommern"


def test_blank_lines_are_ignored() -> None:
    assert parse_station_list(STATION_LIST + "\n\n") == parse_station_list(STATION_LIST)


def test_alive_check_passes_when_every_station_is_current() -> None:
    check_stations_alive(parse_station_list(STATION_LIST), ["00183", "04393"], AS_OF)


def test_alive_check_rejects_a_dead_station() -> None:
    with pytest.raises(ValueError, match="00044"):
        check_stations_alive(parse_station_list(STATION_LIST), ["00183", "00044"], AS_OF)


def test_alive_check_rejects_a_station_that_is_not_listed() -> None:
    with pytest.raises(ValueError, match="99999: not in the station list"):
        check_stations_alive(parse_station_list(STATION_LIST), ["99999"], AS_OF)


def test_alive_check_names_every_problem_at_once() -> None:
    with pytest.raises(ValueError, match=r"00044.*99999") as caught:
        check_stations_alive(parse_station_list(STATION_LIST), ["00044", "99999"], AS_OF)

    assert "00183" not in str(caught.value)


@respx.mock
def test_fetch_station_list_downloads_and_parses(client: httpx.Client) -> None:
    respx.get(f"{BASE}{station_list_path(WIND)}").mock(
        return_value=httpx.Response(200, content=STATION_LIST.encode("latin-1"))
    )

    assert "00183" in fetch_station_list(client, WIND)
