from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from regret import ENGINE_VERSION
from regret.engine.intent import ParsedIntent
from regret.engine.market_analysis import MarketAnalysis
from regret.engine.risk import RiskEngine, RiskResult
from regret.engine.rules import RuleEvaluation, RuleEngine, RuleSpec
from regret.engine.why_not import WhyNotEngine, WhyNotResult
from regret.types import RuleType, Side, Verdict


class DecisionResult(BaseModel):
    verdict: Verdict
    reasons: list[str] = Field(default_factory=list)
    suggested_notional: Decimal | None = None
    suggested_quantity: Decimal | None = None
    reduce_reason: str = ""
    next_condition: str = ""
    blocked: bool = False
    blocked_reason: str = ""
    engine_version: str = ENGINE_VERSION
    market: MarketAnalysis
    risk: RiskResult
    rules: RuleEvaluation
    why_not: WhyNotResult
    entry: dict[str, Any] = Field(default_factory=dict)
    portfolio: dict[str, Any] = Field(default_factory=dict)
    approval_required: bool = True

    model_config = {"arbitrary_types_allowed": True}

    def as_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "reasons": self.reasons,
            "suggested_notional": format(self.suggested_notional, "f") if self.suggested_notional is not None else None,
            "suggested_quantity": format(self.suggested_quantity, "f") if self.suggested_quantity is not None else None,
            "reduce_reason": self.reduce_reason,
            "next_condition": self.next_condition or None,
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "engine_version": self.engine_version,
            "market": self.market.as_dict(),
            "risk": self.risk.as_dict(),
            "rules": self.rules.as_dict(),
            "why_not": self.why_not.as_dict(),
            "entry": self.entry,
            "setup": self.entry,
            "portfolio": self.portfolio,
            "approval_required": self.approval_required,
            "incomplete": self.verdict == Verdict.INCOMPLETE,
        }


class DecisionEngine:
    def __init__(self) -> None:
        self.rules = RuleEngine()
        self.risk_engine = RiskEngine()
        self.why_not = WhyNotEngine()

    def decide(
        self,
        *,
        intent: ParsedIntent,
        market: MarketAnalysis,
        risk: RiskResult,
        rules: list[RuleSpec],
        daily_loss_pct: Decimal | None,
        consecutive_losses: int | None,
        data_fresh: bool,
        freshness_message: str,
        market_open: bool | None,
        news_headlines: list[str] | None,
        asset_tradable: bool | None,
        asset_message: str = "",
    ) -> DecisionResult:
        rule_eval = self.rules.evaluate(
            rules=rules,
            intent=intent,
            risk=risk,
            market=market,
            daily_loss_pct=daily_loss_pct,
            consecutive_losses=consecutive_losses,
        )
        why = self.why_not.evaluate(
            intent=intent,
            market=market,
            risk=risk,
            rules=rule_eval,
            news_headlines=news_headlines,
            consecutive_losses=consecutive_losses,
            data_fresh=data_fresh,
            market_open=market_open,
        )

        entry = {
            "quality": None,
            "trend": market.trend,
            "momentum": market.momentum,
            "volatility": market.volatility,
            "location": market.price_location,
            "risk_reward": format(risk.risk_reward, "f") if risk.risk_reward is not None else None,
            "preferred_entry": format(market.last_close, "f") if market.last_close is not None else None,
            "invalidation": format(risk.stop_used, "f") if risk.stop_used is not None else None,
            "target": format(risk.target_used, "f") if risk.target_used is not None else None,
            "notes": [],
        }
        if not market.available:
            entry["notes"].append(market.unavailable_reason)
        else:
            entry["notes"].append(market.trend_basis)
            entry["notes"].append(market.location_basis)

        portfolio_available = risk.equity is not None
        portfolio = {
            "available": portfolio_available,
            "reason": None
            if portfolio_available
            else "Portfolio check unavailable because no brokerage is connected.",
            "equity": format(risk.equity, "f") if risk.equity is not None else None,
            "buying_power": format(risk.buying_power, "f") if risk.buying_power is not None else None,
            "current_exposure": format(risk.existing_position_value, "f") if risk.existing_position_value is not None else None,
            "after_trade": format(risk.post_trade_exposure, "f") if risk.post_trade_exposure is not None else None,
            "portfolio_percentage_after": format(risk.portfolio_percentage_after, "f") if risk.portfolio_percentage_after is not None else None,
            "buying_power_sufficient": risk.buying_power_sufficient,
        }

        reasons: list[str] = []
        verdict = Verdict.BUY
        blocked = False
        blocked_reason = ""
        suggested_notional = None
        suggested_qty = None
        reduce_reason = ""

        if asset_tradable is False:
            return DecisionResult(
                verdict=Verdict.REJECT,
                reasons=[asset_message or "This asset is not tradable on the connected account."],
                blocked=True,
                blocked_reason=asset_message or "Asset is not tradable.",
                market=market,
                risk=risk,
                rules=rule_eval,
                why_not=why,
                entry=entry,
                portfolio=portfolio,
            )

        if not data_fresh and market.available:
            return DecisionResult(
                verdict=Verdict.REJECT,
                reasons=[freshness_message or "Current market data is not fresh enough to safely evaluate this trade."],
                blocked=True,
                blocked_reason="DECISION BLOCKED. Current market data is not fresh enough to safely evaluate this trade.",
                market=market,
                risk=risk,
                rules=rule_eval,
                why_not=why,
                entry=entry,
                portfolio=portfolio,
            )

        if not market.available:
            reasons = [
                market.unavailable_reason
                or "REGRET cannot complete this verdict because required market data is unavailable."
            ]
            if not portfolio_available:
                reasons.append("Portfolio check unavailable because no brokerage is connected.")
            return DecisionResult(
                verdict=Verdict.INCOMPLETE,
                reasons=reasons,
                blocked=False,
                blocked_reason="INCOMPLETE. Required market data is unavailable.",
                next_condition="The decision can be completed once live market data is available.",
                market=market,
                risk=risk,
                rules=rule_eval,
                why_not=why,
                entry=entry,
                portfolio=portfolio,
            )

        if risk.buying_power_sufficient is False:
            return DecisionResult(
                verdict=Verdict.REJECT,
                reasons=["Insufficient buying power for the requested order."],
                blocked=True,
                blocked_reason="Insufficient buying power.",
                market=market,
                risk=risk,
                rules=rule_eval,
                why_not=why,
                entry=entry,
                portfolio=portfolio,
            )

        size_failures = [
            c for c in rule_eval.hard_failures
            if c.rule_type in {RuleType.MAX_POSITION_PCT.value, RuleType.MAX_RISK_PER_TRADE_PCT.value}
        ]
        other_hard = [c for c in rule_eval.hard_failures if c not in size_failures]

        if other_hard:
            reasons = [c.message for c in other_hard]
            return DecisionResult(
                verdict=Verdict.REJECT,
                reasons=reasons,
                blocked=True,
                blocked_reason=reasons[0],
                market=market,
                risk=risk,
                rules=rule_eval,
                why_not=why,
                entry=entry,
                portfolio=portfolio,
            )

        if size_failures and risk.equity is not None and risk.entry_price is not None:
            candidates: list[Decimal] = []
            reasons_reduce: list[str] = []
            for check in size_failures:
                if check.rule_type == RuleType.MAX_POSITION_PCT.value and check.threshold is not None:
                    max_n = self.risk_engine.max_notional_for_position_pct(
                        risk.equity,
                        risk.existing_position_value or Decimal("0"),
                        check.threshold,
                        intent.side or Side.BUY,
                    )
                    if max_n is not None:
                        candidates.append(max_n)
                        reasons_reduce.append(check.message)
                if (
                    check.rule_type == RuleType.MAX_RISK_PER_TRADE_PCT.value
                    and check.threshold is not None
                    and risk.stop_used is not None
                    and intent.side != Side.SELL
                ):
                    max_n = self.risk_engine.max_notional_for_risk(
                        equity=risk.equity,
                        entry=risk.entry_price,
                        stop=risk.stop_used,
                        max_risk_pct=check.threshold,
                    )
                    if max_n is not None:
                        candidates.append(max_n)
                        reasons_reduce.append(check.message)
            if candidates:
                suggested_notional = max(Decimal("0"), min(candidates))
                suggested_qty = suggested_notional / risk.entry_price if risk.entry_price else None
                reduce_reason = " ".join(reasons_reduce)
                current = risk.notional or Decimal("0")
                if suggested_notional < current:
                    return DecisionResult(
                        verdict=Verdict.REDUCE,
                        reasons=reasons_reduce,
                        suggested_notional=suggested_notional,
                        suggested_quantity=suggested_qty,
                        reduce_reason=reduce_reason,
                        market=market,
                        risk=risk,
                        rules=rule_eval,
                        why_not=why,
                        entry=entry,
                        portfolio=portfolio,
                    )

        wait_reasons: list[str] = []
        if intent.side == Side.BUY and market.price_location == "near resistance":
            wait_reasons.append("Current price is near the calculated 20-session resistance.")
        if intent.side == Side.BUY and market.momentum == "overbought":
            wait_reasons.append("RSI indicates an overbought condition at the current close.")
        chase = next((c for c in rule_eval.soft_warnings if c.rule_type == RuleType.NO_CHASE_DAILY_MOVE_PCT.value), None)
        if chase:
            wait_reasons.append(chase.message)
        if intent.side == Side.BUY and market.trend == "bearish" and market.price_location == "near resistance":
            wait_reasons.append("Trend is bearish and price is extended.")

        if wait_reasons:
            next_condition = "The decision can change if price pulls back from this extended area."
            return DecisionResult(
                verdict=Verdict.WAIT,
                reasons=wait_reasons,
                next_condition=next_condition,
                market=market,
                risk=risk,
                rules=rule_eval,
                why_not=why,
                entry=entry,
                portfolio=portfolio,
            )

        reasons = ["The current setup fits the available market data and the rules that could be evaluated."]
        if not portfolio_available:
            reasons.append("Portfolio check unavailable because no brokerage is connected.")
        if rule_eval.soft_warnings:
            reasons.append("Soft warnings are present and should be reviewed before execution.")
        return DecisionResult(
            verdict=Verdict.BUY,
            reasons=reasons,
            market=market,
            risk=risk,
            rules=rule_eval,
            why_not=why,
            entry=entry,
            portfolio=portfolio,
        )
