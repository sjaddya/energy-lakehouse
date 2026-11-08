"""Unit Tests for the SMARD client"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from energy_lakehouse.http_client import ApiError, NotFoundError
from energy_lakehouse.smard import (
    BASE_URL,
    chunk_path,
    chunks_for_window,
    fetch_chunk,
    fetch_index,
    index_path,
    parse_chunk,
    unit_for,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"
WEEK_MS = 7 * 24 * 60 * 60 * 1000


def at(milliseconds: float) -> datetime:
    """A UTC datetime from epoch milliseconds, for building test windows."""
    return datetime.fromtimestamp(milliseconds / 1000, tz=UTC)


@pytest.fixture
def client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=1.0)


def load_fixture(name: str) -> dict[str, Any]:
    body: dict[str, Any] = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return body


@respx.mock
def test_fetch_index_returns_list_of_chunks(client: httpx.Client) -> None:
    """Test the fetch_index function returns a list of chunk ids"""
    respx.get(f"{BASE_URL}{index_path(4067)}").mock(
        return_value=httpx.Response(200, json={"timestamps": [1, 2, 3]})
    )

    assert fetch_index(client, 4067) == [1, 2, 3]


@respx.mock
def test_fetch_index_raises_api_error_on_missing_timestamps(client: httpx.Client) -> None:
    """Test the fetch_index function raises ApiError if timestamps key is missing"""
    respx.get(f"{BASE_URL}{index_path(4067)}").mock(
        return_value=httpx.Response(200, json={"no_timestamps": []})
    )

    with pytest.raises(ApiError, match="missing or no 'timestamps' key"):
        fetch_index(client, 4067)


@respx.mock
def test_fetch_chunk_raises_not_found_a_missing_week_404(client: httpx.Client) -> None:
    """Test the fetch_chunk function raises NotFoundError if the week is absent"""
    route = respx.get(f"{BASE_URL}{chunk_path(4067, 1789336800000)}").mock(
        return_value=httpx.Response(404)
    )

    with pytest.raises(NotFoundError, match="404"):
        fetch_chunk(client, 4067, 1789336800000)

    assert route.call_count == 1


@respx.mock
def test_fetch_chunk_returns_body(client: httpx.Client) -> None:
    respx.get(f"{BASE_URL}{chunk_path(4067, 1789336800000)}").mock(
        return_value=httpx.Response(200, json={"series": [[1789336800000, 5997.52]]})
    )

    body = fetch_chunk(client, 4067, 1789336800000)

    assert body == {"series": [[1789336800000, 5997.52]]}


def test_chunks_for_window_includes_the_week_straddling_the_start() -> None:
    index = [0, WEEK_MS, 2 * WEEK_MS, 3 * WEEK_MS]

    picked = chunks_for_window(index, at(1.5 * WEEK_MS), at(2.5 * WEEK_MS))

    assert picked == [WEEK_MS, 2 * WEEK_MS]


def test_chunks_for_window_excludes_a_week_that_ended_before_the_window() -> None:
    index = [0, WEEK_MS, 2 * WEEK_MS]

    picked = chunks_for_window(index, at(2.2 * WEEK_MS), at(2.5 * WEEK_MS))

    assert picked == [2 * WEEK_MS]


def test_unit_for_distinguishes_price_from_generation() -> None:
    assert unit_for(4169) == "EUR/MWh"
    assert unit_for(4067) == "MWh"


def test_parse_chunk_rows_utc_aware_filter_id() -> None:
    """Test parsing a chunk. all parsed"""
    json_data = load_fixture("smard_4067_hour.json")

    parsed_data = parse_chunk(json_data, 4067)

    assert len(parsed_data) == 168


def test_parse_chunk_utc_aware() -> None:
    """Test: timestamp is UTC aware"""
    json_data = load_fixture("smard_4067_hour.json")

    parsed_data = parse_chunk(json_data, 4067)

    assert parsed_data[0].timestamp == datetime(2026, 9, 13, 22, 0, tzinfo=UTC)


def test_parse_chunk_filter_id() -> None:
    """Test: filter_id is correct"""
    json_data = load_fixture("smard_4067_hour.json")

    parsed_data = parse_chunk(json_data, 4067)

    assert all(parsed.filter_id == 4067 for parsed in parsed_data)


def test_parse_chunk_none_value_row() -> None:
    """Test for parsing preserve None values"""
    json_data = {"series": [[1789336800000, 5997.52], [1789340400000, None]]}

    parsed_data = parse_chunk(json_data, 4067)

    assert parsed_data[1].value is None


def test_index_path() -> None:
    """Test the index path generation"""
    assert index_path(4067) == "/app/chart_data/4067/DE/index_hour.json"


def test_chunk_path() -> None:
    """Test the chunk path generation"""
    assert chunk_path(4067, 1789336800000) == (
        "/app/chart_data/4067/DE/4067_DE_hour_1789336800000.json"
    )
