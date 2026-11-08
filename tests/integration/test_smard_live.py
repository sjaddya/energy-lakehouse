"""Integration test: calls SMARD for real, so it is skipped by default.

Run with:  uv run python -m pytest --run-integration
"""

import httpx
import pytest

from energy_lakehouse.smard import BASE_URL, fetch_chunk, fetch_index, parse_chunk


@pytest.mark.integration
def test_smard_still_serves_the_expected_shape() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=10) as client:
        index = fetch_index(client, 4067)
        body = fetch_chunk(client, 4067, index[-1])

    rows = parse_chunk(body, 4067)

    assert len(index) > 600
    assert len(rows) == 168
    assert rows[0].timestamp.tzinfo is not None
