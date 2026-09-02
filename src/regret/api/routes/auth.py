from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from regret.api.deps import current_user
from regret.api.security_http import client_ip, wants_device_token
from regret.config import get_settings
from regret.db.session import get_db
from regret.errors import RateLimited, UnauthorizedError
from regret.models.user import User
from regret.services import auth as auth_service
from regret.services import rate_limit

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterBody(BaseModel):
    email: EmailStr
    password: str
    display_name: str = ""


class LoginBody(BaseModel):
    email: EmailStr
    password: str


def _set_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.regret_session_cookie,
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.regret_session_ttl_hours * 3600,
        path="/",
    )


def _clear_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(settings.regret_session_cookie, path="/")


def _public_user(user: User) -> dict:
    return {"id": user.id, "email": user.email, "display_name": user.display_name}


def _rotate_session(db: Session, request: Request, response: Response, user: User) -> str:
    settings = get_settings()
    presented = request.cookies.get(settings.regret_session_cookie)
    if presented:
        auth_service.revoke_session(db, presented)
    token = auth_service.issue_session(db, user, user_agent=request.headers.get("user-agent", ""))
    _set_cookie(response, token)
    return token


def _auth_payload(request: Request, user: User, token: str) -> dict:
    payload = {"user": _public_user(user)}
    if wants_device_token(request):
        payload["token"] = token
    return payload


@router.post("/register")
def register(body: RegisterBody, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    ip = client_ip(request)
    allowed = rate_limit.register_allowed(ip=ip)
    if not allowed.allowed:
        raise RateLimited(
            "Too many accounts were created from this network. Try again later.",
            details={"retry_after": allowed.retry_after_seconds},
        )
    user = auth_service.register_user(db, email=body.email, password=body.password, display_name=body.display_name)
    rate_limit.record_registration(ip=ip)
    token = _rotate_session(db, request, response, user)
    return _auth_payload(request, user, token)


@router.post("/login")
def login(body: LoginBody, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    ip = client_ip(request)
    email = str(body.email)
    allowed = rate_limit.login_allowed(email=email, ip=ip)
    if not allowed.allowed:
        raise RateLimited(
            "Too many sign-in attempts. Try again later.",
            details={"retry_after": allowed.retry_after_seconds},
        )
    try:
        user = auth_service.authenticate(db, email=email, password=body.password)
    except UnauthorizedError:
        rate_limit.record_login_failure(email=email, ip=ip)
        raise
    rate_limit.clear_login_failures(email=email)
    token = _rotate_session(db, request, response, user)
    return _auth_payload(request, user, token)


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    token = request.cookies.get(settings.regret_session_cookie)
    header = request.headers.get("authorization")
    if header and header.lower().startswith("bearer "):
        token = header.split(" ", 1)[1].strip()
    auth_service.revoke_session(db, token)
    _clear_cookie(response)
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(current_user)) -> dict:
    return {"user": _public_user(user)}
