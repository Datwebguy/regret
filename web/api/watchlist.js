export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  return res.status(200).json({ symbols: ["SPY", "QQQ", "IWM", "NVDA", "AAPL", "MSFT", "XSP", "SPX"] });
}
