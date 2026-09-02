from __future__ import annotations

import json
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from regret import ENGINE_VERSION
from regret.engine.decision import DecisionEngine
from regret.engine.intent import ParsedIntent, validate_intent
from regret.engine.market_analysis import analyze_bars
from regret.engine.risk import RiskEngine
from regret.errors import NotFoundError, ValidationFailed
from regret.market.freshness import FreshnessResult, entry_price_from
from regret.models.analysis import Analysis
from regret.models.journal import JournalEntry
from regret.models.trade_intent import TradeIntent
from regret.providers.portfolio import concentration_after_trade
from regret.security import utcnow
from regret.services import audit, connections, llm, rules as rule_service
from regret.services.proposal import build_order_proposal


decision_engine = DecisionEngine()
risk_engine = RiskEngine()

PORTFOLIO_NEEDED = "Portfolio check unavailable because no brokerage is connected."
MARKET_NEEDED = "Market data is unavailable. Connect a brokerage to use live quotes and bars, or ask the operator to enable a market data source."


def analyze_trade(
    db: Session,
    user_id: str,
    *,
    text: str | None = None,
    symbol: str | None = None,
    side: str | None = None,
    notional: str | float | None = None,
    quantity: str | float | None = None,
    order_type: str | None = None,
    limit_price: str | float | None = None,
    stop_price: str | float | None = None,
    target_price: str | float | None = None,
    propose_stop: bool = False,
    parent_intent_id: str | None = None,
    environment: str | None = None,
) -> dict:
    parsed = _resolve_intent(
        text=text,
        symbol=symbol,
        side=side,
        notional=notional,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit_price,
        stop_price=stop_price,
        target_price=target_price,
    )
    if parsed.missing:
        raise ValidationFailed(
            "Trade request is incomplete: " + ", ".join(parsed.missing) + ".",
            details={"missing": parsed.missing, "parsed": parsed.as_record()},
        )

    conn = connections.get_connection(db, user_id, environment)
    provider = connections.provider_for_user(db, user_id, environment)

    account = None
    existing = None
    asset_tradable = None
    asset_message = ""
    clock = None
    market_open = None
    quote = None
    snapshot = None
    bars = []
    news = []
    market_origin = None
    positions_public = []
    orders_public = []
    positions_raw = []
    market_meta = {
        "symbol": parsed.symbol,
        "asset_type": None,
        "available": False,
        "unavailable_reason": MARKET_NEEDED,
        "source": None,
        "timestamp": None,
        "received_timestamp": None,
        "freshness": None,
        "current": False,
        "live": False,
        "bar_count": 0,
        "last_price": None,
        "last_price_source": None,
    }

    if provider is None:
        freshness = FreshnessResult(
            ok=True,
            message=MARKET_NEEDED,
            age_seconds=None,
            source_timestamp=None,
            received_timestamp=utcnow(),
            source="none",
            market_open=None,
        )
        market = analyze_bars([])
        market.unavailable_reason = MARKET_NEEDED
    else:
        ctx = provider.load_analysis_context(parsed.symbol or "")
        account = ctx.account
        existing = ctx.existing
        clock = ctx.clock
        market_open = clock.is_open if clock else None
        quote = ctx.market.quote
        snapshot = ctx.market.snapshot
        bars = ctx.market.bars
        news = ctx.market.news
        market_origin = ctx.market.source
        positions_raw = ctx.positions
        positions_public = ctx.positions_public()
        orders_public = ctx.orders_public()
        market_meta = ctx.market.as_dict()
        if ctx.asset is not None:
            asset_tradable = ctx.asset.tradable and ctx.asset.status == "active"
            asset_message = "" if asset_tradable else f"{parsed.symbol} is not tradable on the connected brokerage account."
        elif ctx.broker_connected:
            asset_tradable = False
            asset_message = f"{parsed.symbol} was not found as a tradable asset."
        freshness = ctx.market.freshness or FreshnessResult(
            ok=True,
            message=ctx.market.unavailable_reason or MARKET_NEEDED,
            age_seconds=None,
            source_timestamp=None,
            received_timestamp=utcnow(),
            source=ctx.market.source or "none",
            market_open=market_open,
        )
        market = analyze_bars(bars) if bars else analyze_bars([])
        if not market.available:
            market.unavailable_reason = ctx.market.unavailable_reason or MARKET_NEEDED

    entry_price, entry_source = entry_price_from(quote, snapshot)
    if entry_price is None and market.last_close is not None:
        entry_price = market.last_close
        entry_source = "last_daily_close"

    # Zero only when the book was fetched and this symbol is absent from it.
    # A present position with a missing qty/value stays unavailable.
    existing_qty = None
    existing_value = None
    if account is not None:
        if existing is None:
            existing_qty = Decimal("0")
            existing_value = Decimal("0")
        else:
            existing_qty = existing.qty
            existing_value = existing.market_value

    risk = risk_engine.calculate(
        intent=parsed,
        equity=account.equity if account else None,
        buying_power=account.buying_power if account else None,
        entry_price=entry_price,
        existing_position_qty=existing_qty,
        existing_position_value=existing_value,
        proposed_stop=market.proposed_stop,
        use_proposed_stop=propose_stop,
    )
    if account is not None:
        concentration = concentration_after_trade(
            positions_raw,
            account.equity,
            symbol=parsed.symbol or "",
            added_notional=risk.notional,
            side=parsed.side.value if parsed.side else None,
        )
        risk = risk.model_copy(update={"concentration_pct": concentration})

    user_rules = rule_service.as_specs(rule_service.list_rules(db, user_id, enabled_only=True))
    consecutive = _consecutive_losses(db, user_id)
    daily_pl = account.daily_pl_pct() if account else None

    decision = decision_engine.decide(
        intent=parsed,
        market=market,
        risk=risk,
        rules=user_rules,
        daily_loss_pct=daily_pl,
        consecutive_losses=consecutive,
        data_fresh=freshness.ok,
        freshness_message=freshness.message,
        market_open=market_open,
        news_headlines=[n.headline for n in news if n.headline],
        asset_tradable=asset_tradable,
        asset_message=asset_message,
    )

    parent_id = parent_intent_id
    if parent_id:
        parent = db.get(TradeIntent, parent_id)
        if parent is None or parent.user_id != user_id:
            raise NotFoundError("Parent trade intent not found.")

    version = 1
    if parent_id:
        version = (db.scalar(select(func.count()).select_from(Analysis).where(Analysis.intent_id == parent_id)) or 0) + 1

    intent_row = TradeIntent(
        user_id=user_id,
        parent_id=parent_id,
        raw_text=text or "",
        symbol=parsed.symbol or "",
        side=parsed.side.value if parsed.side else "",
        notional=parsed.notional,
        quantity=parsed.quantity,
        order_type=parsed.order_type.value if parsed.order_type else None,
        limit_price=parsed.limit_price,
        stop_price=parsed.stop_price,
        target_price=parsed.target_price,
        parse_source=parsed.parse_source,
        parse_notes=" ".join(parsed.notes),
    )
    db.add(intent_row)
    db.flush()

    report = {
        "market": {
            **market_meta,
            "what": market.as_dict() if market.available else None,
            "statement": (
                market.unavailable_reason
                if not market.available
                else (freshness.message if freshness and not freshness.ok else market.trend_basis)
            ),
        },
        "setup": decision.entry,
        "rules": decision.rules.as_dict(),
        "portfolio": {
            **decision.portfolio,
            "account": account.as_public_dict() if account else None,
            "positions": positions_public,
            "orders": orders_public,
            "existing_position": existing.as_public_dict() if existing else None,
        },
        "risk": decision.risk.as_dict(),
        "why_not": decision.why_not.as_dict(),
        "verdict": {
            "value": decision.verdict.value,
            "reasons": decision.reasons,
            "blocked": decision.blocked,
            "blocked_reason": decision.blocked_reason or None,
            "next_condition": decision.next_condition or None,
            "suggested_notional": format(decision.suggested_notional, "f") if decision.suggested_notional is not None else None,
            "suggested_quantity": format(decision.suggested_quantity, "f") if decision.suggested_quantity is not None else None,
            "incomplete": decision.verdict.value == "INCOMPLETE",
        },
    }
    proposal = build_order_proposal(
        intent=parsed,
        decision=decision,
        entry_source=entry_source,
        broker_connected=conn is not None,
    )
    explanation = llm.explain_decision(
        {
            "instruction": "Explain only these computed sections. Do not invent numbers. If a field is null, say it is unavailable.",
            "verdict": decision.verdict.value,
            "reasons": decision.reasons,
            "report": report,
        }
    )
    ai_note = explanation or "Written explanation is temporarily unavailable. The rule and risk checks below still stand."

    payload = {
        "intent": parsed.as_record(),
        "decision": decision.as_dict(),
        "report": report,
        "freshness": freshness.as_dict(),
        "entry_source": entry_source,
        "broker_connected": conn is not None,
        "market_source": market_origin,
        "market_data": market_meta,
        "capabilities": {
            "market": market.available,
            "rules": True,
            "portfolio": account is not None,
            "execution": conn is not None,
        },
        "account": account.as_public_dict() if account else None,
        "positions": positions_public,
        "orders": orders_public,
        "existing_position": existing.as_public_dict() if existing else None,
        "news": [
            {"id": n.id, "headline": n.headline, "source": n.source, "created_at": n.created_at, "url": n.url}
            for n in news
        ],
        "clock": {
            "is_open": market_open,
            "timestamp": clock.timestamp.isoformat() if clock and clock.timestamp else None,
            "next_open": clock.next_open if clock else None,
            "next_close": clock.next_close if clock else None,
        } if clock or market_open is not None else None,
        "order_proposal": proposal,
        "inputs_used": {
            "symbol": parsed.symbol,
            "side": parsed.side.value if parsed.side else None,
            "notional": format(parsed.notional, "f") if parsed.notional is not None else None,
            "quantity": format(parsed.quantity, "f") if parsed.quantity is not None else None,
            "order_type": parsed.order_type.value if parsed.order_type else None,
            "stop_price": format(parsed.stop_price, "f") if parsed.stop_price is not None else None,
            "target_price": format(parsed.target_price, "f") if parsed.target_price is not None else None,
            "entry_price": format(risk.entry_price, "f") if risk.entry_price is not None else None,
            "entry_source": entry_source,
            "broker_connected": conn is not None,
        },
        "ai_explanation": explanation,
        "ai_available": explanation is not None,
        "ai_fallback": None if explanation else ai_note,
    }

    analysis = Analysis(
        user_id=user_id,
        intent_id=intent_row.id,
        analysis_version=version,
        engine_version=ENGINE_VERSION,
        verdict=decision.verdict.value,
        summary=decision.reasons[0] if decision.reasons else "",
        payload_json=json.dumps(payload, default=str),
        rule_snapshot_json=json.dumps([r.snapshot() for r in user_rules], default=str),
        data_timestamp=freshness.source_timestamp,
        received_timestamp=freshness.received_timestamp or utcnow(),
        data_source=freshness.source,
        environment=conn.environment if conn else "unconnected",
        blocked_reason=decision.blocked_reason,
    )
    db.add(analysis)
    db.flush()

    db.add(
        JournalEntry(
            user_id=user_id,
            intent_id=intent_row.id,
            analysis_id=analysis.id,
            entry_type="analysis",
            symbol=parsed.symbol or "",
            verdict=decision.verdict.value,
            user_action="analyzed",
            summary=analysis.summary,
            payload_json=json.dumps(
                {
                    "analysis_id": analysis.id,
                    "verdict": decision.verdict.value,
                    "idea": parsed.raw_text or parsed.as_record(),
                    "rules_snapshot": [r.snapshot() for r in user_rules],
                    "why_not": decision.why_not.as_dict(),
                    "risk": decision.risk.as_dict(),
                    "portfolio": decision.portfolio,
                    "order_proposal": proposal,
                    "market_data": market_meta,
                    "data_timestamp": freshness.source_timestamp.isoformat() if freshness.source_timestamp else None,
                },
                default=str,
            ),
        )
    )
    audit.record(
        db,
        user_id=user_id,
        action="trade_analyzed",
        entity_type="analysis",
        entity_id=analysis.id,
        symbol=parsed.symbol or "",
        decision_id=analysis.id,
        status=decision.verdict.value,
    )
    audit.record(
        db,
        user_id=user_id,
        action="verdict_produced",
        entity_type="analysis",
        entity_id=analysis.id,
        symbol=parsed.symbol or "",
        decision_id=analysis.id,
        status=decision.verdict.value,
    )
    return serialize_analysis(analysis)


def get_analysis(db: Session, user_id: str, analysis_id: str) -> Analysis:
    row = db.get(Analysis, analysis_id)
    if row is None or row.user_id != user_id:
        raise NotFoundError("Analysis not found.")
    return row


def list_analyses(db: Session, user_id: str, *, limit: int = 50) -> list[Analysis]:
    return list(
        db.scalars(
            select(Analysis)
            .where(Analysis.user_id == user_id)
            .order_by(Analysis.created_at.desc())
            .limit(limit)
        ).all()
    )


def serialize_analysis(row: Analysis) -> dict:
    payload = json.loads(row.payload_json)
    return {
        "analysis_id": row.id,
        "intent_id": row.intent_id,
        "analysis_version": row.analysis_version,
        "engine_version": row.engine_version,
        "verdict": row.verdict,
        "summary": row.summary,
        "blocked_reason": row.blocked_reason or None,
        "data_timestamp": row.data_timestamp.isoformat() if row.data_timestamp else None,
        "received_timestamp": row.received_timestamp.isoformat() if row.received_timestamp else None,
        "data_source": row.data_source,
        "environment": row.environment,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "approval_required": True,
        **payload,
    }


def _resolve_intent(**kwargs) -> ParsedIntent:
    text = (kwargs.get("text") or "").strip()
    has_structured = any(kwargs.get(k) for k in ("symbol", "side", "notional", "quantity"))
    if text and not has_structured:
        return llm.parse_intent_from_text(text)
    if text and has_structured:
        parsed = validate_intent(
            symbol=kwargs.get("symbol"),
            side=kwargs.get("side"),
            notional=kwargs.get("notional"),
            quantity=kwargs.get("quantity"),
            order_type=kwargs.get("order_type"),
            limit_price=kwargs.get("limit_price"),
            stop_price=kwargs.get("stop_price"),
            target_price=kwargs.get("target_price"),
        )
        parsed.raw_text = text
        return parsed
    if has_structured:
        return validate_intent(
            symbol=kwargs.get("symbol"),
            side=kwargs.get("side"),
            notional=kwargs.get("notional"),
            quantity=kwargs.get("quantity"),
            order_type=kwargs.get("order_type"),
            limit_price=kwargs.get("limit_price"),
            stop_price=kwargs.get("stop_price"),
            target_price=kwargs.get("target_price"),
        )
    raise ValidationFailed("Provide a trade description or a structured symbol, side, and size.")


def _consecutive_losses(db: Session, user_id: str) -> int | None:
    rows = list(
        db.scalars(
            select(JournalEntry)
            .where(
                JournalEntry.user_id == user_id,
                JournalEntry.entry_type == "outcome",
                JournalEntry.outcome.in_(["win", "loss"]),
            )
            .order_by(JournalEntry.created_at.desc())
            .limit(20)
        ).all()
    )
    if not rows:
        return None
    count = 0
    for row in rows:
        if row.outcome == "loss":
            count += 1
        else:
            break
    return count
