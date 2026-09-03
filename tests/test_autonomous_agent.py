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


def test_autonomous_agent_assigned_equity_liquidation(monkeypatch):
    creds = AlpacaCredentials(environment="paper", api_key_id="mock_key", api_secret="mock_secret")
    config = AgentConfig(auto_liquidate_assigned_equities=True)
    agent = AutonomousOptionsAgent(creds, config)

    closed_symbols = []
    monkeypatch.setattr(agent.broker, "close_position", lambda sym: closed_symbols.append(sym))

    # Mock an assigned stock position (e.g. IWM -100 shares from assigned call)
    mock_pos = [
        {"symbol": "IWM", "qty": "-100", "asset_class": "us_equity", "unrealized_pl": 16.0, "market_value": -29384.0}
    ]
    actions = agent._manage_open_positions(mock_pos)
    assert len(actions) == 1
    assert actions[0]["action"] == "ASSIGNED_EQUITY_AUTO_LIQUIDATED"
    assert "IWM" in closed_symbols


def test_autonomous_agent_expiring_option_pin_risk_safeguard(monkeypatch):
    creds = AlpacaCredentials(environment="paper", api_key_id="mock_key", api_secret="mock_secret")
    config = AgentConfig(auto_close_same_day_expiring=True)
    agent = AutonomousOptionsAgent(creds, config)

    closed_symbols = []
    monkeypatch.setattr(agent.broker, "close_position", lambda sym: closed_symbols.append(sym))

    # Mock an option expiring today/yesterday (e.g. 260902 = 2026-09-02)
    mock_pos = [
        {"symbol": "SPY260902C00766000", "qty": "-1", "asset_class": "us_option", "unrealized_pl": 20.0, "market_value": -50.0}
    ]
    actions = agent._manage_open_positions(mock_pos)
    assert len(actions) == 1
    assert actions[0]["action"] == "EXPIRING_OPTION_PIN_RISK_AUTO_CLOSED"
    assert "SPY260902C00766000" in closed_symbols


def test_autonomous_agent_take_profit_and_stop_loss(monkeypatch):
    creds = AlpacaCredentials(environment="paper", api_key_id="mock_key", api_secret="mock_secret")
    agent = AutonomousOptionsAgent(creds)

    closed_symbols = []
    monkeypatch.setattr(agent.broker, "close_position", lambda sym: closed_symbols.append(sym))

    # Mock a future-expiring option with +$60 profit (take profit >= $50)
    mock_pos_tp = [
        {"symbol": "SPY260918C00780000", "qty": "-1", "asset_class": "us_option", "unrealized_pl": 60.0, "market_value": -40.0}
    ]
    actions_tp = agent._manage_open_positions(mock_pos_tp)
    assert actions_tp[0]["action"] == "TAKE_PROFIT_EXECUTED"
    assert "SPY260918C00780000" in closed_symbols

    # Mock a future-expiring option with -$160 loss (stop loss <= -$150)
    mock_pos_sl = [
        {"symbol": "QQQ260918P00500000", "qty": "-1", "asset_class": "us_option", "unrealized_pl": -160.0, "market_value": -260.0}
    ]
    actions_sl = agent._manage_open_positions(mock_pos_sl)
    assert actions_sl[0]["action"] == "STOP_LOSS_EXECUTED"
    assert "QQQ260918P00500000" in closed_symbols
