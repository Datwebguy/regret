from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from regret.engine.indicators import q, safe_div
from regret.engine.intent import ParsedIntent
from regret.types import Side


class RiskResult(BaseModel):
    available: bool
    unavailable_reason: str = ""
    entry_price: Decimal | None = None
    quantity: Decimal | None = None
    notional: Decimal | None = None
    existing_position_value: Decimal | None = None
    existing_position_qty: Decimal | None = None
    post_trade_exposure: Decimal | None = None
    portfolio_percentage_after: Decimal | None = None
    risk_dollars: Decimal | None = None
    risk_percentage: Decimal | None = None
    reward_dollars: Decimal | None = None
    risk_reward: Decimal | None = None
    cash_impact: Decimal | None = None
    buying_power: Decimal | None = None
    buying_power_remaining: Decimal | None = None
    buying_power_sufficient: bool | None = None
    equity: Decimal | None = None
    stop_used: Decimal | None = None
    target_used: Decimal | None = None
    stop_was_proposed: bool = False
    concentration_pct: Decimal | None = None
    missing_inputs: list[str] = []

    model_config = {"arbitrary_types_allowed": True}

    def as_dict(self) -> dict[str, Any]:
        data = self.model_dump()
        for key, value in list(data.items()):
            if isinstance(value, Decimal):
                data[key] = format(value, "f")
        return data


class RiskEngine:
    def calculate(
        self,
        *,
        intent: ParsedIntent,
        equity: Decimal | None,
        buying_power: Decimal | None,
        entry_price: Decimal | None,
        existing_position_qty: Decimal | None,
        existing_position_value: Decimal | None,
        proposed_stop: Decimal | None = None,
        use_proposed_stop: bool = False,
    ) -> RiskResult:
        missing: list[str] = []
        if equity is None:
            missing.append("account equity")
        if entry_price is None:
            missing.append("entry price")
        if intent.quantity is None and intent.notional is None:
            missing.append("order size")
        if missing:
            return RiskResult(
                available=False,
                unavailable_reason="INSUFFICIENT DATA. Risk calculation unavailable because required inputs are missing: "
                + ", ".join(missing)
                + ".",
                missing_inputs=missing,
                equity=q(equity),
                buying_power=q(buying_power),
                entry_price=q(entry_price),
            )

        assert equity is not None
        assert entry_price is not None

        qty = intent.quantity
        notional = intent.notional
        if qty is None and notional is not None:
            qty = notional / entry_price if entry_price != 0 else None
        if notional is None and qty is not None:
            notional = qty * entry_price
        if qty is None or notional is None:
            return RiskResult(
                available=False,
                unavailable_reason="Unable to derive quantity and notional from the provided size and entry price.",
                missing_inputs=["order size"],
                equity=q(equity),
                entry_price=q(entry_price),
            )

        # None means the book is unknown. 0 means Alpaca/the book said there is no position.
        existing_qty = existing_position_qty
        existing_value = existing_position_value
        post_exposure = None
        cash_impact = None
        portfolio_pct_100 = None
        if existing_value is not None:
            if intent.side == Side.SELL:
                post_exposure = existing_value - notional
                cash_impact = notional
            else:
                post_exposure = existing_value + notional
                cash_impact = -notional
            portfolio_pct = safe_div(post_exposure, equity)
            portfolio_pct_100 = portfolio_pct * Decimal("100") if portfolio_pct is not None else None

        stop = intent.stop_price
        stop_was_proposed = False
        if stop is None and use_proposed_stop and proposed_stop is not None:
            stop = proposed_stop
            stop_was_proposed = True

        risk_dollars = None
        risk_pct = None
        if stop is None:
            risk_note_missing = ["stop_price"]
        else:
            risk_note_missing = []
            risk_per_share = abs(entry_price - stop)
            risk_dollars = risk_per_share * qty
            risk_pct = safe_div(risk_dollars, equity)
            if risk_pct is not None:
                risk_pct = risk_pct * Decimal("100")

        reward_dollars = None
        rr = None
        if intent.target_price is not None:
            reward_per_share = abs(intent.target_price - entry_price)
            reward_dollars = reward_per_share * qty
            if stop is not None:
                risk_per_share = abs(entry_price - stop)
                rr = safe_div(reward_per_share, risk_per_share)

        bp_remaining = None
        bp_ok = None
        if buying_power is not None:
            if intent.side == Side.BUY:
                bp_remaining = buying_power - notional
                bp_ok = bp_remaining >= 0
            else:
                bp_remaining = buying_power
                bp_ok = True

        unavailable = ""
        available = True
        if stop is None:
            available = True
            unavailable = "To calculate trade risk in dollars and percent, an invalidation or stop level is required."

        return RiskResult(
            available=available,
            unavailable_reason=unavailable,
            entry_price=q(entry_price),
            quantity=q(qty, Decimal("0.00000001")),
            notional=q(notional),
            existing_position_value=q(existing_value) if existing_value is not None else None,
            existing_position_qty=q(existing_qty, Decimal("0.00000001")) if existing_qty is not None else None,
            post_trade_exposure=q(post_exposure),
            portfolio_percentage_after=q(portfolio_pct_100),
            risk_dollars=q(risk_dollars),
            risk_percentage=q(risk_pct),
            reward_dollars=q(reward_dollars),
            risk_reward=q(rr),
            cash_impact=q(cash_impact),
            buying_power=q(buying_power),
            buying_power_remaining=q(bp_remaining),
            buying_power_sufficient=bp_ok,
            equity=q(equity),
            stop_used=q(stop),
            target_used=q(intent.target_price),
            stop_was_proposed=stop_was_proposed,
            missing_inputs=risk_note_missing,
        )

    def max_notional_for_position_pct(self, equity: Decimal, existing_value: Decimal, max_pct: Decimal, side: Side) -> Decimal | None:
        limit_value = equity * (max_pct / Decimal("100"))
        if side == Side.SELL:
            return None
        remaining = limit_value - existing_value
        if remaining < 0:
            return Decimal("0")
        return remaining

    def max_notional_for_risk(
        self,
        *,
        equity: Decimal,
        entry: Decimal,
        stop: Decimal,
        max_risk_pct: Decimal,
    ) -> Decimal | None:
        risk_per_share = abs(entry - stop)
        if risk_per_share == 0 or entry == 0:
            return None
        max_risk_dollars = equity * (max_risk_pct / Decimal("100"))
        max_qty = max_risk_dollars / risk_per_share
        return max_qty * entry
