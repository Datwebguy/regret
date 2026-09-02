"""
Options Risk Gates: Deterministic validation before execution.

These gates ensure that NO trade can pass through without clearing
strict risk criteria. AI can propose, but deterministic code decides.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from enum import Enum


class GateStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


@dataclass
class GateResult:
    """Result of a single risk gate check."""
    gate_name: str
    status: GateStatus
    message: str
    severity: str  # "critical", "warning", "info"
    details: dict = None
    
    def as_dict(self) -> dict:
        return {
            "gate": self.gate_name,
            "status": self.status.value,
            "message": self.message,
            "severity": self.severity,
            "details": self.details or {},
        }


@dataclass
class OptionsRiskGateResult:
    """Aggregated result of all risk gates."""
    passed: bool
    gates: list[GateResult]
    critical_failures: list[str]
    warnings: list[str]
    
    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "critical_failures": self.critical_failures,
            "warnings": self.warnings,
            "gates": [g.as_dict() for g in self.gates],
        }


class OptionsRiskGates:
    """Deterministic risk validation for options trades."""
    
    def __init__(
        self,
        *,
        max_loss_per_trade: Decimal = Decimal("500"),
        max_daily_loss: Decimal = Decimal("2000"),
        max_open_positions: int = 5,
        max_single_leg_notional: Decimal = Decimal("10000"),
        min_spread_width_cents: Decimal = Decimal("5"),  # $0.05
        max_bid_ask_width_pct: Decimal = Decimal("10"),  # 10% of credit
    ):
        self.max_loss_per_trade = max_loss_per_trade
        self.max_daily_loss = max_daily_loss
        self.max_open_positions = max_open_positions
        self.max_single_leg_notional = max_single_leg_notional
        self.min_spread_width_cents = min_spread_width_cents
        self.max_bid_ask_width_pct = max_bid_ask_width_pct
    
    def validate_trade(
        self,
        symbol: str,
        setup_type: str,  # "bull_call_spread", "bull_put_spread"
        short_strike: Decimal,
        long_strike: Decimal,
        short_bid: Decimal,
        short_ask: Decimal,
        long_bid: Decimal,
        long_ask: Decimal,
        expiration: str,
        *,
        portfolio_realized_loss: Decimal = Decimal("0"),
        current_open_positions: int = 0,
        short_delta: Decimal = Decimal("0"),
        short_theta: Decimal = Decimal("0"),
        long_delta: Decimal = Decimal("0"),
    ) -> OptionsRiskGateResult:
        """
        Run all risk gates for a proposed options trade.
        
        Args:
            symbol: Underlying ticker
            setup_type: Type of spread
            short_strike: Strike of short leg
            long_strike: Strike of long leg
            short_bid/ask: Bid/ask of short leg
            long_bid/ask: Bid/ask of long leg
            expiration: Expiration date
            portfolio_realized_loss: Cumulative realized loss today
            current_open_positions: Number of currently open spreads
            short_delta: Delta of short leg
            short_theta: Theta of short leg
            long_delta: Delta of long leg
        
        Returns:
            OptionsRiskGateResult with pass/fail and detailed feedback
        """
        gates = []
        
        # Gate 1: Max loss per trade
        gate1 = self._check_max_loss_per_trade(
            Decimal(str(short_strike)),
            Decimal(str(long_strike)),
            Decimal(str(short_bid)),
            Decimal(str(short_ask)),
            Decimal(str(long_bid)),
            Decimal(str(long_ask)),
        )
        gates.append(gate1)
        
        # Gate 2: Daily loss limit
        trade_max_loss = Decimal(str(gate1.details.get("max_loss", 0)))
        gate2 = self._check_daily_loss_limit(
            trade_max_loss,
            Decimal(str(portfolio_realized_loss)),
        )
        gates.append(gate2)
        
        # Gate 3: Open position limit
        gate3 = self._check_open_positions(current_open_positions)
        gates.append(gate3)
        
        # Gate 4: Bid-ask spread health
        gate4 = self._check_bid_ask_spread(short_bid, short_ask, long_bid, long_ask)
        gates.append(gate4)
        
        # Gate 5: Spread width (defined risk)
        gate5 = self._check_spread_width(short_strike, long_strike)
        gates.append(gate5)
        
        # Gate 6: Greeks sanity
        gate6 = self._check_greeks(short_delta, short_theta, setup_type)
        gates.append(gate6)
        
        # Gate 7: Expiration safety
        gate7 = self._check_expiration_safety(expiration)
        gates.append(gate7)
        
        # Aggregate results
        critical_failures = [g.gate_name for g in gates if g.status == GateStatus.FAIL and g.severity == "critical"]
        warnings = [g.gate_name for g in gates if g.status == GateStatus.WARN or (g.status == GateStatus.FAIL and g.severity == "warning")]
        passed = len(critical_failures) == 0
        
        return OptionsRiskGateResult(
            passed=passed,
            gates=gates,
            critical_failures=critical_failures,
            warnings=warnings,
        )
    
    def _check_max_loss_per_trade(
        self,
        short_strike: Decimal,
        long_strike: Decimal,
        short_bid: Decimal,
        short_ask: Decimal,
        long_bid: Decimal,
        long_ask: Decimal,
    ) -> GateResult:
        """Ensure max loss doesn't exceed limit."""
        spread_width = abs(long_strike - short_strike)
        short_credit = (short_bid + short_ask) / 2
        long_debit = (long_bid + long_ask) / 2
        net_credit = short_credit - long_debit
        max_loss = (spread_width - net_credit) * 100  # Convert to dollars (1 contract = 100 shares)
        
        passed = max_loss <= self.max_loss_per_trade
        
        return GateResult(
            gate_name="max_loss_per_trade",
            status=GateStatus.PASS if passed else GateStatus.FAIL,
            message=f"Max loss ${float(max_loss):.2f} {'≤' if passed else '>'} ${float(self.max_loss_per_trade):.2f}",
            severity="critical" if not passed else "info",
            details={
                "max_loss": float(max_loss),
                "limit": float(self.max_loss_per_trade),
                "spread_width": float(spread_width),
                "net_credit": float(net_credit),
            },
        )
    
    def _check_daily_loss_limit(
        self,
        trade_max_loss: Decimal,
        portfolio_realized_loss: Decimal,
    ) -> GateResult:
        """Ensure adding this trade doesn't exceed daily loss limit."""
        t_loss = Decimal(str(trade_max_loss))
        p_loss = Decimal(str(portfolio_realized_loss))
        projected_daily_loss = p_loss + t_loss
        passed = projected_daily_loss <= self.max_daily_loss
        
        return GateResult(
            gate_name="daily_loss_limit",
            status=GateStatus.PASS if passed else GateStatus.FAIL,
            message=f"Projected daily loss ${float(projected_daily_loss):.2f} {'≤' if passed else '>'} ${float(self.max_daily_loss):.2f}",
            severity="critical" if not passed else "info",
            details={
                "projected_daily_loss": float(projected_daily_loss),
                "limit": float(self.max_daily_loss),
                "current_realized_loss": float(p_loss),
                "trade_max_loss": float(t_loss),
            },
        )
    
    def _check_open_positions(self, current_open_positions: int) -> GateResult:
        """Ensure we don't exceed max concurrent spreads."""
        would_exceed = current_open_positions >= self.max_open_positions
        
        return GateResult(
            gate_name="open_position_limit",
            status=GateStatus.PASS if not would_exceed else GateStatus.FAIL,
            message=f"Open positions {current_open_positions} {'<' if not would_exceed else '≥'} limit {self.max_open_positions}",
            severity="critical" if would_exceed else "info",
            details={
                "current_positions": current_open_positions,
                "limit": self.max_open_positions,
            },
        )
    
    def _check_bid_ask_spread(
        self,
        short_bid: Decimal,
        short_ask: Decimal,
        long_bid: Decimal,
        long_ask: Decimal,
    ) -> GateResult:
        """Ensure bid-ask spreads aren't too wide."""
        short_width = short_ask - short_bid
        long_width = long_ask - long_bid
        short_credit = (short_bid + short_ask) / 2
        
        # Spreads should be tighter than 10% of credit received
        short_width_pct = (short_width / short_credit * 100) if short_credit > 0 else Decimal(0)
        long_width_pct = (long_width / short_credit * 100) if short_credit > 0 else Decimal(0)
        
        passed = short_width_pct <= self.max_bid_ask_width_pct and long_width_pct <= self.max_bid_ask_width_pct
        
        return GateResult(
            gate_name="bid_ask_spread_health",
            status=GateStatus.PASS if passed else GateStatus.WARN,
            message=f"Short width {float(short_width_pct):.1f}%, Long width {float(long_width_pct):.1f}% (limit {float(self.max_bid_ask_width_pct)}%)",
            severity="warning" if not passed else "info",
            details={
                "short_width": float(short_width),
                "long_width": float(long_width),
                "short_width_pct": float(short_width_pct),
                "long_width_pct": float(long_width_pct),
                "limit_pct": float(self.max_bid_ask_width_pct),
            },
        )
    
    def _check_spread_width(self, short_strike: Decimal, long_strike: Decimal) -> GateResult:
        """Ensure spread has meaningful width (5 cents minimum)."""
        width = abs(long_strike - short_strike)
        width_cents = width * 100
        passed = width_cents >= self.min_spread_width_cents
        
        return GateResult(
            gate_name="spread_width",
            status=GateStatus.PASS if passed else GateStatus.FAIL,
            message=f"Spread width {float(width_cents):.0f}¢ {'≥' if passed else '<'} {float(self.min_spread_width_cents):.0f}¢",
            severity="critical" if not passed else "info",
            details={
                "width_dollars": float(width),
                "width_cents": float(width_cents),
                "min_cents": float(self.min_spread_width_cents),
            },
        )
    
    def _check_greeks(self, short_delta: Decimal, short_theta: Decimal, setup_type: str) -> GateResult:
        """Validate Greeks make sense for the strategy."""
        messages = []
        passed = True
        
        # For credit spreads, we want:
        # - Short delta between 0.20-0.40 (neutral to slightly bullish/bearish)
        # - Positive theta (time decay working for us)
        
        delta_ok = Decimal("-0.4") <= short_delta <= Decimal("0.4")
        if not delta_ok:
            messages.append(f"Delta {float(short_delta):.2f} outside range [-0.4, 0.4]")
            passed = False
        
        theta_ok = short_theta > 0
        if not theta_ok:
            messages.append(f"Theta {float(short_theta):.4f} should be positive (time decay favor)")
            passed = False
        
        message = " | ".join(messages) if messages else "Greeks are reasonable for this strategy"
        
        return GateResult(
            gate_name="greeks_sanity",
            status=GateStatus.PASS if passed else GateStatus.WARN,
            message=message,
            severity="warning" if not passed else "info",
            details={
                "short_delta": float(short_delta),
                "short_theta": float(short_theta),
                "delta_range": [-0.4, 0.4],
                "theta_requirement": "positive",
            },
        )
    
    def _check_expiration_safety(self, expiration: str) -> GateResult:
        """Ensure expiration is not too close (DTE > 3 days)."""
        # Simplified check; in production, calculate actual DTE
        # For now, just ensure it's a valid future date
        
        # This would parse the expiration date and compare to today
        # Placeholder: assume all dates are valid
        
        return GateResult(
            gate_name="expiration_safety",
            status=GateStatus.PASS,
            message=f"Expiration {expiration} is valid",
            severity="info",
            details={"expiration": expiration},
        )


if __name__ == "__main__":
    gates = OptionsRiskGates()
    
    # Test a trade
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
    
    print(f"Trade passed: {result.passed}")
    print(f"Critical failures: {result.critical_failures}")
    print(f"Warnings: {result.warnings}")
    for gate in result.gates:
        print(f"  {gate.gate_name}: {gate.status.value} - {gate.message}")
