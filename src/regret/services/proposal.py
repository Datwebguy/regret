from __future__ import annotations

from typing import Any

from regret.engine.decision import DecisionResult
from regret.engine.intent import ParsedIntent
from regret.types import Verdict


def build_order_proposal(
    *,
    intent: ParsedIntent,
    decision: DecisionResult,
    entry_source: str | None,
    broker_connected: bool,
) -> dict[str, Any]:
    """
    Structured order review. Never submits. Numbers come from the engines only.
    """
    if decision.verdict in {Verdict.REJECT, Verdict.INCOMPLETE}:
        return {
            "allowed": False,
            "submitted": False,
            "status": "not_proposed",
            "reason": decision.blocked_reason or (decision.reasons[0] if decision.reasons else "This verdict cannot become an order."),
            "verdict": decision.verdict.value,
        }

    rules_payload = decision.rules.as_dict()
    hard = rules_payload.get("hard_failures") or []
    unavailable = [c for c in (rules_payload.get("checks") or []) if c.get("result") == "INSUFFICIENT DATA"]
    if hard:
        rules_label = "FAILED"
    elif unavailable and not any(c.get("result") == "PASS" for c in (rules_payload.get("checks") or [])):
        rules_label = "INSUFFICIENT DATA"
    elif unavailable:
        rules_label = "PASS_WITH_GAPS"
    elif not (rules_payload.get("checks") or []):
        rules_label = "NO_RULES"
    else:
        rules_label = "PASS"

    risk = decision.risk
    if not risk.available:
        risk_label = "INSUFFICIENT DATA"
    elif risk.buying_power_sufficient is False:
        risk_label = "FAILED"
    else:
        risk_label = "PASS"

    qty = decision.suggested_quantity if decision.verdict == Verdict.REDUCE and decision.suggested_quantity is not None else intent.quantity
    notional = decision.suggested_notional if decision.verdict == Verdict.REDUCE and decision.suggested_notional is not None else (intent.notional or risk.notional)

    return {
        "allowed": True,
        "submitted": False,
        "status": "proposal",
        "message": "Not submitted. Review and approve before anything is sent.",
        "symbol": intent.symbol,
        "side": (intent.side.value if intent.side else None),
        "quantity": format(qty, "f") if qty is not None else None,
        "order_type": intent.order_type.value if intent.order_type else "market",
        "estimated_notional": format(notional, "f") if notional is not None else None,
        "limit_price": format(intent.limit_price, "f") if intent.limit_price is not None else None,
        "stop_price": format(intent.stop_price, "f") if intent.stop_price is not None else None,
        "entry_basis": entry_source,
        "entry_price": format(risk.entry_price, "f") if risk.entry_price is not None else None,
        "risk": format(risk.risk_dollars, "f") if risk.risk_dollars is not None else None,
        "risk_pct": format(risk.risk_percentage, "f") if risk.risk_percentage is not None else None,
        "portfolio_exposure_after": format(risk.portfolio_percentage_after, "f") if risk.portfolio_percentage_after is not None else None,
        "rules": rules_label,
        "risk_checks": risk_label,
        "verdict": decision.verdict.value,
        "override_required": decision.verdict in {Verdict.WAIT, Verdict.REDUCE},
        "broker_connected": broker_connected,
        "approval_required": True,
    }
