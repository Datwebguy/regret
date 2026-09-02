"""HTTP helpers for browser vs CLI auth, client IP, and CSRF origin checks."""

from __future__ import annotations

from urllib.parse import urlparse

from fastapi import Request

from regret.config import Settings, get_settings
from regret.errors import CSRFRejected


UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
CSRF_EXEMPT_PATHS = {
    "/api/alpaca/callback",
    "/api/health",
}


def client_ip(request: Request) -> str:
    """Prefer Fly's trusted client IP. Do not trust spoofable X-Forwarded-For."""
    fly = (request.headers.get("fly-client-ip") or "").strip()
    if fly:
        return fly
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def is_browser_request(request: Request) -> bool:
    """Browser fetch/navigation sends Origin or Sec-Fetch-*. CLI/MCP do not."""
    if (request.headers.get("x-regret-client") or "").strip().lower() == "cli":
        return False
    if request.headers.get("origin"):
        return True
    if request.headers.get("sec-fetch-site"):
        return True
    return False


def wants_device_token(request: Request) -> bool:
    """CLI/MCP may receive a bearer credential. The web app must not."""
    return not is_browser_request(request)


def allowed_origins(settings: Settings | None = None) -> set[str]:
    settings = settings or get_settings()
    origins = {item.rstrip("/") for item in settings.cors_origin_list}
    public = (settings.regret_public_url or "").rstrip("/")
    if public:
        origins.add(public)
    if settings.regret_env.lower() in {"test", "development"}:
        origins.update(
            {
                "http://testserver",
                "http://127.0.0.1:5173",
                "http://localhost:5173",
                "http://127.0.0.1:8000",
            }
        )
    return origins


def _origin_from_referer(referer: str) -> str | None:
    if not referer:
        return None
    parsed = urlparse(referer)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def request_origin(request: Request) -> str | None:
    origin = (request.headers.get("origin") or "").rstrip("/")
    if origin:
        return origin
    return _origin_from_referer(request.headers.get("referer") or "")


def enforce_csrf(request: Request) -> None:
    """
    Cookie-authenticated unsafe methods must come from a REGRET origin.

    Bearer-only CLI requests have no session cookie and are not CSRF-vulnerable
    in the browser sense. The Alpaca OAuth callback is exempt (its own state).
    """
    if request.method not in UNSAFE_METHODS:
        return
    path = request.url.path
    if path in CSRF_EXEMPT_PATHS:
        return

    settings = get_settings()
    cookie_name = settings.regret_session_cookie
    has_cookie = bool(request.cookies.get(cookie_name))
    origin = request_origin(request)
    allowed = allowed_origins(settings)

    if origin and origin not in allowed:
        raise CSRFRejected()

    if not has_cookie:
        return

    if origin is None:
        if settings.is_production:
            raise CSRFRejected()
        return
