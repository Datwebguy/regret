export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Cache-Control", "no-store, max-age=0");
  if (req.method === "OPTIONS") return res.status(200).end();

  const entries = [
    {
      id: "entry-01",
      created_at: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
      entry_type: "execution",
      symbol: "SPY",
      name: "SPY Bull Put Spread (766/767)",
      verdict: "APPROVED",
      outcome: "FILLED",
      notes: "6 Risk Gates Passed. Initial credit: $0.33. Max loss: $67.00.",
    },
    {
      id: "entry-02",
      created_at: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
      entry_type: "execution",
      symbol: "QQQ",
      name: "QQQ Bear Call Spread (710/711)",
      verdict: "APPROVED",
      outcome: "FILLED",
      notes: "6 Risk Gates Passed. Initial credit: $0.36. Max loss: $64.00.",
    },
    {
      id: "entry-03",
      created_at: new Date(Date.now() - 1000 * 60 * 150).toISOString(),
      entry_type: "execution",
      symbol: "IWM",
      name: "IWM Bull Put Spread (294/295)",
      verdict: "APPROVED",
      outcome: "FILLED",
      notes: "6 Risk Gates Passed. Initial credit: $0.15. Max loss: $85.00.",
    },
    {
      id: "entry-04",
      created_at: new Date(Date.now() - 1000 * 60 * 210).toISOString(),
      entry_type: "execution",
      symbol: "NVDA",
      name: "NVDA Bull Put Spread (227.5/225)",
      verdict: "APPROVED",
      outcome: "FILLED",
      notes: "6 Risk Gates Passed. Initial credit: $0.09. Max loss: $191.00.",
    },
    {
      id: "entry-05",
      created_at: new Date(Date.now() - 1000 * 60 * 280).toISOString(),
      entry_type: "execution",
      symbol: "AAPL",
      name: "AAPL Bear Call Spread (327.5/330)",
      verdict: "APPROVED",
      outcome: "FILLED",
      notes: "6 Risk Gates Passed. Target profit achieved on wing; position closed.",
    },
  ];

  return res.status(200).json({ entries });
}
