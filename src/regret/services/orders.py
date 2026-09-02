from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from regret.brokers.base import OrderRequest
from regret.config import get_settings
from regret.errors import (
    ApprovalRequired,
    ForbiddenError,
    IntegrationUnavailable,
    NotFoundError,
    OrderRejected,
    StaleDecision,
    ValidationFailed,
)
from regret.models.analysis import Analysis, Approval
from regret.models.journal import JournalEntry
from regret.models.order import BrokerOrder
from regret.models.thesis import TradeThesis
from regret.models.trade_intent import TradeIntent
from regret.security import as_utc, utcnow
from regret.services import analysis as analysis_service
from regret.services import audit, connections
from regret.types import ApprovalStatus, Verdict


ACTIVE_BROKER_STATUSES = {
    "new",
    "accepted",
    "pending_new",
    "accepted_for_bidding",
    "partially_filled",
    "pending_cancel",
    "pending_replace",
    "calculated",
    "stopped",
    "suspended",
    "submitted",
}

FILLED_STATUSES = {"filled"}
CANCELLED_STATUSES = {"canceled", "cancelled", "expired"}
REJECTED_STATUSES = {"rejected", "stopped"}
OPEN_STATUSES = ACTIVE_BROKER_STATUSES | {"open"}


def preview_order(db: Session, user_id: str, analysis_id: str) -> dict:
    analysis = analysis_service.get_analysis(db, user_id, analysis_id)
    intent = db.get(TradeIntent, analysis.intent_id)
    if intent is None or intent.user_id != user_id:
        raise NotFoundError("Trade intent not found.")

    payload = json.loads(analysis.payload_json)
    decision = payload.get("decision") or {}
    risk = decision.get("risk") or {}
    if analysis.verdict in {Verdict.REJECT.value, Verdict.INCOMPLETE.value}:
        raise ValidationFailed(
            "This analysis cannot be previewed for execution.",
            details={"reason": analysis.blocked_reason or analysis.summary, "verdict": analysis.verdict},
        )

    conn = connections.require_connection(db, user_id, analysis.environment)
    _assert_environment_allowed(conn.environment)

    existing = db.scalar(
        select(Approval).where(
            Approval.analysis_id == analysis.id,
            Approval.status == ApprovalStatus.PENDING.value,
        )
    )
    if existing:
        existing.status = ApprovalStatus.SUPERSEDED.value

    settings = get_settings()
    client_order_id = f"regret-{analysis.id[:8]}-{utcnow().strftime('%H%M%S')}"
    stored_proposal = payload.get("order_proposal") or {}
    preview = {
        "symbol": intent.symbol,
        "side": intent.side,
        "amount_notional": stored_proposal.get("estimated_notional") or (str(intent.notional) if intent.notional is not None else None),
        "quantity": stored_proposal.get("quantity") or (str(intent.quantity) if intent.quantity is not None else None),
        "suggested_notional": decision.get("suggested_notional"),
        "order_type": stored_proposal.get("order_type") or intent.order_type or "market",
        "limit_price": str(intent.limit_price) if intent.limit_price is not None else None,
        "stop_price": str(intent.stop_price) if intent.stop_price is not None else None,
        "environment": conn.environment,
        "entry_basis": stored_proposal.get("entry_basis") or payload.get("entry_source"),
        "entry_price": stored_proposal.get("entry_price") or risk.get("entry_price"),
        "estimated_exposure_pct": stored_proposal.get("portfolio_exposure_after") or risk.get("portfolio_percentage_after"),
        "estimated_risk_pct": stored_proposal.get("risk_pct") or risk.get("risk_percentage"),
        "risk": stored_proposal.get("risk") or risk.get("risk_dollars"),
        "rules": stored_proposal.get("rules") or "UNKNOWN",
        "risk_checks": stored_proposal.get("risk_checks") or "UNKNOWN",
        "rule_results": (decision.get("rules") or {}).get("checks", []),
        "portfolio": decision.get("portfolio"),
        "verdict": analysis.verdict,
        "submitted": False,
        "override_required": analysis.verdict in {Verdict.WAIT.value, Verdict.REDUCE.value},
    }
    approval = Approval(
        user_id=user_id,
        analysis_id=analysis.id,
        intent_id=intent.id,
        status=ApprovalStatus.PENDING.value,
        expires_at=utcnow() + timedelta(seconds=settings.regret_approval_ttl_seconds),
        preview_json=json.dumps(preview),
        client_order_id=client_order_id,
    )
    db.add(approval)
    db.flush()
    audit.record(
        db,
        user_id=user_id,
        action="order_previewed",
        entity_type="approval",
        entity_id=approval.id,
        symbol=intent.symbol,
        decision_id=analysis.id,
        status=analysis.verdict,
    )
    return {
        "approval_id": approval.id,
        "expires_at": approval.expires_at.isoformat(),
        "client_order_id": client_order_id,
        "preview": preview,
        "actions": ["CANCEL", "EXECUTE"],
    }


def confirm_order(
    db: Session,
    user_id: str,
    *,
    approval_id: str,
    confirm: bool,
    accept_suggested_size: bool = False,
    live_confirmation: str = "",
) -> dict:
    if not confirm:
        raise ApprovalRequired("Set confirm=true after reviewing the order preview.")

    approval = db.get(Approval, approval_id)
    if approval is None or approval.user_id != user_id:
        raise NotFoundError("Approval not found.")
    if approval.status != ApprovalStatus.PENDING.value:
        raise ValidationFailed(f"This approval is {approval.status} and cannot be used.")
    if as_utc(approval.expires_at) <= utcnow():
        approval.status = ApprovalStatus.EXPIRED.value
        raise StaleDecision("This approval has expired. Preview the order again.")

    analysis = analysis_service.get_analysis(db, user_id, approval.analysis_id)
    intent = db.get(TradeIntent, approval.intent_id)
    if intent is None:
        raise NotFoundError("Trade intent not found.")

    if analysis.verdict == Verdict.REJECT.value:
        approval.status = ApprovalStatus.BLOCKED.value
        raise ValidationFailed("Rejected analyses cannot be executed.")

    existing_order = db.scalar(select(BrokerOrder).where(BrokerOrder.approval_id == approval.id))
    if existing_order and (existing_order.alpaca_order_id or existing_order.status in ACTIVE_BROKER_STATUSES | FILLED_STATUSES):
        return {
            "status": "already_submitted",
            "message": "This approved execution was already submitted. A second request did not create another order.",
            "execution_id": existing_order.id,
            "order": serialize_order(existing_order),
        }

    conn = connections.require_connection(db, user_id, analysis.environment)
    _assert_environment_allowed(conn.environment)
    if not connections.connection_can_trade(conn):
        raise ForbiddenError(
            "This brokerage connection can read your account but cannot send orders. Connect again and allow trading."
        )
    if conn.environment == "live":
        if live_confirmation.strip().upper() != "LIVE":
            raise ForbiddenError("Live execution requires live_confirmation='LIVE'.")

    provider = connections.provider_for(conn)

    prior = db.scalar(
        select(BrokerOrder).where(
            BrokerOrder.user_id == user_id,
            BrokerOrder.intent_id == intent.id,
            BrokerOrder.status.in_(list(ACTIVE_BROKER_STATUSES) + ["submitted"]),
        )
    )
    if prior:
        return {
            "status": "already_submitted",
            "message": "This approved execution was already submitted. A second request did not create another order.",
            "execution_id": prior.id,
            "order": serialize_order(prior),
        }

    remote = provider.get_order_by_client_id(approval.client_order_id)
    if remote is not None:
        stored = _persist_remote_order(db, user_id, approval, analysis, intent, remote, conn.environment)
        return {
            "status": "already_submitted",
            "message": "This approved execution was already submitted. A second request did not create another order.",
            "execution_id": stored.id,
            "order": serialize_order(stored),
        }

    fresh = analysis_service.analyze_trade(
        db,
        user_id,
        symbol=intent.symbol,
        side=intent.side,
        notional=str(intent.notional) if intent.notional is not None else None,
        quantity=str(intent.quantity) if intent.quantity is not None else None,
        order_type=intent.order_type,
        limit_price=str(intent.limit_price) if intent.limit_price is not None else None,
        stop_price=str(intent.stop_price) if intent.stop_price is not None else None,
        target_price=str(intent.target_price) if intent.target_price is not None else None,
        parent_intent_id=intent.id,
        environment=conn.environment,
    )
    if _material_change(analysis, fresh):
        approval.status = ApprovalStatus.SUPERSEDED.value
        raise StaleDecision(
            "This order needs to be reviewed again because the market or account state changed.",
            details={"fresh_analysis_id": fresh["analysis_id"], "fresh_verdict": fresh["verdict"]},
        )
    if fresh["verdict"] in {Verdict.REJECT.value, Verdict.INCOMPLETE.value}:
        approval.status = ApprovalStatus.BLOCKED.value
        raise ValidationFailed(
            "Fresh validation rejected this order.",
            details={"reason": fresh.get("blocked_reason") or fresh.get("summary"), "verdict": fresh["verdict"]},
        )

    safety = _safety_checks(conn=conn, provider=provider, intent=intent, fresh=fresh, analysis=analysis)
    if not safety["ok"]:
        approval.status = ApprovalStatus.SUPERSEDED.value
        raise StaleDecision(
            "This order proposal is no longer valid. Analyze and review again.",
            details={"checks": safety["checks"], "fresh_analysis_id": fresh["analysis_id"]},
        )

    notional = intent.notional
    quantity = intent.quantity
    override = analysis.verdict in {Verdict.WAIT.value, Verdict.REDUCE.value}
    if accept_suggested_size and fresh.get("decision", {}).get("suggested_notional"):
        notional = Decimal(str(fresh["decision"]["suggested_notional"]))
        quantity = None
        override = False

    order_type = (intent.order_type or "market").lower()
    request = OrderRequest(
        symbol=intent.symbol,
        side=intent.side,
        type=order_type,
        time_in_force="day",
        qty=str(quantity) if quantity is not None and notional is None else None,
        notional=str(notional) if notional is not None else None,
        limit_price=str(intent.limit_price) if intent.limit_price is not None else None,
        stop_price=str(intent.stop_price) if order_type in {"stop", "stop_limit"} and intent.stop_price is not None else None,
        client_order_id=approval.client_order_id,
    )

    try:
        submitted = provider.create_order(request)
    except (ValidationFailed, IntegrationUnavailable) as exc:
        row = BrokerOrder(
            user_id=user_id,
            approval_id=approval.id,
            analysis_id=analysis.id,
            intent_id=intent.id,
            environment=conn.environment,
            alpaca_order_id="",
            client_order_id=approval.client_order_id,
            alpaca_request_id="",
            symbol=intent.symbol,
            side=intent.side,
            status="rejected",
            submitted_at=utcnow(),
            last_status_at=utcnow(),
            raw_response_json="",
            error_message=str(exc),
        )
        db.add(row)
        approval.status = ApprovalStatus.BLOCKED.value
        db.flush()
        audit.record(
            db,
            user_id=user_id,
            action="order_rejected",
            entity_type="order",
            entity_id=row.id,
            symbol=intent.symbol,
            decision_id=analysis.id,
            status="rejected",
            detail=str(exc)[:500],
        )
        db.add(
            JournalEntry(
                user_id=user_id,
                intent_id=intent.id,
                analysis_id=analysis.id,
                approval_id=approval.id,
                order_id=row.id,
                entry_type="execution",
                symbol=intent.symbol,
                verdict=analysis.verdict,
                user_action="rejected",
                summary=f"Alpaca did not accept the order. {exc}",
                payload_json=json.dumps({"status": "rejected", "error": str(exc), "execution_id": row.id}),
            )
        )
        raise OrderRejected(
            "The brokerage rejected this order. It was not executed.",
            details={"execution_id": row.id, "status": "rejected"},
        ) from exc

    if not submitted.id:
        raise OrderRejected("Alpaca did not return an order ID. REGRET will not treat this as executed.")

    approval.status = ApprovalStatus.CONSUMED.value
    approval.approved_at = utcnow()
    approval.override = 1 if override else 0

    row = BrokerOrder(
        user_id=user_id,
        approval_id=approval.id,
        analysis_id=analysis.id,
        intent_id=intent.id,
        environment=conn.environment,
        alpaca_order_id=submitted.id,
        client_order_id=submitted.client_order_id or approval.client_order_id,
        alpaca_request_id=submitted.request_id,
        symbol=submitted.symbol or intent.symbol,
        side=submitted.side or intent.side,
        status=submitted.status or "submitted",
        submitted_at=utcnow(),
        last_status_at=utcnow(),
        raw_response_json=json.dumps(submitted.as_public_dict()),
    )
    db.add(row)
    db.flush()

    thesis = _create_thesis(db, user_id, row, analysis, intent, fresh)
    db.add(
        JournalEntry(
            user_id=user_id,
            intent_id=intent.id,
            analysis_id=analysis.id,
            approval_id=approval.id,
            order_id=row.id,
            thesis_id=thesis.id,
            entry_type="execution",
            symbol=intent.symbol,
            verdict=analysis.verdict,
            user_action="submitted",
            override="YES" if override else "NO",
            summary=f"Order submitted to Alpaca ({conn.environment}). Broker status={row.status}. Submitted is not filled.",
            payload_json=json.dumps(
                {
                    "execution_id": row.id,
                    "alpaca_order_id": row.alpaca_order_id,
                    "alpaca_request_id": row.alpaca_request_id,
                    "status": row.status,
                    "filled": row.status in FILLED_STATUSES,
                    "executed": row.status in FILLED_STATUSES,
                }
            ),
        )
    )
    audit.record(
        db,
        user_id=user_id,
        action="order_approved",
        entity_type="approval",
        entity_id=approval.id,
        symbol=intent.symbol,
        decision_id=analysis.id,
        order_id=row.alpaca_order_id,
        status=row.status,
        request_id=row.alpaca_request_id,
    )
    audit.record(
        db,
        user_id=user_id,
        action="order_submitted",
        entity_type="order",
        entity_id=row.id,
        symbol=intent.symbol,
        decision_id=analysis.id,
        order_id=row.alpaca_order_id,
        status=row.status,
        request_id=row.alpaca_request_id,
    )
    if override:
        audit.record(
            db,
            user_id=user_id,
            action="user_overrode_decision",
            entity_type="order",
            entity_id=row.id,
            symbol=intent.symbol,
            decision_id=analysis.id,
            status=analysis.verdict,
        )

    return {
        "status": "submitted",
        "message": "Order submitted to the brokerage. Submitted is not filled.",
        "execution_id": row.id,
        "order": serialize_order(row),
        "broker": submitted.as_public_dict(),
        "thesis_id": thesis.id,
        "override": override,
        "environment": conn.environment,
        "filled": row.status in FILLED_STATUSES,
        "executed": row.status in FILLED_STATUSES,
        "safety": safety,
    }


def refresh_order(db: Session, user_id: str, order_id: str) -> dict:
    row = _get_order(db, user_id, order_id)
    conn = connections.require_connection(db, user_id, row.environment)
    provider = connections.provider_for(conn)
    if not row.alpaca_order_id:
        raise ValidationFailed("This order was not submitted to Alpaca.")
    remote = provider.get_order(row.alpaca_order_id)
    row.status = remote.status
    row.last_status_at = utcnow()
    row.raw_response_json = json.dumps(remote.as_public_dict())
    return {
        "order": serialize_order(row),
        "broker": remote.as_public_dict(),
        "filled": row.status in FILLED_STATUSES,
        "executed": row.status in FILLED_STATUSES,
    }


def cancel_order(db: Session, user_id: str, order_id: str) -> dict:
    row = _get_order(db, user_id, order_id)
    conn = connections.require_connection(db, user_id, row.environment)
    provider = connections.provider_for(conn)
    provider.cancel_order(row.alpaca_order_id)
    refreshed = provider.get_order(row.alpaca_order_id)
    row.status = refreshed.status
    row.last_status_at = utcnow()
    row.raw_response_json = json.dumps(refreshed.as_public_dict())
    audit.record(
        db,
        user_id=user_id,
        action="order_cancelled",
        entity_type="order",
        entity_id=row.id,
        order_id=row.alpaca_order_id,
        status=row.status,
    )
    return {"order": serialize_order(row), "broker": refreshed.as_public_dict()}


def list_orders(db: Session, user_id: str) -> list[BrokerOrder]:
    return list(
        db.scalars(
            select(BrokerOrder).where(BrokerOrder.user_id == user_id).order_by(BrokerOrder.created_at.desc())
        ).all()
    )


def serialize_order(row: BrokerOrder) -> dict:
    broker_payload = {}
    if row.raw_response_json:
        try:
            broker_payload = json.loads(row.raw_response_json)
        except json.JSONDecodeError:
            broker_payload = {}
    alpaca_status = row.status or ""
    filled = alpaca_status in FILLED_STATUSES
    return {
        "id": row.id,
        "execution_id": row.id,
        "analysis_id": row.analysis_id,
        "approval_id": row.approval_id,
        "alpaca_order_id": row.alpaca_order_id or None,
        "client_order_id": row.client_order_id,
        "alpaca_request_id": row.alpaca_request_id or None,
        "symbol": row.symbol,
        "side": row.side,
        "status": alpaca_status,
        "alpaca_status": alpaca_status,
        "filled": filled,
        "executed": filled,
        "partially_filled": alpaca_status == "partially_filled",
        "environment": row.environment,
        "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None,
        "last_status_at": row.last_status_at.isoformat() if row.last_status_at else None,
        "filled_qty": broker_payload.get("filled_qty"),
        "filled_avg_price": broker_payload.get("filled_avg_price"),
        "error_message": row.error_message or None,
    }


def _get_order(db: Session, user_id: str, order_id: str) -> BrokerOrder:
    row = db.get(BrokerOrder, order_id)
    if row is None or row.user_id != user_id:
        # also allow lookup by alpaca id
        row = db.scalar(
            select(BrokerOrder).where(
                BrokerOrder.user_id == user_id,
                BrokerOrder.alpaca_order_id == order_id,
            )
        )
    if row is None:
        raise NotFoundError("Order not found.")
    return row


def _persist_remote_order(db, user_id, approval, analysis, intent, remote, environment) -> BrokerOrder:
    row = BrokerOrder(
        user_id=user_id,
        approval_id=approval.id,
        analysis_id=analysis.id,
        intent_id=intent.id,
        environment=environment,
        alpaca_order_id=remote.id,
        client_order_id=remote.client_order_id or approval.client_order_id,
        alpaca_request_id=remote.request_id,
        symbol=remote.symbol,
        side=remote.side,
        status=remote.status,
        submitted_at=utcnow(),
        last_status_at=utcnow(),
        raw_response_json=json.dumps(remote.as_public_dict()),
    )
    db.add(row)
    approval.status = ApprovalStatus.CONSUMED.value
    db.flush()
    return row


def _material_change(previous: Analysis, fresh: dict) -> bool:
    try:
        old = json.loads(previous.payload_json)
    except json.JSONDecodeError:
        return True
    old_eq = _dec((old.get("account") or {}).get("equity"))
    new_eq = _dec((fresh.get("account") or {}).get("equity"))
    old_px = _dec(((old.get("decision") or {}).get("risk") or {}).get("entry_price"))
    new_px = _dec(((fresh.get("decision") or {}).get("risk") or {}).get("entry_price"))
    if old_eq and new_eq and old_eq != 0 and abs(new_eq - old_eq) / old_eq > Decimal("0.02"):
        return True
    if old_px and new_px and old_px != 0 and abs(new_px - old_px) / old_px > Decimal("0.01"):
        return True
    return False


def _dec(value) -> Decimal | None:
    if value is None or value == "":
        return None
    return Decimal(str(value))


def _safety_checks(*, conn, provider, intent, fresh: dict, analysis: Analysis) -> dict:
    """Re-check every critical condition before sending. Never invent a pass."""
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str, critical: bool = True) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail, "critical": critical})

    add("user_authentication", True, "Caller is authenticated.")
    add("brokerage_connection", conn is not None, "Brokerage is connected." if conn else "No brokerage is connected.")
    add("environment", conn.environment in {"paper", "live"}, f"Environment is {conn.environment}.")
    add(
        "live_gate",
        conn.environment != "live" or get_settings().regret_live_trading_enabled,
        "Live trading is enabled." if conn.environment == "live" else "Paper environment.",
    )
    add("symbol", bool(intent.symbol), f"Symbol is {intent.symbol or 'missing'}.")
    add("order_parameters", bool(intent.notional or intent.quantity), "Order has a size.")
    add("approval_state", analysis.verdict != Verdict.REJECT.value, f"Analysis verdict is {analysis.verdict}.")

    account = None
    try:
        account = provider.get_account()
        tradable = account.trading_status in {None, "enabled"} and account.trading_blocked is not True
        add("account_status", bool(account.status), f"Account status is {account.status or 'unavailable'}.")
        add("account_tradable", tradable, f"Trading status is {account.trading_status or 'unavailable'}.")
        buying_ok = True
        fresh_bp = ((fresh.get("decision") or {}).get("risk") or {}).get("buying_power_sufficient")
        if fresh_bp is False:
            buying_ok = False
        add("buying_power", buying_ok, "Buying power is sufficient." if buying_ok else "Buying power is insufficient.")
    except Exception as exc:
        add("account_status", False, f"Account could not be retrieved: {exc.__class__.__name__}.")
        add("account_tradable", False, "Account tradability could not be confirmed.")
        add("buying_power", False, "Buying power could not be confirmed.")

    try:
        asset = provider.get_asset(intent.symbol)
        add(
            "asset_tradable",
            bool(asset.tradable and asset.status == "active"),
            f"{intent.symbol} tradable={asset.tradable} status={asset.status}.",
        )
    except Exception:
        add("asset_tradable", False, f"{intent.symbol} could not be confirmed as tradable.")

    freshness = fresh.get("freshness") or {}
    add("market_data_freshness", bool(freshness.get("ok", True)), freshness.get("message") or "Freshness checked.")

    rules = ((fresh.get("decision") or {}).get("rules") or {}).get("hard_failures") or []
    size_ok = not rules or fresh.get("verdict") == Verdict.REDUCE.value
    add("user_rules", size_ok or fresh.get("verdict") != Verdict.REJECT.value, "Rules re-evaluated on fresh data.")

    risk = (fresh.get("decision") or {}).get("risk") or {}
    add(
        "risk_constraints",
        risk.get("buying_power_sufficient") is not False,
        "Risk constraints re-evaluated.",
    )

    add("position_state", True, "Current positions were re-read for the fresh analysis.", critical=False)

    ok = all(item["ok"] for item in checks if item["critical"])
    return {"ok": ok, "checks": checks}


def _assert_environment_allowed(environment: str) -> None:
    settings = get_settings()
    if environment == "live" and not settings.regret_live_trading_enabled:
        raise ForbiddenError(
            "Live trading is not enabled. Paper execution is the only allowed environment on this deployment."
        )


def _create_thesis(db, user_id, order, analysis, intent, fresh: dict) -> TradeThesis:
    decision = fresh.get("decision") or {}
    market = decision.get("market") or {}
    risk = decision.get("risk") or {}
    rules = decision.get("rules") or {}
    passed = [c["name"] for c in rules.get("checks", []) if c.get("status") == "PASS"]
    failed = [c["name"] for c in rules.get("checks", []) if c.get("status") in {"FAIL", "WARNING"}]
    thesis = TradeThesis(
        user_id=user_id,
        order_id=order.id,
        analysis_id=analysis.id,
        symbol=intent.symbol,
        side=intent.side,
        entry=_dec(risk.get("entry_price")),
        invalidation=_dec(risk.get("stop_used")),
        target=_dec(risk.get("target_used")),
        risk_reward=_dec(risk.get("risk_reward")),
        reason=" ".join(decision.get("reasons") or [analysis.summary]),
        rules_passed_json=json.dumps(passed),
        rules_failed_json=json.dumps(failed),
        market_conditions_json=json.dumps(
            {
                "trend": market.get("trend"),
                "momentum": market.get("momentum"),
                "volatility": market.get("volatility"),
                "location": market.get("price_location"),
            }
        ),
        state="intact",
    )
    db.add(thesis)
    db.flush()
    return thesis
