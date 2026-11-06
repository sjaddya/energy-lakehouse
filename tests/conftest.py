"""Shared test setup.

Integration tests (marked @pytest.mark.integration) touch real services, so
they are skipped by default and run only with:  pytest --run-integration
"""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--run-integration", action="store_true", help="run integration tests")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-integration"):
        return
    skip = pytest.mark.skip(reason="integration test: pass --run-integration to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def no_real_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Retries wait between attempts; in tests we record the waits instead of sleeping."""
    waits: list[float] = []
    monkeypatch.setattr("time.sleep", waits.append)
    return waits
