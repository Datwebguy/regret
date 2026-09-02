"""
Test suite for options strategy module.

Run with: pytest tests/test_options_strategy.py -v
"""

from decimal import Decimal
import pytest

from regret.strategies.iv_rank_screening import (
    GreekData,
    CreditSpreadSetup,
)
from regret.engine.options_risk_gates import OptionsRiskGates, GateStatus
from regret.services.options_strategy import OptionsStrategyService
from regret.brokers.alpaca import AlpacaCredentials


def test_credit_spread_setup():
    """Test CreditSpreadSetup data model."""
    setup = CreditSpreadSetup(
        symbol="SPY",
        setup_type="bull_call_spread",
        expiration="2026-09-10",
        short_strike=Decimal("580"),
        long_strike=Decimal("585"),
        short_bid=Decimal("1.50"),
        short_ask=Decimal("1.60"),
        long_bid=Decimal("0.80"),
        long_ask=Decimal("0.90"),
        estimated_credit=Decimal("0.70"),
        max_loss=Decimal("430"),
        max_profit=Decimal("70"),
        width=Decimal("5"),
        win_rate_target=Decimal("0.65"),
        short_greeks=GreekData(
            delta=Decimal("0.30"),
            gamma=Decimal("0.05"),
            theta=Decimal("0.025"),
            vega=Decimal("-0.15"),
            rho=Decimal("0.01"),
        ),
        long_greeks=GreekData(
            delta=Decimal("0.10"),
            gamma=Decimal("0.04"),
            theta=Decimal("0.015"),
            vega=Decimal("-0.08"),
            rho=Decimal("0.005"),
        ),
        iv_rank=Decimal("82"),
    )
    
    assert setup.symbol == "SPY"
    assert float(setup.mid_price) == 1.55  # (1.60 + 1.50) / 2
    assert setup.spread_health in ["GOOD", "FAIR", "POOR"]
    assert setup.risk_reward_ratio > 0


def test_risk_gates_approval():
    """Test that good trades pass risk gates."""
    gates = OptionsRiskGates(
        max_loss_per_trade=Decimal("500"),
        max_daily_loss=Decimal("2000"),
    )
    
    result = gates.validate_trade(
        symbol="SPY",
        setup_type="bull_call_spread",
        short_strike=Decimal("580"),
        long_strike=Decimal("585"),
        short_bid=Decimal("1.50"),
        short_ask=Decimal("1.60"),
        long_bid=Decimal("0.80"),
        long_ask=Decimal("0.90"),
        expiration="2026-09-10",
        portfolio_realized_loss=Decimal("0"),
        current_open_positions=0,
        short_delta=Decimal("0.30"),
        short_theta=Decimal("0.025"),
    )
    
    assert result.passed is True
    assert len(result.critical_failures) == 0
    # Max loss check should pass
    max_loss_gate = [g for g in result.gates if g.gate_name == "max_loss_per_trade"][0]
    assert max_loss_gate.status == GateStatus.PASS


def test_risk_gates_rejection_max_loss():
    """Test that trades exceeding max loss are rejected."""
    gates = OptionsRiskGates(max_loss_per_trade=Decimal("100"))  # Very strict
    
    result = gates.validate_trade(
        symbol="SPY",
        setup_type="bull_call_spread",
        short_strike=Decimal("580"),
        long_strike=Decimal("590"),  # Wide spread = high loss
        short_bid=Decimal("2.00"),
        short_ask=Decimal("2.10"),
        long_bid=Decimal("0.10"),
        long_ask=Decimal("0.20"),
        expiration="2026-09-10",
        portfolio_realized_loss=Decimal("0"),
        current_open_positions=0,
    )
    
    assert result.passed is False
    assert "max_loss_per_trade" in result.critical_failures


def test_risk_gates_rejection_open_positions():
    """Test that position limit is enforced."""
    gates = OptionsRiskGates(max_open_positions=3)
    
    result = gates.validate_trade(
        symbol="SPY",
        setup_type="bull_call_spread",
        short_strike=Decimal("580"),
        long_strike=Decimal("585"),
        short_bid=Decimal("1.50"),
        short_ask=Decimal("1.60"),
        long_bid=Decimal("0.80"),
        long_ask=Decimal("0.90"),
        expiration="2026-09-10",
        portfolio_realized_loss=Decimal("0"),
        current_open_positions=3,  # At limit
    )
    
    assert result.passed is False
    assert "open_position_limit" in result.critical_failures


def test_options_strategy_service():
    """Test the full orchestration service."""
    creds = AlpacaCredentials(environment="paper", api_key_id="test", api_secret="test")
    service = OptionsStrategyService(creds)
    
    # Scan for opportunities (mock data)
    result = service.scan_and_propose(
        symbols=["SPY"],
        min_iv_rank=75,
        portfolio_realized_loss=Decimal("0"),
        current_open_positions=0,
    )
    
    assert "scans" in result
    assert "summary" in result
    assert result["summary"]["total_scanned"] == 1
    
    # Should have at least scanned SPY
    spy_scan = [s for s in result["scans"] if s.get("symbol") == "SPY"]
    assert len(spy_scan) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
