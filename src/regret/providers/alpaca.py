from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from regret.brokers.alpaca import AlpacaBrokerAdapter, AlpacaCredentials
from regret.brokers.base import (
    AccountSnapshot,
    AssetInfo,
    ClockInfo,
    OrderRequest,
    OrderSnapshot,
    PositionSnapshot,
)
from regret.errors import DataUnavailable, IntegrationUnavailable, NotFoundError
from regret.market.alpaca import AlpacaMarketDataProvider
from regret.market.base import NewsItem, Quote, Snapshot
from regret.market.freshness import FreshnessResult, evaluate_freshness
from regret.engine.market_analysis import Bar
from regret.providers.portfolio import with_exposure
from regret.security import utcnow


def _last_price(quote: Quote | None, snapshot: Snapshot | None, bars: list[Bar]) -> tuple[str | None, str | None]:
    if quote and quote.mid is not None:
        return format(quote.mid, "f"), "quote_mid"
    if snapshot and snapshot.last_trade_price is not None:
        return format(snapshot.last_trade_price, "f"), "last_trade"
    if snapshot and snapshot.daily_bar is not None:
        return format(snapshot.daily_bar.close, "f"), "daily_bar_close"
    if bars:
        return format(bars[-1].close, "f"), "last_daily_close"
    return None, None


def _parse_bar_ts(value: str) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


@dataclass
class MarketBundle:
    symbol: str
    asset_type: str | None
    available: bool
    unavailable_reason: str = ""
    source: str = ""
    quote: Quote | None = None
    snapshot: Snapshot | None = None
    bars: list[Bar] = field(default_factory=list)
    news: list[NewsItem] = field(default_factory=list)
    freshness: FreshnessResult | None = None

    def as_dict(self) -> dict[str, Any]:
        last_price, last_price_source = _last_price(self.quote, self.snapshot, self.bars)
        live = bool(self.freshness and self.freshness.ok and self.freshness.source and "bars" not in self.freshness.source)
        return {
            "symbol": self.symbol,
            "asset_type": self.asset_type,
            "available": self.available,
            "unavailable_reason": self.unavailable_reason or None,
            "source": self.source or None,
            "timestamp": self.freshness.source_timestamp.isoformat() if self.freshness and self.freshness.source_timestamp else None,
            "received_timestamp": self.freshness.received_timestamp.isoformat() if self.freshness and self.freshness.received_timestamp else None,
            "freshness": self.freshness.as_dict() if self.freshness else None,
            "current": bool(self.freshness.ok) if self.freshness else False,
            "live": live,
            "bar_count": len(self.bars),
            "last_price": last_price,
            "last_price_source": last_price_source,
        }


@dataclass
class AnalysisContext:
    broker_connected: bool
    account: AccountSnapshot | None
    positions: list[PositionSnapshot]
    orders: list[OrderSnapshot]
    existing: PositionSnapshot | None
    asset: AssetInfo | None
    clock: ClockInfo | None
    market: MarketBundle

    def positions_public(self) -> list[dict]:
        equity = self.account.equity if self.account else None
        return [with_exposure(p, equity) for p in self.positions]

    def orders_public(self) -> list[dict]:
        return [order.as_public_dict() for order in self.orders]


class AlpacaProvider:
    """
    Application-facing Alpaca facade.

    Trading and market HTTP stay in the adapters. Services should call this
    object, not Alpaca URLs.
    """

    def __init__(
        self,
        credentials: AlpacaCredentials,
        *,
        feed: str = "iex",
        account_access: bool = True,
        quote_max_age_seconds: int = 60,
    ) -> None:
        self.credentials = credentials
        self.environment = credentials.environment
        self.account_access = account_access
        self.quote_max_age_seconds = quote_max_age_seconds
        self._broker = AlpacaBrokerAdapter(credentials) if account_access else None
        self._market = AlpacaMarketDataProvider(credentials, feed=feed)

    def get_account(self) -> AccountSnapshot:
        return self._require_broker().get_account()

    def get_positions(self) -> list[PositionSnapshot]:
        return self._require_broker().get_positions()

    def get_orders(self, status: str = "open") -> list[OrderSnapshot]:
        return self._require_broker().get_orders(status=status)

    def get_order(self, order_id: str) -> OrderSnapshot:
        return self._require_broker().get_order(order_id)

    def get_order_by_client_id(self, client_order_id: str) -> OrderSnapshot | None:
        return self._require_broker().get_order_by_client_id(client_order_id)

    def get_asset(self, symbol: str) -> AssetInfo:
        return self._require_broker().get_asset(symbol)

    def get_assets(self, *, status: str = "active", asset_class: str = "us_equity") -> list[AssetInfo]:
        return self._require_broker().list_assets(status=status, asset_class=asset_class)

    def get_clock(self) -> ClockInfo:
        return self._require_broker().get_clock()

    def get_market_data(self, symbol: str) -> MarketBundle:
        clean = symbol.strip().upper()
        quote = None
        snapshot = None
        bars: list[Bar] = []
        news: list[NewsItem] = []
        errors: list[str] = []
        asset_type = None
        try:
            snapshot = self._market.get_snapshot(clean)
        except (DataUnavailable, IntegrationUnavailable, NotFoundError) as exc:
            errors.append(str(exc))
        try:
            quote = self._market.get_quote(clean)
        except (DataUnavailable, IntegrationUnavailable, NotFoundError):
            quote = None
        try:
            bars = self._market.get_bars(clean, timeframe="1Day", limit=80)
        except (DataUnavailable, IntegrationUnavailable, NotFoundError) as exc:
            errors.append(str(exc))
        try:
            news = self._market.get_news(clean, limit=5)
        except (DataUnavailable, IntegrationUnavailable, NotFoundError):
            news = []

        if self._broker is not None:
            try:
                asset = self._broker.get_asset(clean)
                asset_type = asset.asset_class or None
            except (NotFoundError, IntegrationUnavailable):
                asset_type = None

        market_open = None
        if self._broker is not None:
            try:
                market_open = self._broker.get_clock().is_open
            except IntegrationUnavailable:
                market_open = None

        has_live_stamp = bool(
            (quote and quote.source_timestamp) or (snapshot and snapshot.last_trade_timestamp)
        )
        if has_live_stamp:
            freshness = evaluate_freshness(
                quote=quote,
                snapshot=snapshot,
                market_open=market_open,
                max_age_seconds=self.quote_max_age_seconds,
            )
        elif bars:
            freshness = FreshnessResult(
                ok=True,
                message="Live quote is unavailable. Structure is calculated from daily bars and is not a live tape.",
                age_seconds=None,
                source_timestamp=_parse_bar_ts(bars[-1].timestamp),
                received_timestamp=utcnow(),
                source=f"alpaca:{self.feed}:bars",
                market_open=market_open,
            )
        else:
            freshness = evaluate_freshness(
                quote=quote,
                snapshot=snapshot,
                market_open=market_open,
                max_age_seconds=self.quote_max_age_seconds,
            )
        available = bool(bars) or quote is not None or (snapshot and snapshot.last_trade_price is not None)
        return MarketBundle(
            symbol=clean,
            asset_type=asset_type,
            available=available,
            unavailable_reason="" if available else (errors[0] if errors else "Market data is unavailable."),
            source=freshness.source,
            quote=quote,
            snapshot=snapshot,
            bars=bars,
            news=news,
            freshness=freshness,
        )

    def create_order(self, request: OrderRequest) -> OrderSnapshot:
        return self._require_broker().submit_order(request)

    def cancel_order(self, order_id: str) -> None:
        self._require_broker().cancel_order(order_id)

    def replace_order(self, order_id: str, request: OrderRequest) -> OrderSnapshot:
        return self._require_broker().replace_order(order_id, request)

    def subscribe_to_updates(self) -> dict[str, Any]:
        return {
            "available": False,
            "message": "Live brokerage streams are not enabled. REGRET reads account, orders and prices on request.",
        }

    def book(self) -> dict[str, Any]:
        """Single retrieval path for the user's real Alpaca book. Never invents fields."""
        account = self.get_account()
        positions = self.get_positions()
        orders = self.get_orders(status="open")
        return {
            "connected": True,
            "environment": self.environment,
            "source": "alpaca",
            "retrieved_at": utcnow().isoformat(),
            "account": account.as_public_dict(),
            "positions": [with_exposure(p, account.equity) for p in positions],
            "orders": [order.as_public_dict() for order in orders],
            "updates": self.subscribe_to_updates(),
        }

    def load_analysis_context(self, symbol: str) -> AnalysisContext:
        account = None
        positions: list[PositionSnapshot] = []
        orders: list[OrderSnapshot] = []
        existing = None
        asset = None
        clock = None
        if self.account_access and self._broker is not None:
            account = self._broker.get_account()
            positions = self._broker.get_positions()
            try:
                orders = self._broker.get_orders(status="open")
            except IntegrationUnavailable:
                orders = []
            existing = next((p for p in positions if p.symbol.upper() == symbol.upper()), None)
            try:
                asset = self._broker.get_asset(symbol)
            except NotFoundError:
                asset = None
            try:
                clock = self._broker.get_clock()
            except IntegrationUnavailable:
                clock = None
        market = self.get_market_data(symbol)
        return AnalysisContext(
            broker_connected=self.account_access,
            account=account,
            positions=positions,
            orders=orders,
            existing=existing,
            asset=asset,
            clock=clock,
            market=market,
        )

    def _require_broker(self) -> AlpacaBrokerAdapter:
        if self._broker is None:
            raise IntegrationUnavailable(
                "Portfolio check unavailable because no brokerage is connected.",
                code="alpaca_not_connected",
                status_code=409,
            )
        return self._broker
