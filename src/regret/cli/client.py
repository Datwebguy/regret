from __future__ import annotations

from typing import Any

import httpx

from regret.cli.config_store import load_config
from regret.errors import IntegrationUnavailable, RegretError


class ApiClient:
    def __init__(self) -> None:
        cfg = load_config()
        self.base = (cfg.get("api_url") or "http://127.0.0.1:8000").rstrip("/")
        self.token = cfg.get("token") or ""

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = kwargs.pop("headers", {})
        headers["X-Regret-Client"] = "cli"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            with httpx.Client(timeout=45.0) as client:
                response = client.request(method, f"{self.base}{path}", headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise IntegrationUnavailable(
                f"Unable to reach REGRET at {self.base}. Start the API with `python -m regret.api`."
            ) from exc
        if response.status_code >= 400:
            try:
                payload = response.json()
            except ValueError:
                payload = {"message": response.text}
            raise RegretError(
                payload.get("message") or "Request failed.",
                code=payload.get("error") or "api_error",
                status_code=response.status_code,
                details=payload.get("details") or {},
            )
        if not response.content:
            return {}
        return response.json()

    def get(self, path: str, **kwargs: Any) -> Any:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Any:
        return self.request("POST", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Any:
        return self.request("DELETE", path, **kwargs)
