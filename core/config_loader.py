from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .utils import read_json


def load_json_config(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return {} if default is None else dict(default)
    data = read_json(path)
    if default is None:
        return data
    merged = dict(default)
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def env_or_value(env_name: str, fallback: Any) -> Any:
    raw = os.getenv(env_name)
    if raw is None or raw == "":
        return fallback
    return raw
