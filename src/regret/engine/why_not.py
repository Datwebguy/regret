from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from regret.engine.intent import ParsedIntent
from regret.engine.market_analysis import MarketAnalysis
from regret.engine.risk import RiskResult
from regret.engine.rules import RuleEvaluation
from regret.types import RuleResultStatus, Side


class WhyNotItem(BaseModel):
    code: str
    title: str
    severity: str
    message: str
    source: str
    actual: str | None = None
    required: str | None = None
    difference: str | None = None
    rule_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "title": self.title,
            "severity": self.severity,
            "message": self.message,
            "source": self.source,
            "actual": self.actual,
            "required": self.required,
            "difference": self.difference,
            "rule_id": self.rule_id,
        }


class WhyNotResult(BaseModel):
    items: list[WhyNotItem] = Field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "items": [i.as_dict() for i in self.items],
            "count": len(self.items),
        }


class WhyNotEngine:
    def evaluate(
        self,
        *,
        intent: ParsedIntent,
        market: MarketAnalysis,
        risk: RiskResult,
        rules: RuleEvaluation,
        news_headlines: list[str] | None = None,
        consecutive_losses: int | None = None,
        data_fresh: bool = True,
        market_open: bool | None = None,
    ) -> WhyNotResult:
        items: list[WhyNotItem] = []

        for check in rules.checks:
            actual = format(check.actual, "f") if check.actual is not None else None
            required = format(check.threshold, "f") if check.threshold is not None else None
            difference = format(check.difference, "f") if check.difference is not None else None
            if check.status == RuleResultStatus.FAIL:
                title = "Portfolio concentration" if check.rule_type == "max_position_pct" else "Rule failure"
                items.append(WhyNotItem(
                    code="rule_violation",
                    title=title,
                    severity="high" if check.severity == "HARD" else "medium",
                    message=check.message,
                    source="rules",
                    actual=actual,
                    required=required,
                    difference=difference,
                    rule_id=check.rule_id,
                ))
            elif check.status == RuleResultStatus.WARNING:
                items.append(WhyNotItem(
                    code="rule_warning",
                    title="Rule warning",
                    severity="medium",
                    message=check.message,
                    source="rules",
                    actual=actual,
                    required=required,
                    difference=difference,
                    rule_id=check.rule_id,
                ))

        if intent.side == Side.BUY and market.price_location == "near resistance":
            items.append(WhyNotItem(
                code="entry_extension",
                title="Market condition",
                severity="medium",
                message="The required entry condition has not been confirmed. Price is near the calculated 20-session high.",
                source="market",
                actual=market.price_location,
                required="not near resistance",
            ))

        if intent.side == Side.BUY and market.trend == "bearish":
            items.append(WhyNotItem(
                code="conflicting_trend",
                title="Market condition",
                severity="medium",
                message=f"Requested buy while calculated trend is bearish. {market.trend_basis}",
                source="market",
                actual=market.trend,
                required="non-bearish trend for a buy",
            ))

        if market.volatility == "high":
            items.append(WhyNotItem(
                code="high_volatility",
                title="Market condition",
                severity="low",
                message=market.volatility_basis or "Calculated volatility is high relative to price.",
                source="market",
                actual=format(market.atr_pct, "f") if market.atr_pct is not None else "high",
                required=None,
            ))

        if risk.buying_power_sufficient is False:
            items.append(WhyNotItem(
                code="buying_power",
                title="Buying power",
                severity="high",
                message="Buying power is insufficient for the requested order size.",
                source="portfolio",
                actual=format(risk.buying_power, "f") if risk.buying_power is not None else None,
                required=format(risk.notional, "f") if risk.notional is not None else None,
            ))

        if "stop_price" in risk.missing_inputs:
            items.append(WhyNotItem(
                code="missing_stop",
                title="Insufficient data",
                severity="medium",
                message="No invalidation/stop was provided, so dollar risk cannot be calculated.",
                source="risk",
                actual=None,
                required="stop_price",
            ))

        if consecutive_losses is not None and consecutive_losses >= 2:
            items.append(WhyNotItem(
                code="recent_losses",
                title="Recent losses",
                severity="medium",
                message=f"{consecutive_losses} consecutive closed losses are recorded in the journal.",
                source="behavior",
                actual=str(consecutive_losses),
                required=None,
            ))

        if not data_fresh:
            items.append(WhyNotItem(
                code="stale_data",
                title="Stale market data",
                severity="high",
                message="Market data is not fresh enough for a safe entry decision.",
                source="data",
            ))

        if market_open is False:
            items.append(WhyNotItem(
                code="market_closed",
                title="Market condition",
                severity="low",
                message="The equity market is currently closed. Last available prices are being used.",
                source="market",
                actual="closed",
                required=None,
            ))

        if news_headlines:
            items.append(WhyNotItem(
                code="recent_news",
                title="Recent headlines",
                severity="low",
                message="Recent headlines exist for this symbol. Review them before entering. REGRET does not invent news summaries.",
                source="news",
                actual=str(len(news_headlines)),
            ))

        return WhyNotResult(items=items)
