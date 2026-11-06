"""Example integration test: calls a real service, so it is skipped by default.

Run with:  uv run pytest --run-integration
Replace the URL with the project's real API once it exists.
"""

import httpx
import pytest

from energy_lakehouse.http_client import get_json


@pytest.mark.integration
def test_public_api_answers() -> None:
    with httpx.Client(base_url="https://httpbin.org", timeout=10) as client:
        body = get_json(client, "/json")

    assert isinstance(body, dict)
