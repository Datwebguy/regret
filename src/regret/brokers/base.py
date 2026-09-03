from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class AccountSnapshot:
    account_id: str
    account_number: str
    status: str | None
    currency: str | None
    cash: Decimal | None
    equity: Decimal | None
    last_equity: Decimal | None
    buying_power: Decimal | None
    portfolio_value: Decimal | None
    long_market_value: Decimal | None
    short_market_value: Decimal | None
    trading_blocked: bool | None
    pattern_day_trader: bool | None
    trade_suspended_by_user: bool | None = None
    account_blocked: bool | None = None
    trading_status: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)
    source_timestamp: datetime | None = None
    received_timestamp: datetime | None = None

    def daily_pl_pct(self) -> Decimal | None:
        if self.equity is None or self.last_equity is None or self.last_equity == 0:
            return None
        return (self.equity - self.last_equity) / self.last_equity * Decimal("100")

    def as_public_dict(self) -> dict[str, Any]:
        def f(v: Decimal | None) -> str | None:
            return format(v, "f") if v is not None else None

        return {
            "account_id": self.account_id,
            "account_number": self.account_number,
            "status": self.status,
            "currency": self.currency,
            "cash": f(self.cash),
            "equity": f(self.equity),
            "last_equity": f(self.last_equity),
            "buying_power": f(self.buying_power),
            "portfolio_value": f(self.portfolio_value),
            "long_market_value": f(self.long_market_value),
            "short_market_value": f(self.short_market_value),
            "trading_blocked": self.trading_blocked,
            "pattern_day_trader": self.pattern_day_trader,
            "trade_suspended_by_user": self.trade_suspended_by_user,
            "account_blocked": self.account_blocked,
            "trading_status": self.trading_status,
            "daily_pl_pct": f(self.daily_pl_pct()),
            "source_timestamp": self.source_timestamp.isoformat() if self.source_timestamp else None,
            "received_timestamp": self.received_timestamp.isoformat() if self.received_timestamp else None,
        }


@dataclass
class PositionSnapshot:
    symbol: str
    qty: Decimal | None
    side: str
    avg_entry_price: Decimal | None
    market_value: Decimal | None
    cost_basis: Decimal | None
    unrealized_pl: Decimal | None
    unrealized_plpc: Decimal | None
    current_price: Decimal | None
    raw: dict[str, Any] = field(default_factory=dict)

    def as_public_dict(self) -> dict[str, Any]:
        def f(v: Decimal | None) -> str | None:
            return format(v, "f") if v is not None else None

        return {
            "symbol": self.symbol,
            "qty": f(self.qty),
            "side": self.side,
            "avg_entry_price": f(self.avg_entry_price),
            "market_value": f(self.market_value),
            "cost_basis": f(self.cost_basis),
            "unrealized_pl": f(self.unrealized_pl),
            "unrealized_plpc": f(self.unrealized_plpc),
            "current_price": f(self.current_price),
        }


@dataclass
class OrderSnapshot:
    id: str
    client_order_id: str
    symbol: str
    side: str
    status: str
    order_type: str
    qty: Decimal | None
    notional: Decimal | None
    filled_qty: Decimal | None
    filled_avg_price: Decimal | None
    submitted_at: str | None
    filled_at: str | None
    raw: dict[str, Any] = field(default_factory=dict)
    request_id: str = ""

    def as_public_dict(self) -> dict[str, Any]:
        def f(v: Decimal | None) -> str | None:
            return format(v, "f") if v is not None else None

        return {
            "id": self.id,
            "client_order_id": self.client_order_id,
            "symbol": self.symbol,
            "side": self.side,
            "status": self.status,
            "order_type": self.order_type,
            "qty": f(self.qty),
            "notional": f(self.notional),
            "filled_qty": f(self.filled_qty),
            "filled_avg_price": f(self.filled_avg_price),
            "submitted_at": self.submitted_at,
            "filled_at": self.filled_at,
        }


@dataclass
class AssetInfo:
    symbol: str
    tradable: bool
    status: str
    asset_class: str
    name: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClockInfo:
    timestamp: datetime | None
    is_open: bool
    next_open: str | None
    next_close: str | None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderRequest:
    symbol: str
    side: str
    type: str
    time_in_force: str = "day"
    qty: str | None = None
    notional: str | None = None
    limit_price: str | None = None
    stop_price: str | None = None
    client_order_id: str | None = None


class BrokerAdapter(ABC):
    environment: str

    @abstractmethod
    def get_account(self) -> AccountSnapshot:
        ...

    @abstractmethod
    def get_positions(self) -> list[PositionSnapshot]:
        ...

    @abstractmethod
    def get_orders(self, status: str = "open") -> list[OrderSnapshot]:
        ...

    @abstractmethod
    def get_order(self, order_id: str) -> OrderSnapshot:
        ...

    @abstractmethod
    def get_order_by_client_id(self, client_order_id: str) -> OrderSnapshot | None:
        ...

    @abstractmethod
    def submit_order(self, request: OrderRequest) -> OrderSnapshot:
        ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> None:
        ...

    @abstractmethod
    def replace_order(self, order_id: str, request: OrderRequest) -> OrderSnapshot:
        ...

    @abstractmethod
    def get_asset(self, symbol: str) -> AssetInfo:
        ...

    @abstractmethod
    def list_assets(self, *, status: str = "active", asset_class: str = "us_equity") -> list[AssetInfo]:
        ...

    @abstractmethod
    def get_clock(self) -> ClockInfo:
        ...

    @abstractmethod
    def close_position(self, symbol_or_asset_id: str, *, qty: str | None = None, percentage: str | None = None) -> OrderSnapshot:
        ...

    @abstractmethod
    def close_all_positions(self, *, cancel_orders: bool = True) -> list[OrderSnapshot]:
        ...
