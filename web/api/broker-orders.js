export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  if (req.method === "OPTIONS") return res.status(200).end();

  const apiKey = process.env.ALPACA_API_KEY || "PKIAUNH7EL5KO7VOW6WOD36IUN";
  const apiSecret = process.env.ALPACA_SECRET_KEY || "4Pqw8oHGkckXWNP5JMxVGWbGc3WVZAdiGW9gE8Uvb2eF";

  try {
    const headers = { "APCA-API-KEY-ID": apiKey, "APCA-API-SECRET-KEY": apiSecret };
    const r = await fetch("https://paper-api.alpaca.markets/v2/orders?status=all&limit=25", { headers });
    const orders = r.ok ? await r.json() : [];
    return res.status(200).json({ orders });
  } catch (err) {
    return res.status(200).json({ orders: [] });
  }
}
