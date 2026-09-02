"""
Test suite for Autonomous AI Options Trading Agent.
"""

from decimal import Decimal
import pytest

from regret.agents.autonomous_agent import AutonomousOptionsAgent, AgentConfig
from regret.brokers.alpaca import AlpacaCredentials


def test_autonomous_agent_init():
    creds = AlpacaCredentials(environment="paper", api_key_id="mock_key", api_secret="mock_secret")
    config = AgentConfig(
        symbols=["SPY", "QQQ"],
        min_iv_rank=50,
        max_loss_per_trade=Decimal("500"),
        max_daily_loss=Decimal("2000"),
        max_open_positions=5,
    )
    agent = AutonomousOptionsAgent(creds, config)
    assert agent.config.symbols == ["SPY", "QQQ"]
    assert agent.config.min_iv_rank == 50
    assert agent.risk_gates.max_loss_per_trade == Decimal("500")


def test_autonomous_agent_run_cycle():
    creds = AlpacaCredentials(environment="paper", api_key_id="mock_key", api_secret="mock_secret")
    config = AgentConfig(
        symbols=["SPY"],
        min_iv_rank=50,
        max_loss_per_trade=Decimal("500"),
        max_daily_loss=Decimal("2000"),
    )
    agent = AutonomousOptionsAgent(creds, config)
    
    # Run single cycle
    cycle_result = agent.run_cycle()
    
    assert cycle_result.cycle_id.startswith("cycle-")
    assert "SPY" in cycle_result.scanned_symbols
    assert cycle_result.status in ["success", "idle", "halted_max_positions", "error"]
    
    # Verify stats
    stats = agent.get_stats()
    assert stats["initial_starting_balance"] == 100000.0
    assert "net_pl_dollars" in stats
    assert stats["competition"] == "Alpaca AI Trading Agents Hackathon"
