"""The seed files and the Python they came from must agree."""

from pathlib import Path

import pytest

from energy_lakehouse.seeds import (
    SEED_DIR,
    SEEDS,
    series_seed_csv,
    station_seed_csv,
    write_seeds,
)
from energy_lakehouse.silver import SERIES_NAMES, STATIONS

SERIES_COLUMNS = "filter_id,series_name,series_group,unit"
STATION_COLUMNS = "station_id,station_name,state"


@pytest.mark.parametrize("name", sorted(SEEDS))
def test_the_committed_seed_matches_the_python_it_came_from(name: str) -> None:
    # The whole point of generating the seeds: if someone edits the CSV by hand,
    # or changes silver.py without regenerating, this is where it shows up.
    committed = (SEED_DIR / name).read_text(encoding="utf-8")
    assert committed == SEEDS[name]()


def test_every_seed_file_exists() -> None:
    for name in SEEDS:
        assert (SEED_DIR / name).is_file(), f"{name} has not been generated"


def test_the_series_seed_has_a_row_for_every_configured_series() -> None:
    lines = series_seed_csv().splitlines()
    assert lines[0] == SERIES_COLUMNS
    assert len(lines) - 1 == len(SERIES_NAMES)


def test_the_station_seed_has_a_row_for_every_configured_station() -> None:
    lines = station_seed_csv().splitlines()
    assert lines[0] == STATION_COLUMNS
    assert len(lines) - 1 == len(STATIONS)


def test_station_ids_keep_their_leading_zeros() -> None:
    # 00183 must not become 183. dbt is told the column is a string in
    # dbt_project.yml; this asserts the file it reads still looks like one.
    body = station_seed_csv().splitlines()[1:]
    assert any(line.startswith("00183,") for line in body)
    assert all(len(line.split(",")[0]) == len("00183") for line in body)


def test_writing_the_seeds_is_deterministic(tmp_path: Path) -> None:
    first = write_seeds(tmp_path)
    contents = [path.read_text(encoding="utf-8") for path in first]
    write_seeds(tmp_path)
    assert [path.read_text(encoding="utf-8") for path in first] == contents


def test_the_files_use_lf_endings(tmp_path: Path) -> None:
    # A CRLF seed would make every regeneration a diff on Windows.
    for path in write_seeds(tmp_path):
        assert b"\r\n" not in path.read_bytes()
