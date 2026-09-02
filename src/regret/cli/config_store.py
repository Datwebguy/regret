from __future__ import annotations

import json
from pathlib import Path


def config_dir() -> Path:
    return Path.home() / ".regret"


def config_path() -> Path:
    return config_dir() / "config.json"


def load_config() -> dict:
    path = config_path()
    if not path.exists():
        return {"api_url": "http://127.0.0.1:8000", "token": ""}
    return json.loads(path.read_text(encoding="utf-8"))


def save_config(data: dict) -> None:
    config_dir().mkdir(parents=True, exist_ok=True)
    path = config_path()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
