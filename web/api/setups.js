export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  const setups = [
    {
      symbol: "SPY",
      strategy: "Bull Put Spread",
      short_strike: 766,
      long_strike: 765,
      net_credit: 0.33,
      iv_rank: 54.2,
      featherless_thesis: "Strong institutional support near 20-day SMA. Volatility skew favors put selling with outer wing hedge.",
      risk_verdict: "APPROVED",
    },
    {
      symbol: "QQQ",
      strategy: "Bear Call Spread",
      short_strike: 710,
      long_strike: 712,
      net_credit: 0.36,
      iv_rank: 48.7,
      featherless_thesis: "Tech sector overbought on RSI momentum divergence. Defined-risk call spread bounds upward tail risk.",
      risk_verdict: "APPROVED",
    },
  ];
  return res.status(200).json({ setups, total: setups.length });
}
