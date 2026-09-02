from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from regret.engine.intent import ParsedIntent
from regret.engine.market_analysis import MarketAnalysis
from regret.engine.risk import RiskResult
from regret.types import RuleResultStatus, RuleSeverity, RuleType, Side, dec


class RuleSpec(BaseModel):
    id: str
    rule_type: RuleType
    name: str
    description: str = ""
    severity: RuleSeverity
    threshold: Decimal | None = None
    custom_expression: str = ""
    version: int = 1
    enabled: bool = True

    model_config = {"arbitrary_types_allowed": True}

    def snapshot(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "rule_type": self.rule_type.value,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "threshold": format(self.threshold, "f") if self.threshold is not None else None,
            "custom_expression": self.custom_expression,
            "version": self.version,
            "enabled": self.enabled,
        }


class RuleCheck(BaseModel):
    rule_id: str
    name: str
    rule_type: str
    severity: str
    status: RuleResultStatus
    threshold: Decimal | None = None
    actual: Decimal | None = None
    difference: Decimal | None = None
    result: str = ""
    message: str
    version: int = 1

    model_config = {"arbitrary_types_allowed": True}

    def as_dict(self) -> dict[str, Any]:
        result = self.result or (
            "FAILED"
            if self.status == RuleResultStatus.FAIL
            else "INSUFFICIENT DATA"
            if self.status == RuleResultStatus.UNAVAILABLE
            else self.status.value
        )
        required = format(self.threshold, "f") if self.threshold is not None else None
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "rule_type": self.rule_type,
            "severity": self.severity,
            "status": self.status.value,
            "result": result,
            "threshold": required,
            "required": required,
            "actual": format(self.actual, "f") if self.actual is not None else None,
            "difference": format(self.difference, "f") if self.difference is not None else None,
            "message": self.message,
            "reason": self.message,
            "version": self.version,
        }


class RuleEvaluation(BaseModel):
    checks: list[RuleCheck] = Field(default_factory=list)
    hard_failures: list[RuleCheck] = Field(default_factory=list)
    soft_warnings: list[RuleCheck] = Field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "checks": [c.as_dict() for c in self.checks],
            "hard_failures": [c.as_dict() for c in self.hard_failures],
            "soft_warnings": [c.as_dict() for c in self.soft_warnings],
        }


class RuleEngine:
    def evaluate(
        self,
        *,
        rules: list[RuleSpec],
        intent: ParsedIntent,
        risk: RiskResult,
        market: MarketAnalysis,
        daily_loss_pct: Decimal | None,
        consecutive_losses: int | None,
    ) -> RuleEvaluation:
        checks: list[RuleCheck] = []
        for rule in rules:
            if not rule.enabled:
                continue
            checks.append(
                self._eval_one(
                    rule,
                    intent=intent,
                    risk=risk,
                    market=market,
                    daily_loss_pct=daily_loss_pct,
                    consecutive_losses=consecutive_losses,
                )
            )
        hard = [c for c in checks if c.status == RuleResultStatus.FAIL and c.severity == RuleSeverity.HARD.value]
        soft = [c for c in checks if c.status == RuleResultStatus.WARNING or (
            c.status == RuleResultStatus.FAIL and c.severity == RuleSeverity.SOFT.value
        )]
        return RuleEvaluation(checks=checks, hard_failures=hard, soft_warnings=soft)

    def _eval_one(
        self,
        rule: RuleSpec,
        *,
        intent: ParsedIntent,
        risk: RiskResult,
        market: MarketAnalysis,
        daily_loss_pct: Decimal | None,
        consecutive_losses: int | None,
    ) -> RuleCheck:
        if rule.rule_type == RuleType.MAX_POSITION_PCT:
            return self._compare(
                rule,
                actual=risk.portfolio_percentage_after,
                op="lte",
                missing_msg="Position limit cannot be evaluated because portfolio percentage after the trade is unavailable.",
                fail_msg=lambda a, t: f"Post-trade exposure {a}% exceeds the {t}% position limit.",
                pass_msg=lambda a, t: f"Post-trade exposure {a}% is within the {t}% position limit.",
            )
        if rule.rule_type == RuleType.MAX_RISK_PER_TRADE_PCT:
            if risk.risk_percentage is None:
                return self._unavailable(rule, "Risk-per-trade cannot be evaluated because a stop/invalidation is not defined.")
            return self._compare(
                rule,
                actual=risk.risk_percentage,
                op="lte",
                missing_msg="Risk-per-trade cannot be evaluated.",
                fail_msg=lambda a, t: f"Trade risk {a}% exceeds the {t}% per-trade limit.",
                pass_msg=lambda a, t: f"Trade risk {a}% is within the {t}% per-trade limit.",
            )
        if rule.rule_type == RuleType.MIN_RISK_REWARD:
            if risk.risk_reward is None:
                return self._unavailable(
                    rule,
                    "Minimum risk/reward cannot be evaluated because stop and target are both required.",
                )
            return self._compare(
                rule,
                actual=risk.risk_reward,
                op="gte",
                missing_msg="Minimum risk/reward cannot be evaluated.",
                fail_msg=lambda a, t: f"Risk/reward {a} is below the required {t}.",
                pass_msg=lambda a, t: f"Risk/reward {a} meets the required {t}.",
            )
        if rule.rule_type == RuleType.MAX_DAILY_LOSS_PCT:
            if daily_loss_pct is None:
                return self._unavailable(rule, "Daily loss cannot be evaluated because today's account P/L is unavailable.")
            # daily_loss_pct is negative when losing
            loss = -daily_loss_pct if daily_loss_pct < 0 else Decimal("0")
            return self._compare(
                rule,
                actual=loss,
                op="lte",
                missing_msg="Daily loss cannot be evaluated.",
                fail_msg=lambda a, t: f"Today's loss {a}% has reached the {t}% daily loss limit.",
                pass_msg=lambda a, t: f"Today's loss {a}% is within the {t}% daily loss limit.",
            )
        if rule.rule_type == RuleType.NO_CHASE_DAILY_MOVE_PCT:
            if market.daily_change_pct is None:
                return self._unavailable(rule, "Chase rule cannot be evaluated because the daily change is unavailable.")
            move = abs(market.daily_change_pct)
            chasing = intent.side == Side.BUY and market.daily_change_pct > 0
            if not chasing:
                return RuleCheck(
                    rule_id=rule.id,
                    name=rule.name,
                    rule_type=rule.rule_type.value,
                    severity=rule.severity.value,
                    status=RuleResultStatus.PASS,
                    threshold=rule.threshold,
                    actual=market.daily_change_pct,
                    message=f"Daily change is {format(market.daily_change_pct, 'f')}%. Chase condition (buying after an up-move) is not met.",
                    version=rule.version,
                )
            return self._compare(
                rule,
                actual=move,
                op="lte",
                missing_msg="Chase rule cannot be evaluated.",
                fail_msg=lambda a, t: f"Asset is up {a}% today, above the {t}% chase threshold.",
                pass_msg=lambda a, t: f"Daily move {a}% is within the {t}% chase threshold.",
            )
        if rule.rule_type == RuleType.MAX_CONSECUTIVE_LOSSES:
            if consecutive_losses is None:
                return self._unavailable(
                    rule,
                    "Consecutive-loss rule cannot be evaluated because there is not enough closed-trade history in REGRET.",
                )
            return self._compare(
                rule,
                actual=Decimal(consecutive_losses),
                op="lt",
                missing_msg="Consecutive-loss rule cannot be evaluated.",
                fail_msg=lambda a, t: f"{int(a)} consecutive losses meets/exceeds the limit of {t}.",
                pass_msg=lambda a, t: f"{int(a)} consecutive losses is below the limit of {t}.",
            )
        if rule.rule_type == RuleType.CUSTOM:
            return self._eval_custom(rule, risk=risk, market=market)
        return self._unavailable(rule, f"Unknown rule type {rule.rule_type}.")

    def _eval_custom(self, rule: RuleSpec, *, risk: RiskResult, market: MarketAnalysis) -> RuleCheck:
        """
        Custom rules are structured, not free-text LLM rules.
        Supported expression: field,op,value  e.g. atr_pct,lt,5
        """
        expr = (rule.custom_expression or "").strip()
        if not expr:
            return self._unavailable(rule, "Custom rule has no structured expression.")
        parts = [p.strip() for p in expr.split(",")]
        if len(parts) != 3:
            return self._unavailable(rule, "Custom rule expression must be field,op,value.")
        field, op, raw_value = parts
        actual = _field_value(field, risk=risk, market=market)
        if actual is None:
            return self._unavailable(rule, f"Custom rule field '{field}' is unavailable from current data.")
        try:
            threshold = Decimal(raw_value)
        except Exception:
            return self._unavailable(rule, "Custom rule value is not numeric.")
        # temporarily override threshold for compare
        cloned = rule.model_copy(update={"threshold": threshold})
        return self._compare(
            cloned,
            actual=actual,
            op=op,
            missing_msg="Custom rule cannot be evaluated.",
            fail_msg=lambda a, t: f"{field} {a} failed {op} {t}.",
            pass_msg=lambda a, t: f"{field} {a} satisfies {op} {t}.",
        )

    def _compare(
        self,
        rule: RuleSpec,
        *,
        actual: Decimal | None,
        op: str,
        missing_msg: str,
        fail_msg,
        pass_msg,
    ) -> RuleCheck:
        if actual is None or rule.threshold is None:
            return self._unavailable(rule, missing_msg)
        ok = {
            "lte": actual <= rule.threshold,
            "lt": actual < rule.threshold,
            "gte": actual >= rule.threshold,
            "gt": actual > rule.threshold,
            "eq": actual == rule.threshold,
        }.get(op)
        if ok is None:
            return self._unavailable(rule, f"Unsupported comparison '{op}'.")
        status = RuleResultStatus.PASS if ok else (
            RuleResultStatus.FAIL if rule.severity == RuleSeverity.HARD else RuleResultStatus.WARNING
        )
        if not ok and rule.severity == RuleSeverity.SOFT:
            status = RuleResultStatus.WARNING
        msg = pass_msg(_fmt(actual), _fmt(rule.threshold)) if ok else fail_msg(_fmt(actual), _fmt(rule.threshold))
        result = "PASS" if ok else "FAILED" if status == RuleResultStatus.FAIL else "WARNING"
        return RuleCheck(
            rule_id=rule.id,
            name=rule.name,
            rule_type=rule.rule_type.value,
            severity=rule.severity.value,
            status=status,
            threshold=rule.threshold,
            actual=actual,
            difference=actual - rule.threshold,
            result=result,
            message=msg,
            version=rule.version,
        )

    def _unavailable(self, rule: RuleSpec, message: str) -> RuleCheck:
        return RuleCheck(
            rule_id=rule.id,
            name=rule.name,
            rule_type=rule.rule_type.value,
            severity=rule.severity.value,
            status=RuleResultStatus.UNAVAILABLE,
            threshold=rule.threshold,
            actual=None,
            difference=None,
            result="INSUFFICIENT DATA",
            message=message,
            version=rule.version,
        )


def _fmt(value: Decimal) -> str:
    return format(value, "f")


def _field_value(field: str, *, risk: RiskResult, market: MarketAnalysis) -> Decimal | None:
    mapping = {
        "portfolio_percentage_after": risk.portfolio_percentage_after,
        "risk_percentage": risk.risk_percentage,
        "risk_reward": risk.risk_reward,
        "atr_pct": market.atr_pct,
        "daily_change_pct": market.daily_change_pct,
        "rsi14": market.rsi14,
        "location": market.location,
        "volume_ratio": market.volume_ratio,
    }
    return mapping.get(field)
