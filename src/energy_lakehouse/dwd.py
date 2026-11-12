"""DWD Open Data: hourly observations for the project's eight weather stations.

station list:  {base}/{folder}/recent/{CODE}_Stundenwerte_Beschreibung_Stationen.txt
recent data:   {base}/{folder}/recent/stundenwerte_{CODE}_{id5}_akt.zip

There is no API. Each station and parameter is one ZIP archive holding a rolling
window of about 550 days, rewritten daily, corrected history included. See
docs/dwd-notes.md for the measured details.
"""

import io
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

import httpx

from energy_lakehouse.http_client import get_bytes

BASE_URL = "https://opendata.dwd.de"
HOURLY_PATH = "/climate_environment/CDC/observations_germany/climate/hourly"

PRODUCT_PREFIX = "produkt_"
ENCODING = "latin-1"
MISSING = -999
STATION_ID_WIDTH = 5

STATION_LIST_HEADER_LINES = 2
MAX_STATION_AGE_DAYS = 7


@dataclass(frozen=True)
class DwdParameter:
    """One DWD parameter folder, and the columns this project takes from it."""

    folder: str
    code: str
    quality_column: str
    measurements: dict[str, str]


@dataclass(frozen=True)
class WeatherReading:
    """One measurement: one station, one hour, one parameter."""

    station_id: str
    timestamp: datetime
    parameter: str
    value: float | None
    quality: int | None


WIND = DwdParameter(
    folder="wind",
    code="FF",
    quality_column="QN_3",
    measurements={"F": "wind_speed_ms", "D": "wind_direction_deg"},
)

SUN = DwdParameter(
    folder="sun",
    code="SD",
    quality_column="QN_7",
    measurements={"SD_SO": "sunshine_minutes"},
)

PARAMETERS = (WIND, SUN)

STATION_IDS = ("04393", "03631", "00183", "03987", "00662", "01303", "05404", "04928")


def station_list_path(parameter: DwdParameter) -> str:
    """Path of the station catalogue for one parameter."""
    return (
        f"{HOURLY_PATH}/{parameter.folder}/recent/"
        f"{parameter.code}_Stundenwerte_Beschreibung_Stationen.txt"
    )


def recent_data_path(parameter: DwdParameter, station_id: str) -> str:
    """Path of one station's rolling archive. `station_id` is five digits of text."""
    return (
        f"{HOURLY_PATH}/{parameter.folder}/recent/"
        f"stundenwerte_{parameter.code}_{station_id}_akt.zip"
    )


def fetch_recent(client: httpx.Client, parameter: DwdParameter, station_id: str) -> bytes:
    """Download one archive. Raises NotFoundError if the station has no file."""
    return get_bytes(client, recent_data_path(parameter, station_id))


def product_member(names: list[str]) -> str:
    """The data member inside the archive. Everything else is metadata.

    The name carries the window it covers (`produkt_ff_stunde_20250504_20261104_00183.txt`)
    and so changes every day the file is rewritten; it can only be found by prefix.
    """
    for name in names:
        if name.startswith(PRODUCT_PREFIX):
            return name
    raise ValueError(f"no member starting with {PRODUCT_PREFIX!r} in {names}")


def read_product(archive: bytes) -> str:
    """Open the archive in memory and return the text of its data member."""
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        member = product_member(zf.namelist())
        return zf.read(member).decode(ENCODING)


def _to_value(field: str) -> float | None:
    """A measurement, or None for the -999 sentinel."""
    value = float(field)
    return None if value == MISSING else value


def _to_quality(field: str) -> int | None:
    """A DWD quality level, or None for the -999 sentinel."""
    value = int(field)
    return None if value == MISSING else value


def parse_product(text: str, parameter: DwdParameter) -> list[WeatherReading]:
    """Turn one product file into readings: one per station, hour and measurement.

    The timestamp is kept exactly as published. `MESS_DATUM` labels the *end* of the
    hour it describes (dwd-notes.md 7); the one-hour shift belongs in silver, so bronze
    stays a faithful copy of the source.
    """
    lines = text.splitlines()
    header = [name.strip() for name in lines[0].split(";")]
    readings: list[WeatherReading] = []

    for line in lines[1:]:
        if not line.strip():
            continue

        fields = [field.strip() for field in line.split(";")]
        row = dict(zip(header, fields, strict=True))

        # The file names the station 00183 but writes 183 in the column.
        station_id = f"{int(row['STATIONS_ID']):0{STATION_ID_WIDTH}d}"
        timestamp = datetime.strptime(row["MESS_DATUM"], "%Y%m%d%H").replace(tzinfo=UTC)
        quality = _to_quality(row[parameter.quality_column])

        for column, name in parameter.measurements.items():
            readings.append(
                WeatherReading(
                    station_id=station_id,
                    timestamp=timestamp,
                    parameter=name,
                    value=_to_value(row[column]),
                    quality=quality,
                )
            )

    return readings


@dataclass(frozen=True)
class Station:
    """One row of a DWD station catalogue."""

    station_id: str
    from_date: date
    to_date: date
    height_m: int
    latitude: float
    longitude: float
    name: str
    state: str


def parse_station_list(text: str) -> dict[str, Station]:
    """Parse a station catalogue, keyed by five-digit station id.

    The file is fixed width, not CSV: station names contain spaces
    ("Sankt Peter-Ording"), so splitting on whitespace corrupts the name and
    shifts every field after it. Fields are taken by character position.
    """
    stations: dict[str, Station] = {}

    for line in text.splitlines()[STATION_LIST_HEADER_LINES:]:
        if not line.strip():
            continue

        station = Station(
            station_id=line[0:5],
            from_date=datetime.strptime(line[6:14], "%Y%m%d").date(),
            to_date=datetime.strptime(line[15:23], "%Y%m%d").date(),
            height_m=int(line[23:38]),
            latitude=float(line[38:50]),
            longitude=float(line[50:60]),
            name=line[61:102].strip(),
            state=line[102:142].strip(),
        )
        stations[station.station_id] = station

    return stations


def fetch_station_list(client: httpx.Client, parameter: DwdParameter) -> dict[str, Station]:
    """Download and parse the station catalogue for one parameter."""
    raw = get_bytes(client, station_list_path(parameter))
    return parse_station_list(raw.decode(ENCODING))


def check_stations_alive(
    stations: dict[str, Station],
    station_ids: Sequence[str],
    as_of: date,
    max_age_days: int = MAX_STATION_AGE_DAYS,
) -> None:
    """Raise unless every configured station is listed and still reporting.

    A station inside `recent/` can be dead (00044 stops 02.03.2026). Dropping it
    silently takes the set from eight stations to seven and reports a calmer,
    sunnier Germany than there was, with nothing failing anywhere.
    """
    oldest_allowed = as_of - timedelta(days=max_age_days)
    problems: list[str] = []

    for station_id in station_ids:
        station = stations.get(station_id)
        if station is None:
            problems.append(f"{station_id}: not in the station list")
        elif station.to_date < oldest_allowed:
            problems.append(f"{station_id} ({station.name}): last reported {station.to_date}")

    if problems:
        raise ValueError(
            f"station check failed, nothing older than {oldest_allowed} is accepted: "
            + "; ".join(problems)
        )
