"""The dbt seed files, rendered from the project facts in `silver`.

A dbt model is SQL and cannot call Python, so the two lookups the silver models
join to have to exist as data in the warehouse. The obvious way to get them
there is to type them into a CSV, and the obvious failure is that the CSV and
`silver.py` drift apart without anyone noticing: a station is renamed in one
place, a new series is added in the other, and a model starts producing nulls
that nothing explains.

So the CSVs are rendered from the same constants, and a test compares the
committed files to what this module produces. Editing one without the other
fails the suite, which is the only form of "single source of truth" that
survives contact with a second person.

Regenerate with:

    uv run python -m energy_lakehouse.seeds
"""

import csv
import io
from collections.abc import Callable
from pathlib import Path
from typing import Any

from energy_lakehouse.silver import series_lookup, station_lookup

# src/energy_lakehouse/seeds.py -> repo root -> dbt/seeds
SEED_DIR = Path(__file__).resolve().parents[2] / "dbt" / "seeds"

SERIES_SEED = "series_lookup.csv"
STATION_SEED = "station_lookup.csv"


def _to_csv(rows: list[dict[str, Any]]) -> str:
    """Rows as CSV text with a header, always LF, so the file is byte-stable."""
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def series_seed_csv() -> str:
    """The SMARD series lookup as seed text: filter_id, name, group, unit."""
    return _to_csv(series_lookup())


def station_seed_csv() -> str:
    """The DWD station lookup as seed text: id, name, federal state."""
    return _to_csv(station_lookup())


SEEDS: dict[str, Callable[[], str]] = {
    SERIES_SEED: series_seed_csv,
    STATION_SEED: station_seed_csv,
}


def write_seeds(directory: Path | None = None) -> list[Path]:
    """Write every seed file and return the paths written."""
    target = SEED_DIR if directory is None else directory
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, render in SEEDS.items():
        path = target / name
        path.write_text(render(), encoding="utf-8", newline="")
        written.append(path)
    return written


if __name__ == "__main__":  # pragma: no cover
    for seed_path in write_seeds():
        print("wrote", seed_path)
