"""Example: a small, robust JSON client. Keep, adapt, or delete per project.

It shows the three things every ingestion client in the projects needs:
a timeout on every request, retries with backoff for temporary failures
(HTTP 429 and 5xx, network errors), and no retry for permanent ones (other 4xx),
because retrying a bad request only hides the bug.
"""

import logging
import time
from typing import Any

import httpx

log = logging.getLogger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class ApiError(RuntimeError):
    """Raised when the API keeps failing or returns a permanent error."""


def get_json(
    client: httpx.Client,
    path: str,
    params: dict[str, Any] | None = None,
    *,
    max_attempts: int = 3,
    backoff_seconds: float = 1.0,
) -> Any:
    """GET `path` and return the decoded JSON body.

    Retries temporary failures up to `max_attempts` times, waiting
    backoff_seconds, then 2x, then 4x between attempts.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.get(path, params=params)
        except httpx.TransportError as exc:  # timeouts, DNS, refused connections
            reason = f"{type(exc).__name__}: {exc}"
        else:
            if response.status_code < 400:
                return response.json()
            if response.status_code not in RETRYABLE_STATUS:
                raise ApiError(f"GET {path} failed permanently with HTTP {response.status_code}")
            reason = f"HTTP {response.status_code}"

        if attempt == max_attempts:
            raise ApiError(f"GET {path} failed after {max_attempts} attempts ({reason})")
        wait = backoff_seconds * 2 ** (attempt - 1)
        log.warning(
            "GET %s attempt %d/%d failed (%s); retrying in %.1fs",
            path,
            attempt,
            max_attempts,
            reason,
            wait,
        )
        time.sleep(wait)

    raise AssertionError("unreachable")  # pragma: no cover


def make_client(base_url: str, timeout_seconds: float = 10.0) -> httpx.Client:
    return httpx.Client(base_url=base_url, timeout=timeout_seconds)
