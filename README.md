# REGRET

Don't just ask AI what to trade. Ask if you should.

REGRET is a trading decision product. It evaluates a proposed trade against live market data, the user's Trading Constitution, the user's actual portfolio, and deterministic risk math before any order can be sent.

It does not invent prices, balances, orders, or fills. If a data source is unavailable, REGRET says so.

## What it does

1. A user creates a REGRET account.
2. The user connects their own Alpaca account (OAuth, or per-user encrypted API keys if OAuth is not configured).
3. The user stores rules.
4. The user submits a trade idea.
5. REGRET pulls live Alpaca account and market data, calculates risk, evaluates rules, and returns BUY / WAIT / REDUCE / REJECT.
6. Execution requires an explicit preview and approval. The model cannot send an order by itself.
7. Paper and live environments are separated. Live execution is disabled until `REGRET_LIVE_TRADING_ENABLED=true`.

Web, CLI, and MCP all call the same API and the same decision engine.

## Requirements

- Python 3.11+
- Node.js 20+ (for the web client)
- An Alpaca account for market data and paper trading
- PostgreSQL in production (SQLite is accepted for local development only)

## Local setup

```powershell
cd C:\Users\DELL\Downloads\REGRET
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
```

Generate local secrets and put them in `.env`:

```powershell
python -c "from regret.security import generate_dev_secrets_if_needed; print(generate_dev_secrets_if_needed())"
```

Start the API:

```powershell
python -m regret.api
```

In another terminal, start the web client:

```powershell
cd web
npm install
npm run dev
```

Open http://127.0.0.1:5173

## Connecting Alpaca

Preferred: register a third-party OAuth application with Alpaca and set:

- `ALPACA_OAUTH_CLIENT_ID`
- `ALPACA_OAUTH_CLIENT_SECRET`
- `ALPACA_OAUTH_REDIRECT_URI`

Until those are set, the Settings page will say OAuth is not configured. A user may instead connect **their own** paper API keys. Keys are encrypted at rest and never returned to the browser.

Do not put a shared personal Alpaca key in the application. Each user must connect their own account.

## CLI

The API must be running.

```powershell
regret setup --api-url http://127.0.0.1:8000 --email you@domain --password ********** --register
regret status
regret portfolio
regret analyze NVDA --side buy --amount 1000 --stop 90 --target 130
regret rules list
regret journal
regret order preview ANALYSIS_ID
regret order confirm APPROVAL_ID --yes
regret order status ORDER_ID
regret monitor NVDA
```

## MCP

Point an MCP client at:

```text
python -m regret.mcp_server
```

The process uses `~/.regret/config.json` (API URL + session token from `regret setup`). `regret_execute_trade` requires an `approval_id` from `regret_create_trade_plan` and `confirm=true`.

## Tests

```powershell
pytest
```

Tests use isolated SQLite databases and fixtures. Those fixtures are not imported into the running application.

## Production notes

- Use PostgreSQL (`REGRET_DATABASE_URL=postgresql+psycopg://...`).
- Set `REGRET_ENV=production`.
- Set strong `REGRET_SECRET_KEY` and `REGRET_ENCRYPTION_KEY`.
- Serve the web build (`cd web && npm run build`) so the API can host `web/dist`.
- Terminate TLS in front of the API.
- Keep `REGRET_LIVE_TRADING_ENABLED=false` until Alpaca third-party live trading approval, security review, and explicit user consent are in place.

## Architecture

```text
Web / CLI / MCP
        ↓
   REGRET API
        ↓
 Decision engine (deterministic)
        ↓
 Alpaca paper or live adapter
```

Financial numbers are calculated in `src/regret/engine`. The language model, if configured, may parse a sentence or explain a result. It does not invent a number and it cannot submit an order.
