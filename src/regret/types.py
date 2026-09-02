from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TradingEnvironment(str, Enum):
    PAPER = "paper"
    LIVE = "live"


class Verdict(str, Enum):
    BUY = "BUY"
    WAIT = "WAIT"
    REDUCE = "REDUCE"
    REJECT = "REJECT"
    INCOMPLETE = "INCOMPLETE"


class RuleType(str, Enum):
    MAX_POSITION_PCT = "max_position_pct"
    MAX_RISK_PER_TRADE_PCT = "max_risk_per_trade_pct"
    MIN_RISK_REWARD = "min_risk_reward"
    MAX_DAILY_LOSS_PCT = "max_daily_loss_pct"
    NO_CHASE_DAILY_MOVE_PCT = "no_chase_daily_move_pct"
    MAX_CONSECUTIVE_LOSSES = "max_consecutive_losses"
    CUSTOM = "custom"


class RuleSeverity(str, Enum):
    HARD = "HARD"
    SOFT = "SOFT"


class RuleResultStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    UNAVAILABLE = "UNAVAILABLE"


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class ConnectionMethod(str, Enum):
    OAUTH = "oauth"
    API_KEY = "api_key"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    CONSUMED = "consumed"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    BLOCKED = "blocked"


class ThesisState(str, Enum):
    INTACT = "intact"
    APPROACHING_INVALIDATION = "approaching_invalidation"
    APPROACHING_TARGET = "approaching_target"
    INVALIDATED = "invalidated"
    TARGET_REACHED = "target_reached"
    CHANGED = "changed"
    UNAVAILABLE = "unavailable"


def dec(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def dec_required(value: Any, name: str) -> Decimal:
    parsed = dec(value)
    if parsed is None:
        raise ValueError(f"{name} is required")
    return parsed


class MoneyFields(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    def model_dump_jsonable(self) -> dict[str, Any]:
        payload = self.model_dump()
        return _jsonable(payload)


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value
