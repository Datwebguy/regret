from __future__ import annotations

import hashlib
from sqlalchemy import select
from sqlalchemy.orm import Session

from regret.errors import UnauthorizedError, ValidationFailed
from regret.models.preferences import UserPreference
from regret.models.user import SessionToken, User
from regret.security import as_utc, generate_token, hash_secret, session_expiry, utcnow, verify_secret
from regret.services import audit


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(db: Session, *, email: str, password: str, display_name: str = "") -> User:
    email_n = normalize_email(email)
    if not email_n or "@" not in email_n:
        raise ValidationFailed("A valid email address is required.")
    if len(password) < 10:
        raise ValidationFailed("Password must be at least 10 characters.")
    existing = db.scalar(select(User).where(User.email == email_n))
    if existing:
        raise ValidationFailed("An account with this email already exists.")
    user = User(
        email=email_n,
        password_hash=hash_secret(password),
        display_name=(display_name or email_n.split("@")[0])[:120],
    )
    db.add(user)
    db.flush()
    db.add(UserPreference(user_id=user.id, default_environment="paper"))
    audit.record(db, user_id=user.id, action="user_registered", entity_type="user", entity_id=user.id)
    return user


def authenticate(db: Session, *, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == normalize_email(email)))
    if user is None or not user.is_active or not verify_secret(password, user.password_hash):
        raise UnauthorizedError("Email or password is incorrect.")
    return user


def issue_session(db: Session, user: User, *, user_agent: str = "") -> str:
    raw = generate_token(32)
    token = SessionToken(
        user_id=user.id,
        token_hash=_hash_token(raw),
        expires_at=session_expiry(),
        user_agent=user_agent[:400],
    )
    db.add(token)
    audit.record(db, user_id=user.id, action="session_created", entity_type="session", entity_id=token.id)
    return raw


def resolve_session(db: Session, raw_token: str | None) -> User:
    if not raw_token:
        raise UnauthorizedError()
    token = db.scalar(select(SessionToken).where(SessionToken.token_hash == _hash_token(raw_token)))
    if token is None or token.revoked:
        raise UnauthorizedError("Session is not valid.")
    if as_utc(token.expires_at) <= utcnow():
        raise UnauthorizedError("Session has expired.")
    user = db.get(User, token.user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Account is not active.")
    return user


def revoke_session(db: Session, raw_token: str | None) -> None:
    if not raw_token:
        return
    token = db.scalar(select(SessionToken).where(SessionToken.token_hash == _hash_token(raw_token)))
    if token:
        token.revoked = True
        audit.record(db, user_id=token.user_id, action="session_revoked", entity_type="session", entity_id=token.id)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
