"""Minimal .env loader — pure stdlib, no external deps."""
from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(env_path: Path | str | None = None) -> None:
    """Parse a .env file and set variables into os.environ (if not already set)."""
    if env_path is None:
        env_path = Path(__file__).resolve().parent.parent / ".env"
    else:
        env_path = Path(env_path)

    if not env_path.is_file():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value
