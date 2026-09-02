from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from regret.brokers.alpaca import AlpacaCredentials
from regret.engine.market_analysis import Bar
from regret.errors import DataUnavailable, IntegrationUnavailable, NotFoundError
from regret.market.base import MarketDataProvider, NewsItem, Quote, Snapshot
from regret.security import utcnow
from regret.types import dec


DATA_URL = "https://data.alpaca.markets"


class AlpacaMarketDataProvider(MarketDataProvider):
    def __init__(self, credentials: AlpacaCredentials, *, feed: str = "iex", timeout: float = 20.0) -> None:
        self.credentials = credentials
        self.feed = feed
        self.timeout = timeout

    def _request(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{DATA_URL}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    url,
                    headers={**self.credentials.headers(), "Accept": "application/json"},
                    params=params,
                )
        except httpx.HTTPError as exc:
            raise IntegrationUnavailable(f"Alpaca market data API is unavailable: {exc.__class__.__name__}.") from exc

        if response.status_code == 401:
            raise IntegrationUnavailable(
                "Market data authorization expired or was revoked.",
                code="alpaca_auth_expired",
                status_code=401,
            )
        if response.status_code == 403:
            raise DataUnavailable(
                "Market data is unavailable. The connected Alpaca account does not have an active data subscription for this feed.",
                code="market_data_subscription_required",
            )
        if response.status_code == 404:
            raise NotFoundError("Market data was not found for this symbol.", code="market_data_not_found")
        if response.status_code == 429:
            raise IntegrationUnavailable("Alpaca market data rate limit reached.", code="alpaca_rate_limited", status_code=429)
        if response.status_code >= 400:
            raise DataUnavailable(_safe_message(response, "Market data request failed."))
        try:
            return response.json()
        except ValueError as exc:
            raise DataUnavailable("Alpaca market data returned a non-JSON response.") from exc

    def get_quote(self, symbol: str) -> Quote:
        data = self._request(f"/v2/stocks/{symbol}/quotes/latest", params={"feed": self.feed})
        quote = data.get("quote") if isinstance(data, dict) else None
        if not isinstance(quote, dict):
            raise DataUnavailable(f"No quote is currently available for {symbol}.")
        received = utcnow()
        return Quote(
            symbol=symbol,
            bid=dec(quote.get("bp")),
            ask=dec(quote.get("ap")),
            bid_size=dec(quote.get("bs")),
            ask_size=dec(quote.get("as")),
            source_timestamp=_parse_ts(quote.get("t")),
            received_timestamp=received,
            source=f"alpaca:{self.feed}:quote",
        )

    def get_bars(self, symbol: str, *, timeframe: str = "1Day", limit: int = 100) -> list[Bar]:
        start = (utcnow() - timedelta(days=220)).date().isoformat()
        data = self._request(
            f"/v2/stocks/{symbol}/bars",
            params={
                "timeframe": timeframe,
                "start": start,
                "limit": limit,
                "feed": self.feed,
                "adjustment": "raw",
            },
        )
        bars_raw = data.get("bars") if isinstance(data, dict) else None
        if not bars_raw:
            raise DataUnavailable(f"No historical bars are currently available for {symbol}.")
        bars: list[Bar] = []
        for item in bars_raw:
            o, h, l, c = dec(item.get("o")), dec(item.get("h")), dec(item.get("l")), dec(item.get("c"))
            v = dec(item.get("v"))
            if None in (o, h, l, c, v):
                continue
            bars.append(
                Bar(
                    timestamp=str(item.get("t") or ""),
                    open=o,
                    high=h,
                    low=l,
                    close=c,
                    volume=v,
                )
            )
        if not bars:
            raise DataUnavailable(f"Bar data for {symbol} did not contain usable OHLC values.")
        return bars

    def get_snapshot(self, symbol: str) -> Snapshot:
        data = self._request(f"/v2/stocks/{symbol}/snapshot", params={"feed": self.feed})
        received = utcnow()
        latest_trade = data.get("latestTrade") or {}
        latest_quote = data.get("latestQuote") or {}
        daily = data.get("dailyBar")
        prev = data.get("prevDailyBar")
        quote = None
        if latest_quote:
            quote = Quote(
                symbol=symbol,
                bid=dec(latest_quote.get("bp")),
                ask=dec(latest_quote.get("ap")),
                bid_size=dec(latest_quote.get("bs")),
                ask_size=dec(latest_quote.get("as")),
                source_timestamp=_parse_ts(latest_quote.get("t")),
                received_timestamp=received,
                source=f"alpaca:{self.feed}:snapshot_quote",
            )
        fields = [k for k, v in data.items() if v]
        return Snapshot(
            symbol=symbol,
            last_trade_price=dec(latest_trade.get("p")),
            last_trade_timestamp=_parse_ts(latest_trade.get("t")),
            quote=quote,
            daily_bar=_bar_from_raw(daily) if daily else None,
            prev_daily_bar=_bar_from_raw(prev) if prev else None,
            received_timestamp=received,
            source=f"alpaca:{self.feed}:snapshot",
            raw_available_fields=fields,
        )

    def get_news(self, symbol: str, *, limit: int = 5) -> list[NewsItem]:
        try:
            data = self._request("/v1beta1/news", params={"symbols": symbol, "limit": limit, "include_content": "false"})
        except DataUnavailable:
            return []
        news = data.get("news") if isinstance(data, dict) else None
        if not news:
            return []
        items: list[NewsItem] = []
        for item in news:
            items.append(
                NewsItem(
                    id=str(item.get("id") or ""),
                    headline=str(item.get("headline") or ""),
                    source=str(item.get("source") or ""),
                    created_at=str(item.get("created_at") or "") or None,
                    url=item.get("url"),
                    symbols=list(item.get("symbols") or []),
                )
            )
        return items

    def get_option_snapshots(self, underlying_symbol: str, *, feed: str = "indicative") -> dict[str, Any]:
        """Fetch option snapshots including quotes, IV, and Greeks for all contracts of an underlying symbol."""
        try:
            data = self._request(f"/v1beta1/options/snapshots/{underlying_symbol.upper()}", params={"feed": feed})
            if isinstance(data, dict) and "snapshots" in data:
                return data["snapshots"]
            if isinstance(data, dict):
                return data
            return {}
        except Exception:
            return {}

    def get_historical_volatility(self, symbol: str, *, days: int = 30) -> Decimal | None:
        """Compute annualized historical volatility from daily close prices."""
        import math
        try:
            bars = self.get_bars(symbol, timeframe="1Day", limit=max(days + 5, 40))
            if len(bars) < 10:
                return None
            closes = [float(b.close) for b in bars[-days:]]
            if len(closes) < 2:
                return None
            returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
            mean_ret = sum(returns) / len(returns)
            variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
            daily_std = math.sqrt(variance)
            annualized_hv = daily_std * math.sqrt(252)
            return Decimal(str(round(annualized_hv, 4)))
        except Exception:
            return None


def _bar_from_raw(item: dict[str, Any]) -> Bar | None:
    o, h, l, c = dec(item.get("o")), dec(item.get("h")), dec(item.get("l")), dec(item.get("c"))
    v = dec(item.get("v")) or dec("0")
    if None in (o, h, l, c):
        return None
    return Bar(timestamp=str(item.get("t") or ""), open=o, high=h, low=l, close=c, volume=v)


def _parse_ts(value: Any) -> datetime | None:
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


def _safe_message(response: httpx.Response, fallback: str) -> str:
    try:
        payload = response.json()
    except ValueError:
        return fallback
    if isinstance(payload, dict) and payload.get("message"):
        return str(payload["message"])
    return fallback
