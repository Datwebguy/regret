from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from regret.models.analysis import Analysis
from regret.models.journal import JournalEntry


MIN_SAMPLE = 5


def behavior_insights(db: Session, user_id: str) -> dict:
    executions = list(
        db.scalars(
            select(JournalEntry).where(
                JournalEntry.user_id == user_id,
                JournalEntry.entry_type == "execution",
            )
        ).all()
    )
    analyses = list(db.scalars(select(Analysis).where(Analysis.user_id == user_id)).all())
    outcomes = [e for e in db.scalars(select(JournalEntry).where(JournalEntry.user_id == user_id, JournalEntry.entry_type == "outcome")).all()]

    if len(executions) < MIN_SAMPLE:
        return {
            "available": False,
            "message": "Not enough trading history to produce a reliable behavioral insight.",
            "sample_size": len(executions),
            "minimum_required": MIN_SAMPLE,
            "insights": [],
        }

    followed = [e for e in executions if e.override != "YES"]
    overrides = [e for e in executions if e.override == "YES"]
    insights = [
        f"You followed the REGRET verdict on {len(followed)} of {len(executions)} executed trades.",
        f"You overrode the verdict on {len(overrides)} of {len(executions)} executed trades.",
    ]
    wins = [o for o in outcomes if o.outcome == "win"]
    losses = [o for o in outcomes if o.outcome == "loss"]
    if len(outcomes) >= MIN_SAMPLE:
        insights.append(f"{len(wins)} wins and {len(losses)} losses are recorded from closed outcomes — not from analyses alone.")
    else:
        insights.append("Closed trade outcomes are still fewer than the minimum sample for win-rate statistics.")

    return {
        "available": True,
        "sample_size": len(executions),
        "analysis_count": len(analyses),
        "execution_count": len(executions),
        "override_count": len(overrides),
        "closed_outcome_count": len(outcomes),
        "insights": insights,
    }
