"""Configuration read from environment variables.

Secrets and anything that differs between machines (API keys, URLs, paths)
come from the environment, never from code. Locally they live in `.env`
(git-ignored); `.env.example` documents every variable with a safe dummy value.
"""

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path = Path(".env")) -> None:
    """Load KEY=VALUE lines from .env into os.environ without overriding real env vars."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    api_base_url: str
    api_timeout_seconds: float
    data_dir: Path
    log_level: str


def get_settings() -> Settings:
    _load_dotenv()
    return Settings(
        api_base_url=os.environ.get("API_BASE_URL", "https://example.org/api"),
        api_timeout_seconds=float(os.environ.get("API_TIMEOUT_SECONDS", "10")),
        data_dir=Path(os.environ.get("DATA_DIR", "data")),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
    )
