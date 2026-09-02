from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from regret.config import get_settings
from regret.db.session import get_db
from regret.errors import UnauthorizedError
from regret.models.user import User
from regret.services import auth as auth_service


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = _extract_token(request)
    return auth_service.resolve_session(db, token)


def optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = _extract_token(request)
    if not token:
        return None
    try:
        return auth_service.resolve_session(db, token)
    except UnauthorizedError:
        return None


def _extract_token(request: Request) -> str | None:
    settings = get_settings()
    cookie = request.cookies.get(settings.regret_session_cookie)
    if cookie:
        return cookie
    header = request.headers.get("authorization") or request.headers.get("Authorization")
    if header and header.lower().startswith("bearer "):
        return header.split(" ", 1)[1].strip()
    return None
