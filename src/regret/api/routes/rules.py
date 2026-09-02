from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from regret.api.deps import current_user
from regret.db.session import get_db
from regret.models.user import User
from regret.services import rules as rule_service

router = APIRouter(prefix="/api/rules", tags=["rules"])


class RuleBody(BaseModel):
    rule_type: str
    name: str
    description: str = ""
    severity: str = "HARD"
    threshold: str | None = None
    custom_expression: str = ""


class RulePatch(BaseModel):
    name: str | None = None
    description: str | None = None
    severity: str | None = None
    threshold: str | None = None
    custom_expression: str | None = None
    enabled: bool | None = None


class TemplateBody(BaseModel):
    template_ids: list[str] | None = None


@router.get("")
def list_rules(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return {
        "rules": [rule_service.public_rule(r) for r in rule_service.list_rules(db, user.id)],
        "templates": rule_service.templates(),
    }


@router.post("")
def create_rule(body: RuleBody, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    rule = rule_service.create_rule(db, user.id, **body.model_dump())
    return {"rule": rule_service.public_rule(rule)}


@router.post("/templates")
def apply_templates(body: TemplateBody, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    created = rule_service.apply_templates(db, user.id, body.template_ids)
    return {"rules": [rule_service.public_rule(r) for r in created]}


@router.patch("/{rule_id}")
def patch_rule(rule_id: str, body: RulePatch, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    rule = rule_service.update_rule(db, user.id, rule_id, **body.model_dump(exclude_unset=True))
    return {"rule": rule_service.public_rule(rule)}


@router.delete("/{rule_id}")
def delete_rule(rule_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    rule_service.delete_rule(db, user.id, rule_id)
    return {"deleted": True}
