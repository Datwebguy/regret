from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from regret.market.base import Quote, Snapshot
from regret.security import utcnow


@dataclass
class FreshnessResult:
    ok: bool
    message: str
    age_seconds: float | None
    source_timestamp: datetime | None
    received_timestamp: datetime | None
    source: str
    market_open: bool | None

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "message": self.message,
            "age_seconds": self.age_seconds,
            "source_timestamp": self.source_timestamp.isoformat() if self.source_timestamp else None,
            "received_timestamp": self.received_timestamp.isoformat() if self.received_timestamp else None,
            "source": self.source,
            "market_open": self.market_open,
        }


def evaluate_freshness(
    *,
    quote: Quote | None,
    snapshot: Snapshot | None,
    market_open: bool | None,
    max_age_seconds: int,
) -> FreshnessResult:
    source_ts = None
    received = utcnow()
    source = "unknown"
    if quote and quote.source_timestamp:
        source_ts = quote.source_timestamp
        received = quote.received_timestamp
        source = quote.source
    elif snapshot and snapshot.last_trade_timestamp:
        source_ts = snapshot.last_trade_timestamp
        received = snapshot.received_timestamp
        source = snapshot.source
    elif snapshot:
        received = snapshot.received_timestamp
        source = snapshot.source

    if source_ts is None:
        if market_open is False:
            return FreshnessResult(
                ok=True,
                message="Market is closed. Using the last available Alpaca snapshot. Decision will note that live quotes are unavailable.",
                age_seconds=None,
                source_timestamp=None,
                received_timestamp=received,
                source=source,
                market_open=market_open,
            )
        return FreshnessResult(
            ok=False,
            message="DECISION BLOCKED. Current market data is not fresh enough to safely evaluate this trade. No source timestamp was returned.",
            age_seconds=None,
            source_timestamp=None,
            received_timestamp=received,
            source=source,
            market_open=market_open,
        )

    now = utcnow()
    if source_ts.tzinfo is None:
        source_ts = source_ts.replace(tzinfo=timezone.utc)
    age = (now - source_ts).total_seconds()

    if market_open is False:
        return FreshnessResult(
            ok=True,
            message="Market is closed. Last trade/quote timestamp is from the prior session and is acceptable for analysis, not as a live quote.",
            age_seconds=age,
            source_timestamp=source_ts,
            received_timestamp=received,
            source=source,
            market_open=market_open,
        )

    if age > max_age_seconds:
        return FreshnessResult(
            ok=False,
            message=(
                f"DECISION BLOCKED. Current market data is not fresh enough to safely evaluate this trade. "
                f"Quote age is {int(age)}s; maximum allowed while the market is open is {max_age_seconds}s."
            ),
            age_seconds=age,
            source_timestamp=source_ts,
            received_timestamp=received,
            source=source,
            market_open=market_open,
        )
    return FreshnessResult(
        ok=True,
        message=f"Market data is current (age {int(age)}s, source {source}).",
        age_seconds=age,
        source_timestamp=source_ts,
        received_timestamp=received,
        source=source,
        market_open=market_open,
    )


def entry_price_from(quote: Quote | None, snapshot: Snapshot | None):
    if quote and quote.mid is not None:
        return quote.mid, "quote_mid"
    if snapshot and snapshot.last_trade_price is not None:
        return snapshot.last_trade_price, "last_trade"
    if snapshot and snapshot.daily_bar is not None:
        return snapshot.daily_bar.close, "daily_bar_close"
    return None, None
