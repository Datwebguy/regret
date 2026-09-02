from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from regret.brokers.alpaca import AlpacaBrokerAdapter, AlpacaCredentials
from regret.config import Settings, get_settings
from regret.errors import ForbiddenError, IntegrationUnavailable, NotFoundError, ValidationFailed
from regret.market.alpaca import AlpacaMarketDataProvider
from regret.providers.alpaca import AlpacaProvider
from regret.models.alpaca_connection import AlpacaConnection
from regret.models.oauth_state import OAuthState
from regret.security import as_utc, decrypt_str, encrypt_str, random_state, utcnow
from regret.services import audit
from regret.types import ConnectionMethod, TradingEnvironment

# Official Alpaca Connect OAuth2
# https://docs.alpaca.markets/us/docs/using-oauth2-and-trading-api
# https://docs.alpaca.markets/us/docs/about-connect-api
AUTHORIZE_URL = "https://app.alpaca.markets/oauth/authorize"
TOKEN_URL = "https://api.alpaca.markets/oauth/token"

# Official scopes: data, trading, account:write.
# REGRET requests only what it uses. account:write is not required.
READ_SCOPES = "data"
TRADE_SCOPES = "data trading"
DEFAULT_CONNECT_SCOPES = TRADE_SCOPES


def scopes_for_purpose(purpose: str) -> str:
    if purpose == "trade":
        return TRADE_SCOPES
    return READ_SCOPES


def connection_can_trade(conn: AlpacaConnection) -> bool:
    scopes = (conn.scopes or "").split()
    return "trading" in scopes


def oauth_status(settings: Settings | None = None) -> dict:
    """User-facing broker status. Never expose environment variable names."""
    settings = settings or get_settings()
    available = settings.oauth_configured
    return {
        "connected": False,
        "connect_available": available,
        "live_trading_enabled": settings.regret_live_trading_enabled,
        "default_environment": "paper" if not settings.regret_live_trading_enabled else settings.regret_default_trading_environment,
        "message": (
            None
            if available
            else "Brokerage connection is currently unavailable. You can still use REGRET to analyze trades, write rules, and keep a journal."
        ),
    }


def begin_oauth(
    db: Session,
    user_id: str,
    *,
    environment: str,
    purpose: str = "trade",
    settings: Settings | None = None,
) -> dict:
    settings = settings or get_settings()
    if not settings.oauth_configured:
        raise IntegrationUnavailable(
            "Brokerage connection is currently unavailable.",
            code="oauth_not_configured",
        )
    env = _normalize_env(environment, settings)
    purpose_n = (purpose or "trade").strip().lower()
    if purpose_n not in {"read", "trade"}:
        raise ValidationFailed("Connection purpose must be read or trade.")
    scopes = scopes_for_purpose(purpose_n)
    state = random_state()
    db.add(
        OAuthState(
            user_id=user_id,
            state=state,
            environment=env,
            scopes=scopes,
            expires_at=utcnow() + timedelta(minutes=10),
        )
    )
    db.flush()
    params = {
        "response_type": "code",
        "client_id": settings.alpaca_oauth_client_id,
        "redirect_uri": settings.alpaca_oauth_redirect_uri,
        "state": state,
        "scope": scopes,
        "env": env,
    }
    url = AUTHORIZE_URL + "?" + urlencode(params)
    audit.record(db, user_id=user_id, action="alpaca_oauth_started", status=env)
    return {
        "authorization_url": url,
        "environment": env,
        "scopes": scopes,
    }


def complete_oauth(
    db: Session,
    *,
    code: str,
    state: str,
    settings: Settings | None = None,
) -> AlpacaConnection:
    settings = settings or get_settings()
    if not settings.oauth_configured:
        raise IntegrationUnavailable("Brokerage connection is currently unavailable.")
    record = db.scalar(select(OAuthState).where(OAuthState.state == state))
    if record is None or record.consumed:
        raise ValidationFailed("This brokerage connection request is not valid.")
    if as_utc(record.expires_at) <= utcnow():
        raise ValidationFailed("This brokerage connection request has expired. Start again.")
    record.consumed = True
    user_id = record.user_id
    env = record.environment
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.alpaca_oauth_client_id,
                    "client_secret": settings.alpaca_oauth_client_secret,
                    "redirect_uri": settings.alpaca_oauth_redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except httpx.HTTPError as exc:
        raise IntegrationUnavailable("Unable to reach Alpaca OAuth token endpoint.") from exc
    if response.status_code >= 400:
        raise IntegrationUnavailable("Alpaca did not accept the OAuth authorization code.")
    payload = response.json()
    access_token = payload.get("access_token")
    if not access_token:
        raise IntegrationUnavailable("Alpaca OAuth response did not include an access token.")
    refresh = payload.get("refresh_token") or ""
    scopes = payload.get("scope") or record.scopes or READ_SCOPES

    creds = AlpacaCredentials(environment=env, access_token=access_token)
    account = AlpacaProvider(creds, account_access=True).get_account()

    conn = _upsert_connection(
        db,
        user_id=user_id,
        environment=env,
        method=ConnectionMethod.OAUTH.value,
        account_id=account.account_id,
        account_number=account.account_number,
        access_token=access_token,
        refresh_token=refresh,
        scopes=scopes,
    )
    audit.record(
        db,
        user_id=user_id,
        action="user_connected_alpaca",
        entity_type="alpaca_connection",
        entity_id=conn.id,
        status=env,
        detail="oauth",
    )
    return conn


def connect_with_api_keys(
    db: Session,
    *,
    user_id: str,
    environment: str,
    api_key_id: str,
    api_secret: str,
    settings: Settings | None = None,
) -> AlpacaConnection:
    """
    Per-user keys, stored encrypted. Used when OAuth is not yet available for the
    deployment. Never uses a shared platform trading key.
    """
    settings = settings or get_settings()
    env = _normalize_env(environment, settings)
    key_id = api_key_id.strip()
    secret = api_secret.strip()
    if not key_id or not secret:
        raise ValidationFailed("Both Alpaca key ID and secret are required.")
    creds = AlpacaCredentials(environment=env, api_key_id=key_id, api_secret=secret)
    account = AlpacaProvider(creds, account_access=True).get_account()
    conn = _upsert_connection(
        db,
        user_id=user_id,
        environment=env,
        method=ConnectionMethod.API_KEY.value,
        account_id=account.account_id,
        account_number=account.account_number,
        api_key_id=key_id,
        api_secret=secret,
        scopes=TRADE_SCOPES,
    )
    audit.record(
        db,
        user_id=user_id,
        action="user_connected_alpaca",
        entity_type="alpaca_connection",
        entity_id=conn.id,
        status=env,
        detail="api_key",
    )
    return conn


def disconnect(db: Session, user_id: str, environment: str) -> None:
    conn = get_connection(db, user_id, environment)
    if conn is None:
        raise NotFoundError("No Alpaca connection exists for this environment.")
    db.delete(conn)
    audit.record(db, user_id=user_id, action="alpaca_disconnected", status=environment)


def get_connection(db: Session, user_id: str, environment: str | None = None) -> AlpacaConnection | None:
    stmt = select(AlpacaConnection).where(
        AlpacaConnection.user_id == user_id,
        AlpacaConnection.status == "active",
    )
    if environment:
        stmt = stmt.where(AlpacaConnection.environment == environment)
    else:
        stmt = stmt.order_by(AlpacaConnection.updated_at.desc())
    return db.scalar(stmt)


def list_connections(db: Session, user_id: str) -> list[AlpacaConnection]:
    return list(
        db.scalars(
            select(AlpacaConnection).where(AlpacaConnection.user_id == user_id)
        ).all()
    )


def public_connection(conn: AlpacaConnection | None) -> dict | None:
    if conn is None:
        return None
    return {
        "id": conn.id,
        "environment": conn.environment,
        "method": conn.method,
        "alpaca_account_id": conn.alpaca_account_id,
        "alpaca_account_number": conn.alpaca_account_number,
        "scopes": conn.scopes,
        "status": conn.status,
        "last_verified_at": conn.last_verified_at.isoformat() if conn.last_verified_at else None,
        "last_error": conn.last_error or None,
        "can_trade": connection_can_trade(conn),
    }


def credentials_for(conn: AlpacaConnection) -> AlpacaCredentials:
    if conn.method == ConnectionMethod.OAUTH.value:
        token = decrypt_str(conn.access_token_encrypted)
        return AlpacaCredentials(environment=conn.environment, access_token=token)
    key = decrypt_str(conn.api_key_encrypted)
    secret = decrypt_str(conn.api_secret_encrypted)
    return AlpacaCredentials(environment=conn.environment, api_key_id=key, api_secret=secret)


def broker_for(conn: AlpacaConnection) -> AlpacaBrokerAdapter:
    return AlpacaBrokerAdapter(credentials_for(conn))


def market_for(conn: AlpacaConnection, settings: Settings | None = None) -> AlpacaMarketDataProvider:
    settings = settings or get_settings()
    return AlpacaMarketDataProvider(credentials_for(conn), feed=settings.alpaca_data_feed)


def provider_for(conn: AlpacaConnection, settings: Settings | None = None) -> AlpacaProvider:
    settings = settings or get_settings()
    return AlpacaProvider(
        credentials_for(conn),
        feed=settings.alpaca_data_feed,
        account_access=True,
        quote_max_age_seconds=settings.regret_quote_max_age_seconds,
    )


def market_only_provider(settings: Settings | None = None) -> AlpacaProvider | None:
    settings = settings or get_settings()
    if not settings.platform_market_data_configured:
        return None
    creds = AlpacaCredentials(
        environment="paper",
        api_key_id=settings.market_data_key_id,
        api_secret=settings.market_data_secret,
    )
    return AlpacaProvider(
        creds,
        feed=settings.alpaca_data_feed,
        account_access=False,
        quote_max_age_seconds=settings.regret_quote_max_age_seconds,
    )


def provider_for_user(db: Session, user_id: str, environment: str | None = None) -> AlpacaProvider | None:
    conn = get_connection(db, user_id, environment)
    if conn is not None:
        return provider_for(conn)
    return market_only_provider()


def platform_market_provider(settings: Settings | None = None) -> AlpacaMarketDataProvider | None:
    """Public market data only. Never used to trade or read a user account."""
    settings = settings or get_settings()
    if not settings.platform_market_data_configured:
        return None
    creds = AlpacaCredentials(
        environment="paper",
        api_key_id=settings.market_data_key_id,
        api_secret=settings.market_data_secret,
    )
    return AlpacaMarketDataProvider(creds, feed=settings.alpaca_data_feed)


def market_provider_for_user(db: Session, user_id: str, environment: str | None = None):
    conn = get_connection(db, user_id, environment)
    if conn is not None:
        return market_for(conn), "brokerage"
    platform = platform_market_provider()
    if platform is not None:
        return platform, "market_data"
    return None, None


def require_connection(db: Session, user_id: str, environment: str | None = None) -> AlpacaConnection:
    conn = connection_for_execution(db, user_id, environment)
    if conn is None:
        raise IntegrationUnavailable(
            "Connect Alpaca to include your actual portfolio, buying power and existing positions.",
            code="alpaca_not_connected",
            status_code=409,
        )
    return conn


def connection_for_execution(
    db: Session, user_id: str, preferred_environment: str | None = None
) -> AlpacaConnection | None:
    """
    Resolve the user's real brokerage connection.

    An analysis done before connecting is stored as environment=unconnected.
    That must not be treated as an Alpaca environment.
    """
    preferred = (preferred_environment or "").strip().lower()
    if preferred in {TradingEnvironment.PAPER.value, TradingEnvironment.LIVE.value}:
        conn = get_connection(db, user_id, preferred)
        if conn is not None:
            return conn
        return None
    return get_connection(db, user_id, None)


def verify_connection(db: Session, user_id: str, environment: str | None = None) -> dict:
    """Hit Alpaca for this user. Never invent an account if the request fails."""
    conn = connection_for_execution(db, user_id, environment)
    base = oauth_status()
    if conn is None:
        base["connected"] = False
        base["reachable"] = False
        base["account"] = None
        return base
    try:
        account = provider_for(conn).get_account()
    except Exception as exc:
        conn.last_error = "The brokerage could not be reached with the saved connection."
        db.flush()
        base["connected"] = True
        base["reachable"] = False
        base["active"] = public_connection(conn)
        base["account"] = None
        base["message"] = conn.last_error
        _ = exc
        return base
    conn.last_error = ""
    conn.last_verified_at = utcnow()
    conn.alpaca_account_id = account.account_id or conn.alpaca_account_id
    conn.alpaca_account_number = account.account_number or conn.alpaca_account_number
    db.flush()
    base["connected"] = True
    base["reachable"] = True
    base["active"] = public_connection(conn)
    base["account"] = account.as_public_dict()
    base["message"] = None
    return base


def _upsert_connection(
    db: Session,
    *,
    user_id: str,
    environment: str,
    method: str,
    account_id: str,
    account_number: str,
    access_token: str = "",
    refresh_token: str = "",
    api_key_id: str = "",
    api_secret: str = "",
    scopes: str = "",
) -> AlpacaConnection:
    conn = db.scalar(
        select(AlpacaConnection).where(
            AlpacaConnection.user_id == user_id,
            AlpacaConnection.environment == environment,
        )
    )
    if conn is None:
        conn = AlpacaConnection(user_id=user_id, environment=environment)
        db.add(conn)
    conn.method = method
    conn.alpaca_account_id = account_id
    conn.alpaca_account_number = account_number
    conn.scopes = scopes
    conn.status = "active"
    conn.last_error = ""
    conn.last_verified_at = utcnow()
    conn.access_token_encrypted = encrypt_str(access_token) if access_token else ""
    conn.refresh_token_encrypted = encrypt_str(refresh_token) if refresh_token else ""
    conn.api_key_encrypted = encrypt_str(api_key_id) if api_key_id else ""
    conn.api_secret_encrypted = encrypt_str(api_secret) if api_secret else ""
    db.flush()
    return conn


def _normalize_env(environment: str, settings: Settings) -> str:
    env = (environment or "paper").strip().lower()
    if env not in {TradingEnvironment.PAPER.value, TradingEnvironment.LIVE.value}:
        raise ValidationFailed("Environment must be paper or live.")
    if env == TradingEnvironment.LIVE.value and not settings.regret_live_trading_enabled:
        raise ForbiddenError(
            "Live trading is not enabled. Paper is the only brokerage environment on this deployment."
        )
    return env
