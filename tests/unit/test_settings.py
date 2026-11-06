from pathlib import Path

import pytest

from energy_lakehouse.settings import get_settings


def test_defaults_when_nothing_is_set(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)  # no .env here
    for key in ("API_BASE_URL", "API_TIMEOUT_SECONDS", "DATA_DIR", "LOG_LEVEL"):
        monkeypatch.delenv(key, raising=False)

    s = get_settings()

    assert s.api_timeout_seconds == 10.0
    assert s.data_dir == Path("data")


def test_reads_values_from_dotenv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("API_TIMEOUT_SECONDS", raising=False)
    (tmp_path / ".env").write_text("# comment\nAPI_TIMEOUT_SECONDS=2.5\n", encoding="utf-8")

    assert get_settings().api_timeout_seconds == 2.5


def test_real_environment_beats_dotenv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("LOG_LEVEL=DEBUG\n", encoding="utf-8")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    assert get_settings().log_level == "WARNING"
