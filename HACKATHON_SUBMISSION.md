# 🏆 REGRET — Autonomous AI Options Trading Agent
**Event:** Alpaca AI Trading Agents Hackathon (Lablab.ai)  
**Submission Category:** Autonomous Trading Agents & Trading Applications  
**Paper Trading Account Baseline:** \$100,000.00 Starting Balance  
**Repository / Live App:** [https://regret.fly.dev](https://regret.fly.dev)  

---

## 1. Project Overview & Philosophy

Most AI trading bots hallucinate entries, take unbounded tail risk, or act as unpredictable "black boxes." 

**REGRET** is an **Autonomous AI Options Trading Agent** built around a fundamental insight:  
> *AI excels at market context, macroeconomic synthesis, and opportunistic pattern recognition — but deterministic code must own risk, position sizing, and execution bounds.*

REGRET autonomously scans high-liquidity underlyings (SPY, QQQ, IWM, NVDA, AAPL, MSFT), detects elevated Implied Volatility regimes (**IV Rank > 50%**), generates defined-risk options credit spread setups using LLM reasoning, validates every trade against **Strict Deterministic Risk Gates**, and executes orders on Alpaca's Paper Trading API.

```
┌─────────────────┐     ┌──────────────────────┐     ┌────────────────────────┐
│  Alpaca Market  │ ──► │  Featherless AI      │ ──► │   Deterministic Hard   │
│  Data & Options │     │  Open-Source LLM     │     │   Risk Gates (Python)  │
│  (IV Rank / OCC)│     │  (Llama 3.3 / Qwen)  │     │   (Zero Tail Risk)     │
└─────────────────┘     └──────────────────────┘     └────────────────────────┘
                                                                  │
                                                        [PASS]    ▼    [FAIL]
                                                 ┌────────────────────────┐
                                                 │ Alpaca Paper Broker    │
                                                 │ Multi-Leg Execution    │
                                                 │ (Leaderboard Tracking) │
                                                 └────────────────────────┘
```

---

## 2. AI Intelligence Layer: Featherless.ai Integration

REGRET leverages **Featherless.ai** serverless inference to power its open-source LLM intelligence layer:
- **Provider:** Featherless.ai (`https://api.featherless.ai/v1`)
- **Models:** `meta-llama/Llama-3.3-70B-Instruct`, `deepseek-ai/DeepSeek-R1-Distill-Llama-70B`, `Qwen/Qwen2.5-72B-Instruct`
- **Role:** Analyzes macroeconomic context, implied vs historical volatility divergence, support/resistance levels, and generates structured probabilistic trade setups.
- **Guardrail:** The LLM produces qualitative reasoning and strategy conviction, but deterministic Python code calculates position sizing, Greeks, and hard exit stops.

---

## 3. How to Compete on the Lablab.ai Live Leaderboard

The Lablab.ai Alpaca Hackathon ranks projects based on paper trading P&L and risk management on a dedicated \$100,000 paper account:

1. **Initialize \$100k Account:** Create a brand-new Alpaca paper account initialized with **\$100,000.00**.
2. **Retrieve Paper Account ID:** Copy your Paper Account ID (e.g., `PA3ABC123456`) and API keys.
3. **Configure Environment:** Set `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`, and `FEATHERLESS_API_KEY` in `.env`.
4. **Run Autonomous Agent:** Execute `regret agent run` (or 24/7 autonomous loop) during market hours. The agent scans, reasons via Featherless, clears risk gates, and submits multi-leg option orders.
5. **Submit to Lablab.ai:** Submit your **Paper Trading Account ID**, **GitHub Repository**, **1-page writeup**, and **Demo Video**. Lablab.ai and Alpaca track your Account ID for live leaderboard P&L verification.

All trading strategies are built exclusively on **defined-risk options spreads**:
- **Strategy Type:** Bull Put Spreads (Credit Put Spreads) and Bear Call Spreads (Credit Call Spreads).
- **Core Edge:** Selling options premium when implied volatility is significantly elevated relative to historical realized volatility (**IV Rank > 50–75%**), capturing volatility crush and positive Theta decay.
- **Strike Selection:**
  - Short leg: 0.20 – 0.30 Delta (~70–80% probability of expiring out of the money).
  - Long leg: \$5.00 width out-of-the-money hedge to strictly define max loss.
  - Expiration Target: 7 to 45 DTE (optimal theta acceleration window).

---

## 3. Hard Deterministic Risk Gates

Before any order touches the broker, it must pass 100% of the following code-enforced gates in `regret.engine.options_risk_gates`:

1. **Max Loss Per Trade Gate:** Hard cap at \$500 max loss per trade. Unbounded risk (naked calls/puts) is mathematically impossible.
2. **Daily Loss Halt Gate:** Cumulative daily losses cannot exceed \$2,000. If hit, the agent automatically halts all new entries.
3. **Max Concurrent Position Gate:** Maximum of 5 open option spreads concurrently to prevent portfolio concentration.
4. **Bid-Ask Spread Health Gate:** Rejects illiquid options where the bid-ask spread exceeds 10% of the credit received.
5. **Greeks Sanity Gate:** Verifies positive Theta ($\Theta > 0$) and bounded Delta ($-0.40 \le \Delta \le 0.40$).
6. **Expiration Safety Gate:** Restricts entries to safe DTE bounds (7–45 DTE) to avoid gamma explosions and pin risk.

---

## 4. Automated Position & Exit Management

Open positions are continuously monitored in real-time by the autonomous agent:
- 🎯 **Profit Target (Take Profit):** Automatically closes the spread when **50% of max profit** is achieved.
- 🛑 **Stop Loss:** Automatically closes the spread if loss reaches **2.0x initial credit received**.
- ⏱️ **Pin Risk / DTE Exit:** Closes open spreads at **1 DTE** to eliminate expiration weekend assignment risk.

---

## 5. Alpaca Tooling & Infrastructure Integration

REGRET deeply integrates the entire Alpaca developer ecosystem:
- **Alpaca Trading API:** Multi-leg options routing, order lifecycle management (`/v2/orders`, `position_intent`), and account synchronization.
- **Alpaca Market Data API:** Real-time stock quotes, historical daily OHLC bars, and options chain snapshots (`/v1beta1/options/snapshots`).
- **Alpaca CLI & MCP Integration:** Complete tool support enabling AI agents (via Cursor, Claude, or custom sidecars) to run `regret agent run`, `regret options scan`, and view competition stats.

---

## 6. CLI Quick Start & Autonomous Execution

```powershell
# 1. Setup local environment
git clone https://github.com/your-username/REGRET.git
cd REGRET
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .

# 2. Configure Alpaca Paper Credentials
$env:APCA_API_KEY_ID = "YOUR_ALPACA_PAPER_KEY"
$env:APCA_API_SECRET_KEY = "YOUR_ALPACA_PAPER_SECRET"
$env:ALPACA_ENVIRONMENT = "paper"

# 3. Run Autonomous Agent Cycle
regret agent run

# 4. View Hackathon Competition Stats ($100k baseline)
regret agent stats

# 5. Start Continuous 24/7 Agent Loop
python -m regret.agents.autonomous_agent
```

---

## 7. Submission Checklist Summary

- ✅ **$100,000 Paper Account:** Dedicated fresh Alpaca paper account initialized and verified.
- ✅ **Mandatory Options Trading:** Live IV Rank screening and defined-risk Credit Spread execution.
- ✅ **Autonomous AI Agent:** Autonomous loop with LLM reasoning, opportunity ranking, and automatic order routing.
- ✅ **Deterministic Risk Gates:** 6 hard risk gates preventing any unbounded losses or overleveraging.
- ✅ **Tooling & MCP/CLI:** Full CLI commands and Model Context Protocol (MCP) server endpoints.
- ✅ **1-Page Documentation & Web UI:** Production-ready dashboard with live P&L tracking, Greeks, and decision logs.
