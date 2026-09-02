export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Cache-Control", "no-store, max-age=0");
  if (req.method === "OPTIONS") return res.status(200).end();

  const rules = [
    {
      id: "gate-1",
      rule_type: "defined_risk_requirement",
      name: "Gate 1: Outer Long Wing Protection",
      severity: "HARD",
      threshold: "100%",
      description: "Every short option must be paired with an outer long wing. Naked options are unconditionally rejected.",
      status: "ACTIVE",
    },
    {
      id: "gate-2",
      rule_type: "positive_theta_decay",
      name: "Gate 2: Positive Theta Decay",
      severity: "HARD",
      threshold: "Theta > 0",
      description: "The net position must generate strictly positive time decay in favor of the portfolio.",
      status: "ACTIVE",
    },
    {
      id: "gate-3",
      rule_type: "max_trade_loss",
      name: "Gate 3: Per-Trade Loss Cap",
      severity: "HARD",
      threshold: "$500.00",
      description: "Maximum possible loss cannot exceed $500 per defined-risk spread.",
      status: "ACTIVE",
    },
    {
      id: "gate-4",
      rule_type: "daily_drawdown_limit",
      name: "Gate 4: Daily Circuit Breaker",
      severity: "HARD",
      threshold: "$2,000.00",
      description: "Automated trading halts if cumulative daily loss reaches $2,000.",
      status: "ACTIVE",
    },
    {
      id: "gate-5",
      rule_type: "max_open_positions",
      name: "Gate 5: Maximum 5 Concurrent Spreads",
      severity: "HARD",
      threshold: "5 Spreads",
      description: "Max 5 open spreads (10 option legs) to maintain strict portfolio diversification.",
      status: "ACTIVE",
    },
    {
      id: "gate-6",
      rule_type: "liquidity_spread_filter",
      name: "Gate 6: Bid/Ask Liquidity Tolerance",
      severity: "HARD",
      threshold: "<= 10%",
      description: "Bid/ask spread must be within allowable tight tolerances to prevent slippage.",
      status: "ACTIVE",
    },
  ];

  const templates = [
    {
      rule_type: "profit_target",
      name: "Automated 50% Profit-Take",
      severity: "HARD",
      threshold: "50%",
      description: "Automatically buy-to-close spread when 50% of maximum credit received is captured.",
    },
    {
      rule_type: "stop_loss",
      name: "2.0x Credit Stop Loss",
      severity: "HARD",
      threshold: "200%",
      description: "Automatically buy-to-close spread if unrealized loss reaches 2.0x initial credit.",
    },
  ];

  return res.status(200).json({ rules, templates });
}
