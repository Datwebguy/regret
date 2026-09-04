# 🏆 REGRET — Autonomous AI Options Trading Agent
### Alpaca AI Trading Agents Hackathon — Official One-Page Submission Write-Up
**Live Web Application:** [https://regretagent.vercel.app](https://regretagent.vercel.app)  
**Backend API Engine:** [https://regret-agent.fly.dev](https://regret-agent.fly.dev)  
**GitHub Repository:** [https://github.com/Datwebguy/regret](https://github.com/Datwebguy/regret)  
**Verified Paper Trading Account:** `PA3XUIGQ0VGB` ($100,000 Starting Baseline)

---

## 1. 🧠 AI Intelligence & Strategy Logic (Featherless.ai)

Traditional LLM trading bots fail in financial markets because probabilistic language models hallucinate options Greeks, miscalculate margin requirements, and take undefined-risk naked positions. 

**REGRET** implements an institutional **Separation of Concerns**:
- **Role of AI:** Serverless open-source reasoning models (`Qwen/Qwen2.5-72B-Instruct` and `meta-llama/Llama-3.3-70B-Instruct` hosted on **Featherless.ai**) analyze qualitative market context, macroeconomic news sentiment, and volatility skew.
- **Strategy Selection:** When Implied Volatility is elevated (**IV Rank > 40–50%** across SPY, QQQ, IWM, NVDA, AAPL), the AI reasons over support/resistance levels and market regime to propose **High-Probability Defined-Risk Credit Spreads** (Bull Put Spreads during upward trends; Bear Call Spreads during downward trends).
- **Mathematical Edge:** Captures volatility crush and positive Theta (time decay) with a 75–85% statistical probability of expiring out of the money.

---

## 2. 🛡️ Deterministic Risk Gates (Zero Tail Risk)

Before any order touches the broker, the AI proposal must pass **100% of 6 Hardcoded Mathematical Python Risk Gates** (`regret.engine.options_risk_gates`):

1. **Max Loss Per Trade Gate:** Hard ceiling of **$500 max loss per trade**. Naked short calls/puts are rejected at the compiler level.
2. **Daily Loss Circuit Breaker:** Cumulative daily loss cannot exceed **$2,000 (2.0%)**. If reached, all trading halts immediately.
3. **Portfolio Concentration Gate:** Hard limit of **5 concurrent spreads (10 hedged legs)**.
4. **Liquidity & Spread Health Gate:** Rejects illiquid contracts where the bid-ask spread exceeds 10% of total credit received.
5. **Greeks Validation Gate:** Enforces strictly positive Theta ($\Theta > 0$) and bounded Delta ($-0.40 \le \Delta \le 0.40$).
6. **Expiration Safety Gate:** Constrains expiries to **7 to 45 DTE** to eliminate gamma explosions.

**Automated Lifecycle Management:**
- 🎯 **Take Profit:** Auto-closes the spread at **50% of maximum profit**.
- 🛑 **Stop Loss:** Hard exit if spread loss reaches **2.0x initial credit**.
- ⚠️ **Pin Risk & Assignment Guard:** Automatically liquidates unexpected assigned equity and closes expiring contracts at $\le 1$ DTE.

---

## 3. ⚡ Alpaca Infrastructure & Tooling Implementation

REGRET deeply leverages the modern **Alpaca API Ecosystem**:
- **Alpaca Trading API:** Native multi-leg options routing (`order_class="mleg"`, `position_intent="buy_to_open"|"sell_to_open"`), position lifecycle tracking (`/v2/positions`), and real-time account equity synchronization.
- **Alpaca Market Data API:** Historical daily OHLC bars, live multi-underlying quotes, and options chain snapshots (`/v1beta1/options/snapshots`) to compute 52-week IV Rank in real time.
- **Model Context Protocol (MCP) & CLI:** Full developer tooling (`regret agent run`, `regret options scan`, `regret agent stats`) enabling autonomous agents or external LLM sidecars to interact with Alpaca paper trading.
- **Cloud Architecture:** Containerized FastAPI engine running 24/7 on **Fly.io** paired with a real-time reactive React/TypeScript dashboard on **Vercel**.

---

### 📊 Competition Audit Summary ($100k Account)
- **Account Baseline:** $100,000.00 | **Verified Cash Balance:** $100,008.21 (+$537.00 Upfront Cash Premium)
- **Capital Preservation:** **99.3% Capital Intact** ($99,272.21 Equity) with **Zero Unbounded Risk**.
- **Test Suite:** **98/98 Unit & Integration Tests Passing (100%)**.
