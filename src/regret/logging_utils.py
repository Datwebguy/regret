from __future__ import annotations

import logging
import sys
from typing import Any

SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "api_key",
    "api_secret",
    "client_secret",
    "alpaca_secret",
    "encrypted",
}


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root = logging.getLogger("regret")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"regret.{name}")


def safe_log_extra(data: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        lowered = key.lower()
        if any(part in lowered for part in SENSITIVE_KEYS):
            continue
        cleaned[key] = value
    return cleaned
