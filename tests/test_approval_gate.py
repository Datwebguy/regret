from datetime import timedelta

from regret.models.analysis import Analysis, Approval
from regret.models.trade_intent import TradeIntent
from regret.security import utcnow
from regret.services import orders as order_service
from regret.types import ApprovalStatus
from tests.conftest import register


def test_confirm_without_flag_is_rejected(client):
    register(client, "gate@example.com")
    response = client.post("/api/orders/confirm", json={"approval_id": "missing", "confirm": False})
    assert response.status_code == 409
    assert response.json()["error"] == "approval_required"


def test_execute_requires_existing_approval(client):
    register(client, "gate2@example.com")
    response = client.post("/api/orders/confirm", json={"approval_id": "does-not-exist", "confirm": True})
    assert response.status_code == 404


def test_expired_approval_cannot_execute(db):
    from regret.services import auth as auth_service

    user = auth_service.register_user(db, email="expire@example.com", password="super-secret-pass")
    intent = TradeIntent(user_id=user.id, symbol="NVDA", side="buy", notional=1000, parse_source="test")
    db.add(intent)
    db.flush()
    analysis = Analysis(
        user_id=user.id,
        intent_id=intent.id,
        analysis_version=1,
        engine_version="1.0.0",
        verdict="BUY",
        summary="ok",
        payload_json="{}",
        rule_snapshot_json="[]",
        environment="paper",
    )
    db.add(analysis)
    db.flush()
    approval = Approval(
        user_id=user.id,
        analysis_id=analysis.id,
        intent_id=intent.id,
        status=ApprovalStatus.PENDING.value,
        expires_at=utcnow() - timedelta(seconds=1),
        preview_json="{}",
        client_order_id="regret-expired",
    )
    db.add(approval)
    db.commit()

    from regret.errors import StaleDecision
    import pytest

    with pytest.raises(StaleDecision):
        order_service.confirm_order(db, user.id, approval_id=approval.id, confirm=True)


def test_health_does_not_invent_market_data(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    body = health.json()
    assert "price" not in body
    assert "equity" not in body
    assert body["live_trading_enabled"] is False
