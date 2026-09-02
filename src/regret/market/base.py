from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from regret.engine.market_analysis import Bar


@dataclass
class Quote:
    symbol: str
    bid: Decimal | None
    ask: Decimal | None
    bid_size: Decimal | None
    ask_size: Decimal | None
    source_timestamp: datetime | None
    received_timestamp: datetime
    source: str

    @property
    def mid(self) -> Decimal | None:
        if self.bid is not None and self.ask is not None:
            return (self.bid + self.ask) / Decimal("2")
        return self.ask or self.bid


@dataclass
class Snapshot:
    symbol: str
    last_trade_price: Decimal | None
    last_trade_timestamp: datetime | None
    quote: Quote | None
    daily_bar: Bar | None
    prev_daily_bar: Bar | None
    received_timestamp: datetime
    source: str
    raw_available_fields: list[str] = field(default_factory=list)


@dataclass
class NewsItem:
    id: str
    headline: str
    source: str
    created_at: str | None
    url: str | None
    symbols: list[str]


class MarketDataProvider(ABC):
    @abstractmethod
    def get_quote(self, symbol: str) -> Quote:
        ...

    @abstractmethod
    def get_bars(self, symbol: str, *, timeframe: str = "1Day", limit: int = 100) -> list[Bar]:
        ...

    @abstractmethod
    def get_snapshot(self, symbol: str) -> Snapshot:
        ...

    @abstractmethod
    def get_news(self, symbol: str, *, limit: int = 5) -> list[NewsItem]:
        ...
