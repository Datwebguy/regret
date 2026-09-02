from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from cryptography.fernet import Fernet, InvalidToken

from regret.config import Settings, get_settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def generate_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def hash_secret(value: str) -> str:
    return bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_secret(value: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(value.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _fernet(settings: Settings | None = None) -> Fernet:
    settings = settings or get_settings()
    raw = settings.regret_encryption_key.strip()
    if raw:
        key = raw.encode("utf-8")
        if len(key) != 44:
            digest = hashlib.sha256(raw.encode("utf-8")).digest()
            key = base64.urlsafe_b64encode(digest)
        return Fernet(key)
    if settings.is_production:
        raise RuntimeError("REGRET_ENCRYPTION_KEY must be set in production")
    digest = hashlib.sha256(settings.require_secret_key().encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_str(plaintext: str, settings: Settings | None = None) -> str:
    return _fernet(settings).encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_str(token: str, settings: Settings | None = None) -> str:
    try:
        return _fernet(settings).decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Unable to decrypt stored credential") from exc


def new_encryption_key() -> str:
    return Fernet.generate_key().decode("utf-8")


def sign_value(value: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    key = settings.require_secret_key().encode("utf-8")
    digest = hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{value}.{digest}"


def unsign_value(signed: str, settings: Settings | None = None) -> str | None:
    if "." not in signed:
        return None
    value, digest = signed.rsplit(".", 1)
    settings = settings or get_settings()
    key = settings.require_secret_key().encode("utf-8")
    expected = hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, digest):
        return None
    return value


def session_expiry(settings: Settings | None = None) -> datetime:
    settings = settings or get_settings()
    return utcnow() + timedelta(hours=settings.regret_session_ttl_hours)


def random_state() -> str:
    return secrets.token_urlsafe(24)


def ensure_data_dir(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    path = settings.sqlite_path()
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)


def generate_dev_secrets_if_needed() -> dict[str, str]:
    """Return generated secrets for first-run local development only."""
    return {
        "REGRET_SECRET_KEY": secrets.token_urlsafe(48),
        "REGRET_ENCRYPTION_KEY": new_encryption_key(),
    }


def fingerprint(value: str) -> str:
    """Non-reversible short fingerprint for logs. Never log the raw secret."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
