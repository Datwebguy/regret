<div align="center">

# REGRET
### Autonomous AI Options Trading Agent

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-1e293b.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.0-61dafb.svg?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Alpaca API](https://img.shields.io/badge/Alpaca-Paper%20%26%20Live-f59e0b.svg?style=flat-square)](https://alpaca.markets/)
[![Featherless AI](https://img.shields.io/badge/Featherless.ai-Serverless%20LLM-38bdf8.svg?style=flat-square)](https://featherless.ai/)
[![Tests Passing](https://img.shields.io/badge/Tests-98%20Passed%20(100%25)-3fb950.svg?style=flat-square)](tests/)
[![Live App](https://img.shields.io/badge/Live%20Dashboard-regretagent.vercel.app-000000.svg?style=flat-square&logo=vercel)](https://regretagent.vercel.app)
[![API Engine](https://img.shields.io/badge/Live%20API-regret--agent.fly.dev-6851ff.svg?style=flat-square&logo=flydotio)](https://regret-agent.fly.dev)

<br />

**High-probability, defined-risk options credit spread engine pairing open-source LLM market reasoning with 6 deterministic mathematical risk gates.**

<br />

</div>

---

## 🏛️ Executive Summary

Most autonomous LLM trading agents fail in financial markets because large language models are probabilistic text generators. When granted direct broker execution authority, language models frequently hallucinate options Greeks, miscalculate margin collateral, and enter undefined-risk naked short positions that expose portfolios to catastrophic tail risk.

**REGRET** enforces an uncompromised separation of concerns:

1. **Strategic Market Intelligence**: Serverless open reasoning models (e.g. Qwen 2.5 72B / Llama 3.3 via Featherless.ai) evaluate macro regime shifts, earnings calendars, and volatility skew.
2. **Deterministic Risk Execution**: Hardened Python risk engines own 100% of mathematical validation, position sizing, strike selection, and atomic multi-leg order routing.

Zero naked options. Zero tail risk. Every position is mathematically bounded before any order touches the broker.

---

## 🏆 Lablab.ai Alpaca Hackathon Submission Links

* 🌐 **Live Web Application**: [https://regretagent.vercel.app](https://regretagent.vercel.app)
* ⚡ **Live Backend API Engine**: [https://regret-agent.fly.dev](https://regret-agent.fly.dev)
* 📄 **Official One-Page Write-Up**: [ONE_PAGE_WRITEUP.md](ONE_PAGE_WRITEUP.md)
* 📊 **Verified Paper Trading Account ID**: `PA3XUIGQ0VGB` (\$100,000 Baseline)
* 🧪 **Automated Test Suite**: 98 Passing Tests (100% Core Coverage)

---

## ⚡ Core Architecture

The quantitative execution pipeline operates in four closed-loop stages:

```
┌────────────────────────┐
│  Alpaca Market Data    │ ──► Real-time Quotes, Historical Bars & 52-Week IV Rank
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│  Featherless AI Engine │ ──► Qualitative Regime Analysis & Strategic Thesis (Qwen / Llama)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ 6 Hardcoded Risk Gates │ ──► Deterministic Boundary Checks (Loss Caps, Theta, Sizing)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│  Alpaca Trading API    │ ──► Atomic Multi-Leg Order Routing (SPY, QQQ, IWM, NVDA, AAPL, SPX)
└────────────────────────┘
```

### The 4 Pipeline Stages

1. **Market Scanner & IV Rank Calculation**:
   The engine continuously scans high-liquidity underlyings (`SPY`, `QQQ`, `IWM`, `NVDA`, `AAPL`, `MSFT`) and cash-settled index options (`XSP`, `SPX`). It computes rolling 52-week Implied Volatility Rank (IV Rank) to identify volatility expansion setups ripe for mean reversion.

2. **AI Market Regime Reasoning**:
   When IV Rank exceeds threshold ($\ge 40$), Featherless AI generates structured strategic trade theses, analyzing underlying trend direction, support/resistance levels, and upcoming catalyst events.

3. **Deterministic 6-Gate Risk Engine**:
   Every trade proposal must clear six hardened mathematical gates before execution:
   * **Gate 1 (Defined Risk Requirement)**: Every short option MUST be paired with an outer long protective wing (Bull Put Spread or Bear Call Spread). Naked options are unconditionally rejected.
   * **Gate 2 (Positive Theta Decay)**: The net spread must generate strictly positive time decay ($\Theta > 0$) in favor of the portfolio.
   * **Gate 3 (Per-Trade Loss Cap)**: Maximum possible loss cannot exceed \$500 per spread setup.
   * **Gate 4 (Daily Circuit Breaker)**: Cumulative daily portfolio drawdown is capped at \$2,000. Trading halts automatically upon breach.
   * **Gate 5 (Position Concentration Limit)**: Maximum of 5 concurrent open spreads (10 total option legs) to prevent over-leveraging.
   * **Gate 6 (Bid/Ask Liquidity Bound)**: Bid-ask spread must be within allowable tight tolerances to prevent slippage.

4. **Active Lifecycle Position Management**:
   The background agent monitors all active spreads 24/7 with automated exit logic:
   * **Profit Taking**: Automatically closes spreads when reaching **50% of maximum credit received**.
   * **Stop Loss**: Automatically closes spreads if unrealized loss reaches **2.0x initial credit**.
   * **Expiry Protection**: Automatically closes open spreads **24 hours before expiration (1 DTE)** to eliminate pin risk and early assignment paths.

---

## 🚀 Key Features

* **Multi-Leg Credit Spreads**: Native multi-leg order execution for Bull Put Spreads and Bear Call Spreads.
* **Cash-Settled Index Options Ready**: Architected for European-style cash-settled index options (`SPX`, `XSP`, `VIX`) with zero early assignment risk.
* **Dual Execution Modes**:
  * **Autonomous CLI Daemon**: Run headless 24/7 background agent with configurable polling cycles.
  * **Interactive Web Terminal**: Full-featured React 19 UI with real-time portfolio telemetry, trade analysis workspace, and rules engine.
* **Privacy & Social Sharing**:
  * Interactive privacy toggle (`👁️` / `🙈`) to mask sensitive broker account IDs during recordings.
  * 1-click **"Copy Card Image"** export rendering 2x high-resolution performance cards for building in public on X.
* **Zero Fake Data Policy**: 100% of quotes, balances, positions, and Greeks are verified directly against Alpaca's live and paper broker endpoints.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend Engine** | Python 3.11+, FastAPI, SQLAlchemy, Alembic, Pydantic v2 |
| **Broker & Market Data** | Alpaca Trading API & Market Data (`alpaca-py`) |
| **AI Inference** | Featherless.ai Serverless Open Reasoning Models (Qwen 2.5 72B, Llama 3.3) |
| **Frontend UI** | React 19, TypeScript, Vite, React Router v7, HTML5 Canvas |
| **Testing & Quality** | Pytest, Pytest-Asyncio, Ruff, MyPy (98 passing tests) |
| **Deployment** | Docker, Fly.io, Persistent Encrypted Volumes |

---

## 📦 Quickstart & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Datwebguy/regret.git
cd regret
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```ini
# Alpaca Paper Trading Credentials
ALPACA_API_KEY=your_alpaca_key_id
ALPACA_SECRET_KEY=your_alpaca_secret_key
REGRET_DEFAULT_TRADING_ENVIRONMENT=paper

# Featherless AI Inference
FEATHERLESS_API_KEY=your_featherless_api_key
FEATHERLESS_MODEL=Qwen/Qwen2.5-72B-Instruct

# Application Secrets
REGRET_SECRET_KEY=your_random_secret_jwt_key
REGRET_DATABASE_URL=sqlite:///./regret.db
```

### 3. Backend Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate

# Install dependencies
pip install -e .

# Run database migrations
alembic upgrade head
```

### 4. Frontend Setup

```bash
cd web
npm install
npm run build
cd ..
```

### 5. Launch the Platform

```bash
# Start FastAPI backend server
python -m uvicorn regret.api.main:app --host 127.0.0.1 --port 8000

# In a second terminal, start the Vite development server (optional for hot reload)
cd web
npm run dev
```

Visit **`http://127.0.0.1:5173`** in your browser.

---

## 💻 CLI Commands

REGRET includes a command-line interface for headless execution and telemetry:

```bash
# Display live account stats and open option contracts
regret agent stats

# Run a single autonomous scan and execution cycle
regret agent run

# Launch continuous autonomous background trading loop (5-minute cycles)
regret agent start --interval 300

# Screen underlyings for high IV Rank opportunities
regret scan --symbols SPY,QQQ,NVDA,AAPL,XSP

# Submit an on-demand trade idea for 6-gate risk evaluation
regret analyze --symbol SPY --strategy bull_put_spread
```

---

## 🧪 Verification & Test Suite

The entire codebase is verified with an automated test suite covering authentication, Alpaca broker adapter integration, multi-leg spread pricing, risk gate boundary checks, and AI response sanitization:

```bash
pytest
```

```text
======================= 98 passed, 1 skipped in 31.42s =======================
```

---

## 🔒 Security & Privacy

* **Credential Isolation**: Broker API keys and secrets are never logged, never exposed in client bundles, and never returned via public APIs.
* **Deterministic Risk Bounds**: Execution logic is strictly sandboxed. LLM outputs cannot override mathematical risk gates.
* **Account Masking**: Client dashboards feature interactive masking toggles to protect account numbers during presentations and public shares.

---

## 📄 License

This project is licensed under the Apache 2.0 License.
