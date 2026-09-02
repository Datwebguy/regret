from __future__ import annotations

from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from regret.engine.rules import RuleSpec
from regret.engine.templates import RULE_TEMPLATES
from regret.errors import NotFoundError, ValidationFailed
from regret.models.trading_rule import TradingRule
from regret.services import audit
from regret.types import RuleSeverity, RuleType


def list_rules(db: Session, user_id: str, *, enabled_only: bool = False) -> list[TradingRule]:
    stmt = select(TradingRule).where(TradingRule.user_id == user_id).order_by(TradingRule.created_at.asc())
    if enabled_only:
        stmt = stmt.where(TradingRule.enabled.is_(True))
    return list(db.scalars(stmt).all())


def get_rule(db: Session, user_id: str, rule_id: str) -> TradingRule:
    rule = db.get(TradingRule, rule_id)
    if rule is None or rule.user_id != user_id:
        raise NotFoundError("Rule not found.")
    return rule


def create_rule(
    db: Session,
    user_id: str,
    *,
    rule_type: str,
    name: str,
    description: str = "",
    severity: str = "HARD",
    threshold: str | float | Decimal | None = None,
    custom_expression: str = "",
) -> TradingRule:
    parsed_type = _parse_type(rule_type)
    parsed_sev = _parse_severity(severity)
    if not name.strip():
        raise ValidationFailed("Rule name is required.")
    thresh = _parse_threshold(threshold)
    if parsed_type != RuleType.CUSTOM and thresh is None:
        raise ValidationFailed("This rule type requires a numeric threshold.")
    if parsed_type == RuleType.CUSTOM and not custom_expression.strip():
        raise ValidationFailed("Custom rules require a structured expression: field,op,value.")
    rule = TradingRule(
        user_id=user_id,
        rule_type=parsed_type.value,
        name=name.strip()[:160],
        description=(description or "").strip(),
        severity=parsed_sev.value,
        threshold=thresh,
        custom_expression=custom_expression.strip(),
        enabled=True,
        version=1,
    )
    db.add(rule)
    db.flush()
    audit.record(db, user_id=user_id, action="rule_created", entity_type="rule", entity_id=rule.id)
    return rule


def update_rule(db: Session, user_id: str, rule_id: str, **changes) -> TradingRule:
    rule = get_rule(db, user_id, rule_id)
    if "name" in changes and changes["name"] is not None:
        rule.name = str(changes["name"]).strip()[:160]
    if "description" in changes and changes["description"] is not None:
        rule.description = str(changes["description"])
    if "severity" in changes and changes["severity"] is not None:
        rule.severity = _parse_severity(changes["severity"]).value
    if "threshold" in changes and changes["threshold"] is not None:
        rule.threshold = _parse_threshold(changes["threshold"])
    if "custom_expression" in changes and changes["custom_expression"] is not None:
        rule.custom_expression = str(changes["custom_expression"]).strip()
    if "enabled" in changes and changes["enabled"] is not None:
        rule.enabled = bool(changes["enabled"])
    rule.version += 1
    audit.record(db, user_id=user_id, action="rule_changed", entity_type="rule", entity_id=rule.id, detail=str(rule.version))
    return rule


def delete_rule(db: Session, user_id: str, rule_id: str) -> None:
    rule = get_rule(db, user_id, rule_id)
    db.delete(rule)
    audit.record(db, user_id=user_id, action="rule_deleted", entity_type="rule", entity_id=rule_id)


def apply_templates(db: Session, user_id: str, template_ids: list[str] | None = None) -> list[TradingRule]:
    created: list[TradingRule] = []
    existing_types = {r.rule_type for r in list_rules(db, user_id)}
    for template in RULE_TEMPLATES:
        if template_ids is not None and template["rule_type"] not in template_ids:
            continue
        if template["rule_type"] in existing_types:
            continue
        created.append(
            create_rule(
                db,
                user_id,
                rule_type=template["rule_type"],
                name=template["name"],
                description=template["description"],
                severity=template["severity"],
                threshold=template["threshold"],
            )
        )
    return created


def as_specs(rules: list[TradingRule]) -> list[RuleSpec]:
    specs: list[RuleSpec] = []
    for rule in rules:
        thresh = Decimal(str(rule.threshold)) if rule.threshold is not None else None
        specs.append(
            RuleSpec(
                id=rule.id,
                rule_type=RuleType(rule.rule_type),
                name=rule.name,
                description=rule.description,
                severity=RuleSeverity(rule.severity),
                threshold=thresh,
                custom_expression=rule.custom_expression,
                version=rule.version,
                enabled=rule.enabled,
            )
        )
    return specs


def public_rule(rule: TradingRule) -> dict:
    return {
        "id": rule.id,
        "rule_type": rule.rule_type,
        "name": rule.name,
        "description": rule.description,
        "severity": rule.severity,
        "threshold": str(rule.threshold) if rule.threshold is not None else None,
        "custom_expression": rule.custom_expression,
        "enabled": rule.enabled,
        "version": rule.version,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }


def templates() -> list[dict]:
    return list(RULE_TEMPLATES)


def _parse_type(value: str) -> RuleType:
    try:
        return RuleType(value)
    except ValueError as exc:
        raise ValidationFailed("Unsupported rule type.") from exc


def _parse_severity(value: str) -> RuleSeverity:
    try:
        return RuleSeverity(value.upper())
    except ValueError as exc:
        raise ValidationFailed("Severity must be HARD or SOFT.") from exc


def _parse_threshold(value) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationFailed("Threshold must be numeric.") from exc
    if parsed < 0:
        raise ValidationFailed("Threshold cannot be negative.")
    return parsed
