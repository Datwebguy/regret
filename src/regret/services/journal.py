from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session


def _load_json(raw: str | None):
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []

from regret.errors import NotFoundError
from regret.models.analysis import Analysis
from regret.models.journal import JournalEntry
from regret.models.order import BrokerOrder


def list_entries(db: Session, user_id: str, *, symbol: str | None = None, limit: int = 100) -> list[dict]:
    stmt = select(JournalEntry).where(JournalEntry.user_id == user_id).order_by(JournalEntry.created_at.desc()).limit(limit)
    if symbol:
        stmt = stmt.where(JournalEntry.symbol == symbol.upper())
    return [public_entry(row, db) for row in db.scalars(stmt).all()]


def get_entry(db: Session, user_id: str, entry_id: str) -> dict:
    row = db.get(JournalEntry, entry_id)
    if row is None or row.user_id != user_id:
        raise NotFoundError("Journal entry not found.")
    return public_entry(row, db)


def public_entry(row: JournalEntry, db: Session | None = None) -> dict:
    payload = {}
    if row.payload_json:
        try:
            payload = json.loads(row.payload_json)
        except json.JSONDecodeError:
            payload = {}
    snapshot = None
    alpaca_order_id = payload.get("alpaca_order_id")
    if db is not None and row.analysis_id:
        analysis = db.get(Analysis, row.analysis_id)
        if analysis and analysis.user_id == row.user_id:
            try:
                frozen = json.loads(analysis.payload_json)
            except json.JSONDecodeError:
                frozen = {}
            snapshot = {
                "idea": (frozen.get("intent") or {}).get("raw_text") or frozen.get("intent"),
                "verdict": analysis.verdict,
                "market_data": frozen.get("market_data"),
                "rules_at_the_time": _load_json(analysis.rule_snapshot_json),
                "portfolio": (frozen.get("report") or {}).get("portfolio") or frozen.get("account"),
                "risk": (frozen.get("decision") or {}).get("risk"),
                "why_not": (frozen.get("decision") or {}).get("why_not"),
                "order_proposal": frozen.get("order_proposal"),
                "data_timestamp": analysis.data_timestamp.isoformat() if analysis.data_timestamp else None,
            }
    if db is not None and row.order_id and not alpaca_order_id:
        order = db.get(BrokerOrder, row.order_id)
        if order and order.user_id == row.user_id:
            alpaca_order_id = order.alpaca_order_id or None
    return {
        "id": row.id,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "entry_type": row.entry_type,
        "symbol": row.symbol,
        "verdict": row.verdict,
        "user_action": row.user_action,
        "override": row.override,
        "outcome": row.outcome or None,
        "summary": row.summary,
        "analysis_id": row.analysis_id,
        "order_id": row.order_id,
        "alpaca_order_id": alpaca_order_id or None,
        "payload": payload,
        "snapshot": snapshot,
    }
