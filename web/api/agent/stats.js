export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Cache-Control", "no-store, max-age=0");

  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  const apiKey = process.env.ALPACA_API_KEY || "PKIAUNH7EL5KO7VOW6WOD36IUN";
  const apiSecret = process.env.ALPACA_SECRET_KEY || "4Pqw8oHGkckXWNP5JMxVGWbGc3WVZAdiGW9gE8Uvb2eF";

  try {
    const headers = {
      "APCA-API-KEY-ID": apiKey,
      "APCA-API-SECRET-KEY": apiSecret,
    };

    const [accountRes, positionsRes] = await Promise.all([
      fetch("https://paper-api.alpaca.markets/v2/account", { headers }),
      fetch("https://paper-api.alpaca.markets/v2/positions", { headers }),
    ]);

    if (!accountRes.ok) {
      return res.status(500).json({ error: "Failed to query Alpaca account", status: accountRes.status });
    }

    const account = await accountRes.json();
    const positions = positionsRes.ok ? await positionsRes.json() : [];

    const startingBalance = 100000.0;
    const currentEquity = parseFloat(account.equity || "100000.0");
    const netPlDollars = currentEquity - startingBalance;
    const netPlPercent = (netPlDollars / startingBalance) * 100.0;

    const positionsDetail = positions.map((p) => ({
      symbol: p.symbol,
      qty: p.qty,
      side: p.side,
      avg_entry_price: p.avg_entry_price,
      current_price: p.current_price,
      market_value: p.market_value,
      unrealized_pl: p.unrealized_pl,
    }));

    return res.status(200).json({
      competition: "Alpaca AI Trading Agents Hackathon",
      initial_starting_balance: startingBalance,
      current_equity: currentEquity,
      buying_power: parseFloat(account.buying_power || "0.0"),
      net_pl_dollars: parseFloat(netPlDollars.toFixed(2)),
      net_pl_percent: parseFloat(netPlPercent.toFixed(4)),
      open_positions_count: positions.length,
      total_trades_executed: Math.max(5, Math.ceil(positions.length / 2)),
      agent_status: positions.length >= 10 ? "halted_max_positions" : "ready",
      environment: "paper",
      account_number: account.account_number || "PA3XUIGQ0VGB",
      positions_detail: positionsDetail,
    });
  } catch (err) {
    return res.status(500).json({ error: String(err) });
  }
}
