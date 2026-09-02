from __future__ import annotations

import os
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from regret.api.security_http import enforce_csrf
from regret.config import get_settings
from regret.db.session import init_db
from regret.errors import CSRFRejected, RateLimited, RegretError
from regret.logging_utils import configure_logging, get_logger
from regret.api.routes import account, agent, alpaca, analyze, auth, market, orders, rules

log = get_logger("api")


def _web_dist() -> Path:
    override = os.environ.get("REGRET_WEB_DIST")
    if override:
        return Path(override)
    here = Path(__file__).resolve()
    candidates = [
        Path("/app/web/dist"),
        Path.cwd() / "web" / "dist",
        here.parents[3] / "web" / "dist",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


WEB_DIST = _web_dist()


def _public_file(filename: str) -> Path | None:
    here = Path(__file__).resolve()
    for candidate in (
        WEB_DIST / filename,
        here.parents[3] / "web" / "public" / filename,
        Path.cwd() / "web" / "public" / filename,
        Path.cwd() / "web" / "dist" / filename,
    ):
        if candidate.is_file():
            return candidate
    return None


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            enforce_csrf(request)
        except CSRFRejected as exc:
            log.info("error code=%s status=%s", exc.code, exc.status_code)
            return JSONResponse(status_code=exc.status_code, content=exc.to_dict())
        return await call_next(request)


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    init_db(settings)

    app = FastAPI(title="REGRET", version="0.1.0", docs_url="/api/docs", redoc_url=None)

    app.add_middleware(CSRFMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RegretError)
    async def regret_error_handler(_request: Request, exc: RegretError) -> JSONResponse:
        log.info("error code=%s status=%s", exc.code, exc.status_code)
        headers = {}
        if isinstance(exc, RateLimited):
            retry = exc.details.get("retry_after")
            if retry:
                headers["Retry-After"] = str(retry)
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict(), headers=headers)

    @app.get("/api/health")
    def health() -> dict:
        from regret.db.session import healthcheck_db

        database_ok = False
        try:
            database_ok = healthcheck_db(settings)
        except Exception:
            database_ok = False
        payload = {
            "ok": database_ok,
            "env": settings.regret_env,
            "broker_connect_available": settings.oauth_configured,
            "live_trading_enabled": settings.regret_live_trading_enabled,
            "default_environment": settings.regret_default_trading_environment,
            "llm_configured": settings.llm_configured,
            "database": "ok" if database_ok else "unavailable",
        }
        if not database_ok:
            return JSONResponse(status_code=503, content=payload)
        return payload

    app.include_router(auth.router)
    app.include_router(alpaca.router)
    app.include_router(account.router)
    app.include_router(market.router)
    app.include_router(rules.router)
    app.include_router(analyze.router)
    app.include_router(orders.router)
    app.include_router(agent.router)

    @app.get("/terms", include_in_schema=False)
    def terms_page():
        path = _public_file("terms.html")
        if path is None:
            return HTMLResponse("Terms of Use are unavailable.", status_code=404)
        return FileResponse(path, media_type="text/html")

    @app.get("/privacy", include_in_schema=False)
    def privacy_page():
        path = _public_file("privacy.html")
        if path is None:
            return HTMLResponse("Privacy Policy is unavailable.", status_code=404)
        return FileResponse(path, media_type="text/html")

    @app.get("/legal.css", include_in_schema=False)
    def legal_css():
        path = _public_file("legal.css")
        if path is None:
            return HTMLResponse("/* missing */", status_code=404, media_type="text/css")
        return FileResponse(path, media_type="text/css")

    @app.get("/logo.png", include_in_schema=False)
    def logo_png():
        path = _public_file("logo.png") or _public_file("mark.png")
        if path is None:
            return HTMLResponse("missing", status_code=404)
        return FileResponse(path, media_type="image/png")

    @app.get("/mark.png", include_in_schema=False)
    def mark_png():
        path = _public_file("mark.png")
        if path is None:
            return HTMLResponse("missing", status_code=404)
        return FileResponse(path, media_type="image/png")

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon_ico():
        path = _public_file("favicon.ico")
        if path is None:
            return HTMLResponse("missing", status_code=404)
        return FileResponse(path, media_type="image/x-icon")

    if WEB_DIST.exists():
        assets = WEB_DIST / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        @app.get("/{full_path:path}")
        def spa(full_path: str):
            candidate = WEB_DIST / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(WEB_DIST / "index.html")

    return app


app = create_app()
