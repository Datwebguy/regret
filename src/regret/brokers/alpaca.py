from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import httpx

from regret.brokers.base import (
    AccountSnapshot,
    AssetInfo,
    BrokerAdapter,
    ClockInfo,
    OrderRequest,
    OrderSnapshot,
    PositionSnapshot,
)
from regret.errors import DataUnavailable, IntegrationUnavailable, NotFoundError, ValidationFailed
from regret.security import utcnow
from regret.types import dec


PAPER_TRADING_URL = "https://paper-api.alpaca.markets"
LIVE_TRADING_URL = "https://api.alpaca.markets"


def trading_base_url(environment: str) -> str:
    if environment == "live":
        return LIVE_TRADING_URL
    return PAPER_TRADING_URL


class AlpacaCredentials:
    def __init__(
        self,
        *,
        environment: str,
        access_token: str | None = None,
        api_key_id: str | None = None,
        api_secret: str | None = None,
    ) -> None:
        self.environment = environment
        self.access_token = access_token
        self.api_key_id = api_key_id
        self.api_secret = api_secret
        if not access_token and not (api_key_id and api_secret):
            raise IntegrationUnavailable("Alpaca credentials are not available for this user.")

    def headers(self) -> dict[str, str]:
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {
            "APCA-API-KEY-ID": self.api_key_id or "",
            "APCA-API-SECRET-KEY": self.api_secret or "",
        }


class AlpacaBrokerAdapter(BrokerAdapter):
    def __init__(self, credentials: AlpacaCredentials, *, timeout: float = 20.0) -> None:
        self.credentials = credentials
        self.environment = credentials.environment
        self.base_url = trading_base_url(credentials.environment)
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> tuple[Any, str]:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method,
                    url,
                    headers={**self.credentials.headers(), "Accept": "application/json"},
                    json=json,
                    params=params,
                )
        except httpx.HTTPError as exc:
            raise IntegrationUnavailable(f"Alpaca trading API is unavailable: {exc.__class__.__name__}.") from exc

        request_id = response.headers.get("X-Request-ID") or response.headers.get("x-request-id") or ""
        if response.status_code == 401:
            raise IntegrationUnavailable(
                "Alpaca authorization expired or was revoked. Reconnect the Alpaca account.",
                code="alpaca_auth_expired",
                status_code=401,
            )
        if response.status_code == 403:
            raise IntegrationUnavailable(
                _message_from_response(response, "Alpaca rejected this request (403)."),
                code="alpaca_forbidden",
                status_code=403,
            )
        if response.status_code == 404:
            raise NotFoundError(_message_from_response(response, "Alpaca resource not found."), code="alpaca_not_found")
        if response.status_code == 422:
            raise ValidationFailed(_message_from_response(response, "Alpaca rejected the order parameters."))
        if response.status_code == 429:
            raise IntegrationUnavailable(
                "Alpaca rate limit reached. Try again shortly.",
                code="alpaca_rate_limited",
                status_code=429,
            )
        if response.status_code >= 500:
            raise IntegrationUnavailable("Alpaca trading API returned a server error.")
        if response.status_code >= 400:
            raise IntegrationUnavailable(_message_from_response(response, "Alpaca request failed."))
        if response.status_code == 204 or not response.content:
            return None, request_id
        try:
            return response.json(), request_id
        except ValueError as exc:
            raise IntegrationUnavailable("Alpaca returned a non-JSON response.") from exc

    def get_account(self) -> AccountSnapshot:
        data, _ = self._request("GET", "/v2/account")
        received = utcnow()
        trading_blocked = _optional_bool(data, "trading_blocked")
        trade_suspended = _optional_bool(data, "trade_suspended_by_user")
        account_blocked = _optional_bool(data, "account_blocked")
        return AccountSnapshot(
            account_id=str(data.get("id") or ""),
            account_number=str(data.get("account_number") or ""),
            status=str(data.get("status") or "") or None,
            currency=str(data.get("currency") or "") or None,
            cash=dec(data.get("cash")),
            equity=dec(data.get("equity")),
            last_equity=dec(data.get("last_equity")),
            buying_power=dec(data.get("buying_power")),
            portfolio_value=dec(data.get("portfolio_value")),
            long_market_value=dec(data.get("long_market_value")),
            short_market_value=dec(data.get("short_market_value")),
            trading_blocked=trading_blocked,
            pattern_day_trader=_optional_bool(data, "pattern_day_trader"),
            trade_suspended_by_user=trade_suspended,
            account_blocked=account_blocked,
            trading_status=_trading_status(trading_blocked, trade_suspended, account_blocked),
            raw=_public_account_raw(data),
            received_timestamp=received,
        )

    def get_positions(self) -> list[PositionSnapshot]:
        data, _ = self._request("GET", "/v2/positions")
        if not isinstance(data, list):
            raise DataUnavailable("Alpaca positions response was not a list.")
        return [
            PositionSnapshot(
                symbol=str(item.get("symbol") or ""),
                qty=dec(item.get("qty")),
                side=str(item.get("side") or ""),
                avg_entry_price=dec(item.get("avg_entry_price")),
                market_value=dec(item.get("market_value")),
                cost_basis=dec(item.get("cost_basis")),
                unrealized_pl=dec(item.get("unrealized_pl")),
                unrealized_plpc=dec(item.get("unrealized_plpc")),
                current_price=dec(item.get("current_price")),
                raw=_public_position_raw(item),
            )
            for item in data
        ]

    def get_orders(self, status: str = "open") -> list[OrderSnapshot]:
        data, request_id = self._request("GET", "/v2/orders", params={"status": status, "limit": 100, "direction": "desc"})
        if not isinstance(data, list):
            raise DataUnavailable("Alpaca orders response was not a list.")
        return [_map_order(item, request_id) for item in data]

    def get_order(self, order_id: str) -> OrderSnapshot:
        data, request_id = self._request("GET", f"/v2/orders/{order_id}")
        return _map_order(data, request_id)

    def get_order_by_client_id(self, client_order_id: str) -> OrderSnapshot | None:
        try:
            data, request_id = self._request("GET", f"/v2/orders:by_client_order_id", params={"client_order_id": client_order_id})
        except NotFoundError:
            return None
        return _map_order(data, request_id)

    def submit_order(self, request: OrderRequest) -> OrderSnapshot:
        payload: dict[str, Any] = {
            "symbol": request.symbol,
            "side": request.side,
            "type": request.type,
            "time_in_force": request.time_in_force,
        }
        if request.qty:
            payload["qty"] = request.qty
        if request.notional:
            payload["notional"] = request.notional
        if request.limit_price:
            payload["limit_price"] = request.limit_price
        if request.stop_price:
            payload["stop_price"] = request.stop_price
        if request.client_order_id:
            payload["client_order_id"] = request.client_order_id
        data, request_id = self._request("POST", "/v2/orders", json=payload)
        return _map_order(data, request_id)

    def get_option_contracts(
        self,
        underlying_symbol: str,
        *,
        expiration_gte: str | None = None,
        expiration_lte: str | None = None,
        status: str = "active",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch active option contracts for an underlying symbol from Alpaca Trading API."""
        params: dict[str, Any] = {
            "underlying_symbols": underlying_symbol.upper(),
            "status": status,
            "limit": limit,
        }
        if expiration_gte:
            params["expiration_date_gte"] = expiration_gte
        if expiration_lte:
            params["expiration_date_lte"] = expiration_lte
        data, _ = self._request("GET", "/v2/options/contracts", params=params)
        if isinstance(data, dict) and "option_contracts" in data:
            return data["option_contracts"]
        if isinstance(data, list):
            return data
        return []

    def submit_option_order(
        self,
        symbol: str,
        qty: int | str,
        side: str,
        *,
        order_type: str = "limit",
        limit_price: str | None = None,
        position_intent: str = "buy_to_open",
        time_in_force: str = "day",
        client_order_id: str | None = None,
    ) -> OrderSnapshot:
        """Submit a single-leg option contract order on Alpaca."""
        payload: dict[str, Any] = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side.lower(),
            "type": order_type,
            "time_in_force": time_in_force,
            "position_intent": position_intent,
        }
        if limit_price is not None:
            payload["limit_price"] = str(limit_price)
        if client_order_id:
            payload["client_order_id"] = client_order_id
        data, request_id = self._request("POST", "/v2/orders", json=payload)
        return _map_order(data, request_id)

    def submit_spread_order(
        self,
        *,
        short_symbol: str,
        long_symbol: str,
        qty: int = 1,
        short_price: str | None = None,
        long_price: str | None = None,
        client_order_id_prefix: str | None = None,
    ) -> list[OrderSnapshot]:
        """Submit both legs of a credit spread (long leg first to cover the short leg, avoiding uncovered rejection)."""
        pfx = client_order_id_prefix or f"regret-opt-{utcnow().strftime('%H%M%S')}"

        # 1. Try native multi-leg (mleg) spread order
        try:
            mleg_payload = {
                "order_class": "mleg",
                "qty": str(qty),
                "type": "market",
                "time_in_force": "day",
                "legs": [
                    {
                        "symbol": long_symbol,
                        "ratio_qty": "1",
                        "side": "buy",
                        "position_intent": "buy_to_open",
                    },
                    {
                        "symbol": short_symbol,
                        "ratio_qty": "1",
                        "side": "sell",
                        "position_intent": "sell_to_open",
                    },
                ],
                "client_order_id": f"{pfx}-mleg",
            }
            data, request_id = self._request("POST", "/v2/orders", json=mleg_payload)
            return [_map_order(data, request_id)]
        except Exception:
            pass

        # 2. Sequential fallback: Buy the Long protection leg FIRST so the short leg is covered
        orders = []
        try:
            # Leg 1: Long hedge leg (Buy to open)
            long_order = self.submit_option_order(
                symbol=long_symbol,
                qty=qty,
                side="buy",
                order_type="limit" if long_price else "market",
                limit_price=long_price,
                position_intent="buy_to_open",
                client_order_id=f"{pfx}-long",
            )
            orders.append(long_order)

            # Leg 2: Short leg (Sell to open)
            short_order = self.submit_option_order(
                symbol=short_symbol,
                qty=qty,
                side="sell",
                order_type="limit" if short_price else "market",
                limit_price=short_price,
                position_intent="sell_to_open",
                client_order_id=f"{pfx}-short",
            )
            orders.append(short_order)
            return orders
        except Exception as exc:
            # Rollback: Cancel any submitted legs if the full spread failed to place
            for o in orders:
                try:
                    self.cancel_order(o.id)
                except Exception:
                    pass
            raise exc

    def cancel_order(self, order_id: str) -> None:
        self._request("DELETE", f"/v2/orders/{order_id}")

    def replace_order(self, order_id: str, request: OrderRequest) -> OrderSnapshot:
        payload: dict[str, Any] = {}
        if request.qty:
            payload["qty"] = request.qty
        if request.time_in_force:
            payload["time_in_force"] = request.time_in_force
        if request.limit_price:
            payload["limit_price"] = request.limit_price
        if request.stop_price:
            payload["stop_price"] = request.stop_price
        data, request_id = self._request("PATCH", f"/v2/orders/{order_id}", json=payload)
        return _map_order(data, request_id)

    def get_asset(self, symbol: str) -> AssetInfo:
        data, _ = self._request("GET", f"/v2/assets/{symbol}")
        return AssetInfo(
            symbol=str(data.get("symbol") or symbol),
            tradable=bool(data.get("tradable")),
            status=str(data.get("status") or ""),
            asset_class=str(data.get("class") or data.get("asset_class") or ""),
            name=str(data.get("name") or ""),
            raw={"tradable": data.get("tradable"), "status": data.get("status"), "class": data.get("class")},
        )

    def list_assets(self, *, status: str = "active", asset_class: str = "us_equity") -> list[AssetInfo]:
        data, _ = self._request("GET", "/v2/assets", params={"status": status, "asset_class": asset_class})
        if not isinstance(data, list):
            raise DataUnavailable("Alpaca assets response was not a list.")
        return [
            AssetInfo(
                symbol=str(item.get("symbol") or ""),
                tradable=bool(item.get("tradable")),
                status=str(item.get("status") or ""),
                asset_class=str(item.get("class") or item.get("asset_class") or ""),
                name=str(item.get("name") or ""),
                raw={"tradable": item.get("tradable"), "status": item.get("status"), "class": item.get("class")},
            )
            for item in data
        ]

    def get_clock(self) -> ClockInfo:
        data, _ = self._request("GET", "/v2/clock")
        ts = _parse_ts(data.get("timestamp"))
        return ClockInfo(
            timestamp=ts,
            is_open=bool(data.get("is_open")),
            next_open=str(data.get("next_open") or "") or None,
            next_close=str(data.get("next_close") or "") or None,
            raw={"is_open": data.get("is_open"), "timestamp": data.get("timestamp")},
        )

    def close_position(
        self,
        symbol_or_asset_id: str,
        *,
        qty: str | None = None,
        percentage: str | None = None,
    ) -> OrderSnapshot:
        params: dict[str, Any] = {}
        if qty is not None:
            params["qty"] = str(qty)
        if percentage is not None:
            params["percentage"] = str(percentage)
        data, request_id = self._request("DELETE", f"/v2/positions/{symbol_or_asset_id}", params=params or None)
        return _map_order(data, request_id)

    def close_all_positions(self, *, cancel_orders: bool = True) -> list[OrderSnapshot]:
        params = {"cancel_orders": cancel_orders}
        data, request_id = self._request("DELETE", "/v2/positions", params=params)
        if isinstance(data, list):
            return [_map_order(item, request_id) for item in data]
        return []


def _map_order(data: dict[str, Any], request_id: str) -> OrderSnapshot:
    return OrderSnapshot(
        id=str(data.get("id") or ""),
        client_order_id=str(data.get("client_order_id") or ""),
        symbol=str(data.get("symbol") or ""),
        side=str(data.get("side") or ""),
        status=str(data.get("status") or ""),
        order_type=str(data.get("type") or data.get("order_type") or ""),
        qty=dec(data.get("qty")),
        notional=dec(data.get("notional")),
        filled_qty=dec(data.get("filled_qty")),
        filled_avg_price=dec(data.get("filled_avg_price")),
        submitted_at=data.get("submitted_at"),
        filled_at=data.get("filled_at"),
        raw=_public_order_raw(data),
        request_id=request_id,
    )


def _message_from_response(response: httpx.Response, fallback: str) -> str:
    try:
        payload = response.json()
    except ValueError:
        return fallback
    if isinstance(payload, dict):
        for key in ("message", "msg"):
            if payload.get(key):
                return str(payload[key])
    return fallback


def _parse_ts(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _optional_bool(data: dict[str, Any], key: str) -> bool | None:
    if key not in data or data.get(key) is None:
        return None
    return bool(data.get(key))


def _trading_status(
    trading_blocked: bool | None,
    trade_suspended: bool | None,
    account_blocked: bool | None,
) -> str | None:
    """Map Alpaca flags only. None means Alpaca did not return the flags."""
    if trading_blocked is True:
        return "blocked"
    if trade_suspended is True:
        return "suspended_by_user"
    if account_blocked is True:
        return "account_blocked"
    if trading_blocked is False:
        return "enabled"
    return None


def _public_account_raw(data: dict[str, Any]) -> dict[str, Any]:
    keep = [
        "status", "currency", "cash", "equity", "last_equity", "buying_power",
        "portfolio_value", "long_market_value", "short_market_value",
        "trading_blocked", "pattern_day_trader", "trade_suspended_by_user",
        "account_blocked", "multiplier",
    ]
    return {k: data.get(k) for k in keep if k in data}


def _public_position_raw(data: dict[str, Any]) -> dict[str, Any]:
    keep = ["symbol", "qty", "side", "avg_entry_price", "market_value", "unrealized_pl", "current_price"]
    return {k: data.get(k) for k in keep}


def _public_order_raw(data: dict[str, Any]) -> dict[str, Any]:
    keep = [
        "id", "client_order_id", "symbol", "side", "status", "type", "qty", "notional",
        "filled_qty", "filled_avg_price", "submitted_at", "filled_at", "canceled_at", "failed_at",
    ]
    return {k: data.get(k) for k in keep}
