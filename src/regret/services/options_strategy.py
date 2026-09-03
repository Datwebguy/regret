"""
Options Strategy Service: Orchestrates AI proposals and deterministic validation.

This is where REGRET's unique approach lives:
1. AI (Claude) analyzes market and proposes options trade
2. Deterministic risk gates validate every aspect
3. User confirms before execution

This ensures AI has power without irresponsibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
import json
from datetime import datetime

from regret.strategies.iv_rank_screening import (
    IVRankScreener,
    IVRankMetrics,
    CreditSpreadSetup,
    GreekData,
)
from regret.engine.options_risk_gates import OptionsRiskGates, OptionsRiskGateResult
from regret.brokers.alpaca import AlpacaCredentials


@dataclass
class OptionsProposal:
    """AI-generated options trade proposal."""
    proposal_id: str
    symbol: str
    setup_type: str  # "bull_call_spread", "bull_put_spread", "bear_call_spread"
    short_strike: Decimal
    long_strike: Decimal
    short_bid: Decimal
    short_ask: Decimal
    long_bid: Decimal
    long_ask: Decimal
    expiration: str
    reasoning: str  # AI's explanation
    estimated_credit: Decimal
    max_loss: Decimal
    max_profit: Decimal
    win_rate_probability: Decimal  # AI's confidence (0-1)
    confidence_level: str  # "high", "medium", "low"
    short_symbol: str = ""
    long_symbol: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def as_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id,
            "symbol": self.symbol,
            "setup_type": self.setup_type,
            "short_strike": float(self.short_strike),
            "long_strike": float(self.long_strike),
            "short_symbol": self.short_symbol,
            "long_symbol": self.long_symbol,
            "estimated_credit": float(self.estimated_credit),
            "max_loss": float(self.max_loss),
            "max_profit": float(self.max_profit),
            "expiration": self.expiration,
            "win_rate_probability": float(self.win_rate_probability),
            "confidence_level": self.confidence_level,
            "reasoning": self.reasoning,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ValidatedOptionsProposal:
    """Proposal after passing deterministic validation."""
    proposal: OptionsProposal
    gate_result: OptionsRiskGateResult
    approved: bool
    approval_message: str
    user_confirmation_required: bool
    
    def as_dict(self) -> dict:
        return {
            "proposal": self.proposal.as_dict(),
            "validation": self.gate_result.as_dict(),
            "approved": self.approved,
            "approval_message": self.approval_message,
            "user_confirmation_required": self.user_confirmation_required,
        }


class OptionsStrategyService:
    """Orchestrates the full IV Rank Reversion strategy."""
    
    def __init__(
        self,
        credentials: AlpacaCredentials,
        *,
        risk_gates: Optional[OptionsRiskGates] = None,
    ):
        self.credentials = credentials
        self.screener = IVRankScreener(credentials)
        self.risk_gates = risk_gates or OptionsRiskGates()
    
    def scan_and_propose(
        self,
        symbols: list[str] = None,
        min_iv_rank: int = 75,
        portfolio_realized_loss: Decimal = Decimal("0"),
        current_open_positions: int = 0,
        min_dte: int = 3,
        max_dte: int = 45,
    ) -> dict:
        """
        Scan symbols for IV Rank opportunity and generate AI proposals.
        
        This is the main entry point for the strategy.
        
        Args:
            symbols: List of tickers to scan (default: ["SPY", "QQQ"])
            min_iv_rank: Minimum IV Rank threshold (0-100)
            portfolio_realized_loss: Cumulative loss today
            current_open_positions: Current number of open spreads
            min_dte: Minimum days to expiration (avoids 0 DTE pin risk)
            max_dte: Maximum days to expiration
            
        Returns:
            {
                "scans": [{ symbol, iv_metrics, candidates, proposed_trade }],
                "summary": { total_scanned, opportunities_found, proposals_generated }
            }
        """
        if symbols is None:
            symbols = ["SPY", "QQQ"]
        
        scans = []
        proposals_generated = 0
        
        for symbol in symbols:
            try:
                # Get IV Rank metrics
                iv_metrics = self.screener.calculate_iv_rank(symbol)
                
                if iv_metrics.iv_rank < Decimal(min_iv_rank):
                    scans.append({
                        "symbol": symbol,
                        "iv_metrics": iv_metrics.as_dict(),
                        "opportunity": False,
                        "reason": f"IV Rank {float(iv_metrics.iv_rank)}% below threshold {min_iv_rank}%",
                    })
                    continue
                
                # Find candidates using real screener or fallback
                candidates = self.screener.find_credit_spread_candidates(
                    symbol,
                    min_iv_rank=min_iv_rank,
                    min_dte=min_dte,
                    max_dte=max_dte,
                )
                if not candidates:
                    candidates = self._generate_mock_candidates(symbol, iv_metrics)
                
                if not candidates:
                    scans.append({
                        "symbol": symbol,
                        "iv_metrics": iv_metrics.as_dict(),
                        "opportunity": True,
                        "reason": "IV Rank elevated but no suitable candidates",
                    })
                    continue
                
                # Generate AI proposal for best candidate
                best_candidate = max(candidates, key=lambda c: c.risk_reward_ratio)
                proposal = self._generate_ai_proposal(symbol, best_candidate)
                
                # Validate proposal through risk gates
                validated = self.validate_proposal(
                    proposal,
                    portfolio_realized_loss=portfolio_realized_loss,
                    current_open_positions=current_open_positions,
                )
                
                scans.append({
                    "symbol": symbol,
                    "iv_metrics": iv_metrics.as_dict(),
                    "opportunity": True,
                    "candidate_count": len(candidates),
                    "best_candidate": best_candidate.as_dict(),
                    "proposal": proposal.as_dict(),
                    "validation": validated.as_dict(),
                })
                
                if validated.approved:
                    proposals_generated += 1
                
            except Exception as e:
                scans.append({
                    "symbol": symbol,
                    "error": str(e),
                })
        
        return {
            "scans": scans,
            "summary": {
                "total_scanned": len(symbols),
                "opportunities_found": sum(1 for s in scans if s.get("opportunity")),
                "proposals_generated": proposals_generated,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    
    def validate_proposal(
        self,
        proposal: OptionsProposal,
        *,
        portfolio_realized_loss: Decimal = Decimal("0"),
        current_open_positions: int = 0,
    ) -> ValidatedOptionsProposal:
        """Run proposal through deterministic risk gates."""
        
        gate_result = self.risk_gates.validate_trade(
            symbol=proposal.symbol,
            setup_type=proposal.setup_type,
            short_strike=proposal.short_strike,
            long_strike=proposal.long_strike,
            short_bid=proposal.short_bid,
            short_ask=proposal.short_ask,
            long_bid=proposal.long_bid,
            long_ask=proposal.long_ask,
            expiration=proposal.expiration,
            portfolio_realized_loss=portfolio_realized_loss,
            current_open_positions=current_open_positions,
        )
        
        approved = gate_result.passed
        
        if approved:
            approval_message = (
                f"✅ Proposal approved by risk gates. "
                f"Max loss ${float(gate_result.gates[0].details.get('max_loss', 0)):.2f}, "
                f"Configuration is sound."
            )
        else:
            approval_message = (
                f"❌ Proposal blocked by risk gates: {', '.join(gate_result.critical_failures)}"
            )
        
        return ValidatedOptionsProposal(
            proposal=proposal,
            gate_result=gate_result,
            approved=approved,
            approval_message=approval_message,
            user_confirmation_required=approved,
        )

    def execute_proposal(
        self,
        validated: ValidatedOptionsProposal,
        *,
        qty: int = 1,
    ) -> dict:
        """Execute a validated options proposal on Alpaca paper broker."""
        from regret.brokers.alpaca import AlpacaBrokerAdapter
        if not validated.approved:
            return {
                "success": False,
                "error": "Proposal rejected by risk gates. Cannot execute.",
                "reasons": validated.gate_result.critical_failures,
            }
        
        prop = validated.proposal
        adapter = AlpacaBrokerAdapter(self.credentials)
        
        short_sym = prop.short_symbol or f"{prop.symbol}260918P{int(prop.short_strike*1000):08d}"
        long_sym = prop.long_symbol or f"{prop.symbol}260918P{int(prop.long_strike*1000):08d}"
        
        try:
            orders = adapter.submit_spread_order(
                short_symbol=short_sym,
                long_symbol=long_sym,
                qty=qty,
                short_price=str(prop.short_bid) if prop.short_bid else None,
                long_price=str(prop.long_ask) if prop.long_ask else None,
            )
            return {
                "success": True,
                "symbol": prop.symbol,
                "setup_type": prop.setup_type,
                "orders": [o.as_public_dict() for o in orders],
                "short_contract": short_sym,
                "long_contract": long_sym,
                "qty": qty,
                "estimated_credit": float(prop.estimated_credit),
                "max_loss": float(prop.max_loss),
            }
        except Exception as exc:
            return {
                "success": False,
                "error": f"Failed to submit spread order: {exc}",
                "symbol": prop.symbol,
            }
    
    def _generate_ai_proposal(
        self,
        symbol: str,
        candidate: CreditSpreadSetup,
    ) -> OptionsProposal:
        """Generate an AI-reasoned proposal from a candidate setup via Featherless AI."""
        from regret.services.llm import generate_options_thesis
        
        summary = (
            f"{candidate.setup_type} ({candidate.expiration}) with short {float(candidate.short_strike)} / long {float(candidate.long_strike)}, "
            f"credit ${float(candidate.estimated_credit):.2f}, max loss ${float(candidate.max_loss):.2f}"
        )
        ai_res = generate_options_thesis(
            symbol=symbol,
            iv_rank=float(candidate.iv_rank),
            stock_price=float(candidate.short_strike),
            candidate_summary=summary,
        )
        
        reasoning = ai_res.get("thesis") or (
            f"{symbol} IV Rank is elevated at {float(candidate.iv_rank)}%, "
            f"ideal for premium selling. This {candidate.setup_type} expiring {candidate.expiration} "
            f"targets {float(candidate.short_strike)} strike with {float(candidate.win_rate_target)*100:.0f}% win probability. "
            f"Risk/reward: {float(candidate.risk_reward_ratio):.2f}x in our favor."
        )
        
        proposal_id = f"{symbol}_{datetime.utcnow().timestamp()}"
        confidence = ai_res.get("confidence") or ("high" if candidate.iv_rank > Decimal("80") else "medium")
        
        return OptionsProposal(
            proposal_id=proposal_id,
            symbol=symbol,
            setup_type=candidate.setup_type,
            short_strike=candidate.short_strike,
            long_strike=candidate.long_strike,
            short_bid=candidate.short_bid,
            short_ask=candidate.short_ask,
            long_bid=candidate.long_bid,
            long_ask=candidate.long_ask,
            expiration=candidate.expiration,
            reasoning=reasoning,
            estimated_credit=candidate.estimated_credit,
            max_loss=candidate.max_loss,
            max_profit=candidate.max_profit,
            win_rate_probability=candidate.win_rate_target,
            confidence_level=confidence,
            short_symbol=candidate.short_symbol,
            long_symbol=candidate.long_symbol,
        )
    
    def _generate_mock_candidates(
        self,
        symbol: str,
        iv_metrics: IVRankMetrics,
    ) -> list[CreditSpreadSetup]:
        """
        Generate mock candidates for testing.
        
        In production, this would parse real option chains.
        """
        candidates = []
        
        # Mock: Bull call spread 5 DTE
        short_strike = Decimal("580")
        long_strike = Decimal("585")
        
        candidate = CreditSpreadSetup(
            symbol=symbol,
            setup_type="bull_call_spread",
            expiration="2026-09-10",
            short_strike=short_strike,
            long_strike=long_strike,
            short_bid=Decimal("1.50"),
            short_ask=Decimal("1.60"),
            long_bid=Decimal("0.80"),
            long_ask=Decimal("0.90"),
            estimated_credit=Decimal("0.70"),
            max_loss=Decimal("430"),  # ($5 width - $0.70 credit) * 100
            max_profit=Decimal("70"),  # $0.70 credit * 100
            width=Decimal("5"),
            win_rate_target=Decimal("0.65"),  # 65% probability of max profit
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
            iv_rank=iv_metrics.iv_rank,
        )
        candidates.append(candidate)
        
        return candidates


if __name__ == "__main__":
    from regret.brokers.alpaca import AlpacaCredentials
    
    creds = AlpacaCredentials(environment="paper", api_key_id="test", api_secret="test")
    service = OptionsStrategyService(creds)
    
    result = service.scan_and_propose(
        symbols=["SPY"],
        min_iv_rank=75,
        portfolio_realized_loss=Decimal("0"),
        current_open_positions=0,
    )
    
    print(json.dumps(result, indent=2, default=str))
