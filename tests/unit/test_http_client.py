"""Unit tests for the example client. No real network: respx intercepts every request."""

import httpx
import pytest
import respx

from data_project.http_client import ApiError, get_json

BASE = "https://api.test"


@pytest.fixture
def client() -> httpx.Client:
    return httpx.Client(base_url=BASE, timeout=1.0)


@respx.mock
def test_returns_json_on_success(client: httpx.Client) -> None:
    respx.get(f"{BASE}/items").mock(return_value=httpx.Response(200, json={"n": 3}))

    assert get_json(client, "/items") == {"n": 3}


@respx.mock
def test_passes_query_parameters(client: httpx.Client) -> None:
    route = respx.get(f"{BASE}/items", params={"region": "DE"}).mock(
        return_value=httpx.Response(200, json=[])
    )

    get_json(client, "/items", params={"region": "DE"})

    assert route.called


@pytest.mark.parametrize("status", [429, 500, 503])
@respx.mock
def test_retries_temporary_errors_then_succeeds(
    client: httpx.Client, status: int, no_real_sleep: list[float]
) -> None:
    respx.get(f"{BASE}/items").mock(
        side_effect=[httpx.Response(status), httpx.Response(200, json={"ok": True})]
    )

    assert get_json(client, "/items", backoff_seconds=0.5) == {"ok": True}
    assert no_real_sleep == [0.5]


@respx.mock
def test_backoff_doubles_between_attempts(client: httpx.Client, no_real_sleep: list[float]) -> None:
    respx.get(f"{BASE}/items").mock(return_value=httpx.Response(503))

    with pytest.raises(ApiError, match="after 3 attempts"):
        get_json(client, "/items", max_attempts=3, backoff_seconds=1.0)

    assert no_real_sleep == [1.0, 2.0]


@pytest.mark.parametrize("status", [400, 401, 404])
@respx.mock
def test_does_not_retry_permanent_errors(client: httpx.Client, status: int) -> None:
    route = respx.get(f"{BASE}/items").mock(return_value=httpx.Response(status))

    with pytest.raises(ApiError, match="permanently"):
        get_json(client, "/items")

    assert route.call_count == 1


@respx.mock
def test_retries_network_timeouts(client: httpx.Client) -> None:
    respx.get(f"{BASE}/items").mock(
        side_effect=[httpx.ConnectTimeout("slow"), httpx.Response(200, json=[1])]
    )

    assert get_json(client, "/items") == [1]
