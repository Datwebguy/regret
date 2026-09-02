"""
API Routes for Autonomous AI Options Trading Agent.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from regret.agents.autonomous_agent import AgentConfig, AutonomousOptionsAgent
from regret.api.deps import current_user, optional_user
from regret.brokers.alpaca import AlpacaCredentials
from regret.config import get_settings
from regret.db.session import get_db
from regret.models.user import User
from regret.services import connections

router = APIRouter(prefix="/api/agent", tags=["agent"])

# Global singleton agent instance per worker process
_agent_instance: AutonomousOptionsAgent | None = None


def _get_agent(user: User | None, db: Session) -> AutonomousOptionsAgent:
    global _agent_instance
    creds = None
    if user:
        conn = connections.connection_for_execution(db, user.id, "paper")
        if conn:
            creds = connections.credentials_for(conn)
    
    if creds is None:
        settings = get_settings()
        creds = AlpacaCredentials(
            environment=settings.regret_default_trading_environment,
            api_key_id=settings.alpaca_api_key or settings.alpaca_data_api_key_id,
            api_secret=settings.alpaca_secret_key or settings.alpaca_data_api_secret_key,
        )

    if _agent_instance is None or _agent_instance.credentials.api_key_id != creds.api_key_id:
        _agent_instance = AutonomousOptionsAgent(creds)
    return _agent_instance


class AgentRunBody(BaseModel):
    symbols: list[str] | None = None
    min_iv_rank: int | None = None


@router.post("/run")
def run_agent_cycle(
    body: AgentRunBody | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Trigger a single autonomous scan, risk check, and execution cycle."""
    agent = _get_agent(user, db)
    if body and body.symbols:
        agent.config.symbols = body.symbols
    if body and body.min_iv_rank is not None:
        agent.config.min_iv_rank = body.min_iv_rank

    result = agent.run_cycle()
    return result.as_dict()


@router.get("/stats")
def get_agent_stats(
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve Hackathon Competition P&L stats ($100k starting balance baseline) and agent status."""
    agent = _get_agent(user, db)
    return agent.get_stats()



@router.get("/history")
def get_agent_history(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve recent autonomous trading cycles and decisions."""
    agent = _get_agent(user, db)
    return {
        "cycles": [c.as_dict() for c in reversed(agent.history[-20:])],
        "total_cycles": len(agent.history),
    }
