from __future__ import annotations

from decimal import Decimal

from regret.types import RuleSeverity, RuleType


RULE_TEMPLATES: list[dict] = [
    {
        "rule_type": RuleType.MAX_POSITION_PCT.value,
        "name": "Maximum position size",
        "description": "Do not let any single position exceed this percentage of portfolio equity.",
        "severity": RuleSeverity.HARD.value,
        "threshold": "20",
    },
    {
        "rule_type": RuleType.MAX_RISK_PER_TRADE_PCT.value,
        "name": "Maximum risk per trade",
        "description": "Risk no more than this percentage of account equity, measured from entry to stop.",
        "severity": RuleSeverity.HARD.value,
        "threshold": "2",
    },
    {
        "rule_type": RuleType.MIN_RISK_REWARD.value,
        "name": "Minimum risk/reward",
        "description": "Require at least this reward-to-risk ratio when both stop and target are defined.",
        "severity": RuleSeverity.SOFT.value,
        "threshold": "2",
    },
    {
        "rule_type": RuleType.MAX_DAILY_LOSS_PCT.value,
        "name": "Maximum daily loss",
        "description": "Stop opening new positions after this percentage daily loss.",
        "severity": RuleSeverity.HARD.value,
        "threshold": "3",
    },
    {
        "rule_type": RuleType.NO_CHASE_DAILY_MOVE_PCT.value,
        "name": "Do not chase",
        "description": "Do not buy an asset after this percentage daily move.",
        "severity": RuleSeverity.SOFT.value,
        "threshold": "8",
    },
    {
        "rule_type": RuleType.MAX_CONSECUTIVE_LOSSES.value,
        "name": "Consecutive losses",
        "description": "Stop trading after this many consecutive closed losses recorded in REGRET.",
        "severity": RuleSeverity.HARD.value,
        "threshold": "3",
    },
]


def template_threshold(raw: str) -> Decimal:
    return Decimal(raw)
