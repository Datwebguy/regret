export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  return res.status(200).json({
    user: {
      id: "usr_alpaca_live",
      email: "trader@regret.trade",
      display_name: "Alpaca Paper Trader (PA3XUIGQ0VGB)",
    },
  });
}
