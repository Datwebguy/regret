# REGRET — agent handover

**Date:** 13 August 2026  
**Operator:** Isheno Ebenezer (`princeabel2000@gmail.com`)  
**Purpose:** Give the next agent everything needed to continue REGRET during the hackathon. Do not restart from a blank product.

This is a **real multi-user trading decision product**, not a mock. Read this whole file before editing.

---

## 1. Absolute product rules (locked)

1. **No fake financial data.** No mock prices, balances, positions, orders, or fills. If a source is missing, say so. `None` is not `0`.
2. **REGRET account ≠ Alpaca account.** Analyze works without a brokerage. Brokerage is optional and only needed for the real book / sending an order.
3. **AI never executes.** Deterministic engines first. An order is submitted only after preview + explicit user confirmation.
4. **Paper and live are separate.** Live order submission is **off** on production (`REGRET_LIVE_TRADING_ENABLED=false`). Do not turn live on.
5. **Web, CLI, and MCP share one engine** (Python, `Decimal`).
6. **User isolation.** One user cannot see another’s Alpaca connection or confirm another user’s approval.
7. **Official Alpaca docs only** for OAuth and APIs. Do not invent Alpaca success.
8. **Do not claim “production secure.”** Auth was hardened (Phase 1). Residuals remain.
9. **Do not invent legal entities, licenses, or SOC2.** Operator is a sole proprietor.
10. **Do not put secrets in git, `fly.toml`, chat, or the browser JSON.**

REGRET is a **decision app / tool**, not a broker-dealer, not an investment adviser, not copy-trading, not a signal feed.

---

## 2. Paths and live URLs

| What | Path / URL |
|---|---|
| Code | `C:\Users\DELL\Downloads\REGRET` |
| Alpaca upload pack (PDFs, screenshots, paper logo) | `C:\Users\DELL\Downloads\REGRET-alpaca-uploads` |
| Logo HTML sources | `C:\Users\DELL\Downloads\REGRET\alpaca-connect-assets\` |
| Win+G recordings | `C:\Users\DELL\Videos\Captures` |
| Production | https://regret.fly.dev |
| Health | https://regret.fly.dev/api/health |
| Terms | https://regret.fly.dev/terms |
| Privacy | https://regret.fly.dev/privacy |
| OAuth callback | https://regret.fly.dev/api/alpaca/callback |
| API docs (prod) | https://regret.fly.dev/api/docs |
| Fly dashboard | https://fly.io/apps/regret |
| Fly monitoring | https://fly.io/apps/regret/monitoring |
| Alpaca Connect | https://app.alpaca.markets/connect |
| Alpaca OAuth docs | https://docs.alpaca.markets/us/docs/using-oauth2-and-trading-api |
| Alpaca register app | https://docs.alpaca.markets/us/docs/registering-your-app |
| Alpaca about Connect | https://docs.alpaca.markets/us/docs/about-connect-api |

Health at handover:

```json
{"ok":true,"env":"production","broker_connect_available":true,"live_trading_enabled":false,"default_environment":"paper","llm_configured":false,"database":"ok"}
```

`broker_connect_available: true` means Client ID + Secret are set on Fly. It does **not** mean Alpaca authorize works. See §7.

---

## 3. What the product is

A user writes a trade idea. REGRET checks market data it can retrieve, the user’s written rules, and (if connected) the real Alpaca book. It returns a structured verdict: **BUY / WAIT / REDUCE / REJECT / INCOMPLETE**.

Then, only if the user previews and confirms, REGRET may submit a **paper** order. Submitted ≠ filled.

Stack:

- **API:** FastAPI, Python 3.11, SQLAlchemy 2, SQLite on a Fly volume (`/data/regret.db`)
- **Web:** React + Vite SPA, served by the same FastAPI origin (`/app/web/dist`)
- **CLI:** `regret` (`src/regret/cli/`), header `X-Regret-Client: cli`
- **MCP:** `src/regret/mcp_server/` talks to the REGRET API, not raw Alpaca
- **Host:** Fly.io app `regret`, region `iad`, machine `811d19db22d3d8`, 512mb shared, volume `regret_data`
- **Identity:** REGRET is source of record (Option A). No Google / reset / verify / MFA / passkeys yet.

Key packages:

- Engine: `src/regret/engine/` (`decision.py`, `rules.py`, `risk.py`, `why_not.py`, `market_analysis.py`, `intent.py`)
- Alpaca facade: `src/regret/providers/alpaca.py`
- Broker adapter: `src/regret/brokers/alpaca.py`
- Market: `src/regret/market/alpaca.py`
- Orders / proposal / analysis: `src/regret/services/`
- Auth HTTP: `src/regret/api/routes/auth.py`, `src/regret/api/security_http.py`, `src/regret/services/auth.py`

Verdicts and rule results must stay structured. Rule failures include FAILED + actual / required / difference. Missing data is INSUFFICIENT DATA, not a fake pass.

---

## 4. Operator / compliance identity

Use these if Alpaca or legal copy is involved. Do **not** invent an LLC.

- Legal name: **Isheno Ebenezer**
- Type: sole proprietorship / unincorporated
- Owner: Isheno Ebenezer, 100%
- Contact: Isheno Ebenezer, Operator, `princeabel2000@gmail.com`
- Website: https://regret.fly.dev
- Not a registered broker-dealer or investment adviser

Filled DDQ (send this, not a blank form):

- `C:\Users\DELL\Downloads\REGRET-alpaca-uploads\REGRET-OAuth-DDQ-V3-responses.pdf`
- `C:\Users\DELL\Downloads\REGRET-alpaca-uploads\REGRET-information-security-practices.pdf`

Source questionnaire: `C:\Users\DELL\Downloads\OAuth Due Diligence Questionnaire_V3.pdf`

Alpaca compliance contact: **Radzi (AlpacaDB, Inc.)** / **support@alpaca.markets**  
They asked (13 Aug 2026) for: completed OAuth DDQ + a short connect **video, not Loom**.

Suggested reply already drafted in this session (operator can paste):

```
Hello Radzi,

Please find attached:

1. Completed OAuth Due Diligence Questionnaire
2. REGRET Information Security Practices
3. Screen recording of the connect flow (not Loom), including the required Authorize REGRET disclosure and Deny / Allow

REGRET is a trading decision application operated by Isheno Ebenezer. Connecting a brokerage is optional and paper-only on the current deployment. Live trading is disabled. OAuth authorize currently returns “unknown client” until this review is complete.

Website: https://regret.fly.dev
Redirect: https://regret.fly.dev/api/alpaca/callback
Terms: https://regret.fly.dev/terms
Privacy: https://regret.fly.dev/privacy

Thank you,
Isheno Ebenezer
princeabel2000@gmail.com
```

Video: Xbox Game Bar (`Win + G` / `Win + Alt + R`). Saves to `C:\Users\DELL\Videos\Captures` as MP4. Record: sign in → Settings → Broker → Connect Alpaca → pause on **Authorize REGRET** + **Deny / Allow** → Allow. If Alpaca shows *unknown client*, leave it in.

---

## 5. Auth (Phase 1 — done)

Goals that shipped:

- Browser sessions are **cookie-only** (`regret_session`, HttpOnly, Secure in production, SameSite=Lax, path `/`, 7 days)
- Login/register JSON for browsers is `{ user }` only. **No token in the browser**
- SPA uses `credentials: "include"`. One-time `localStorage.removeItem("regret_token")`
- CLI/MCP still get a bearer token when `X-Regret-Client: cli` or no browser Origin
- Session tokens hashed SHA-256 at rest; passwords bcrypt cost 12
- Login/register rotate the session (fixation prevention)
- Login rate limit: 5 fails / email, 30 / IP, 900s. Register: 8 / IP / 3600s. In-memory, single machine
- Client IP: trust `Fly-Client-IP`, not `X-Forwarded-For`
- CSRF: Origin allowlist on unsafe methods when a cookie is present; missing Origin rejected in production; `/api/alpaca/callback` GET exempt
- Signed-in users hitting `/` or `/login` are sent back into the app (`sessionStorage` key `regret_last_app`)

Tests: `tests/test_auth_phase1.py`, `tests/test_auth_security.py`, `tests/test_auth_isolation.py`

**Do not implement in this phase unless the operator asks:** Google login, password reset, email verify, MFA, passkeys, IdP.

Residuals (do not oversell):

- Rate limiter resets on deploy / second machine
- Logout `delete_cookie` may omit Secure/HttpOnly on the clear header
- CSRF is origin allowlist, not a synchronizer token
- SQLite on one Fly volume

---

## 6. Fly / deploy

```powershell
cd C:\Users\DELL\Downloads\REGRET
$env:FLY_NO_WIREGUARD = "1"
$env:FLY_NO_UPDATE_CHECK = "1"
fly deploy -a regret --depot
```

`fly.exe` lives at `C:\Users\DELL\.fly\bin\fly.exe`. Auto-update was **disabled** after a failed self-update zeroed the binary. If `fly` dies with “no application associated”, restore from `C:\Users\DELL\.fly\bin\flyctl.exe.old` and run `fly settings autoupdate disable`.

Windows curl TLS: use `curl.exe --ssl-no-revoke`.

Secrets (names only — never print values):

| Secret | Status |
|---|---|
| `REGRET_SECRET_KEY` | Deployed |
| `REGRET_ENCRYPTION_KEY` | Deployed |
| `ALPACA_OAUTH_CLIENT_ID` | Deployed |
| `ALPACA_OAUTH_CLIENT_SECRET` | Deployed |

Set more secrets:

```powershell
fly secrets set NAME="value" -a regret
```

Dockerfile builds the Vite app then FastAPI. Listens on `0.0.0.0:8080`. Smoke check often warns “8080 not listening yet” during startup; health usually passes a few seconds later.

SQLite URL in production: `sqlite:////data/regret.db` on volume `regret_data`.

---

## 7. Alpaca Connect — current blocker

OAuth **client credentials are on Fly**. REGRET builds the official authorize URL:

`GET https://app.alpaca.markets/oauth/authorize?response_type=code&client_id=…&redirect_uri=https://regret.fly.dev/api/alpaca/callback&state=…&scope=data%20trading&env=paper`

Token exchange: `POST https://api.alpaca.markets/oauth/token`

Scopes used: `data` and `trading`. **Do not request `account:write`.**

**What users see today:** Alpaca page *“Client authentication failed due to unknown client…”*

This is **not a REGRET bug** if `client_id` in the URL matches the Alpaca dashboard Client ID (operator confirmed it matched). Alpaca has not activated the app for authorize. Official flow: submit app → get Client ID immediately → **compliance review** → then authorize works.

Forum/support has also blamed unpublished apps for this exact error. Publish is a directory listing; compliance email is the real gate.

**Do not** swap ID/secret again. An early attempt set a long hex as Client ID; that was corrected.

**Do not** claim OAuth “works” until a real user completes authorize and lands on Settings with `alpaca=connected`.

In-app connect UX (required by DDQ v.3, already in Settings → Broker):

1. User clicks **Connect Alpaca**
2. Disclosure appears: **Authorize REGRET** + two official paragraphs
3. **Deny** (stay) or **Allow** (then redirect to Alpaca)
4. Copy lives in `web/src/lib/alpacaDisclosure.ts`

Advanced path still exists: per-user encrypted API keys in Settings. Operator-only. Not the primary model.

Paper first. Live off.

---

## 8. Web UI (current)

- React + Vite, editorial paper look (`web/src/styles.css`)
- Mark: dark square, cream italic **R**, red bar (`web/public/mark.png`) — used as favicon and in chrome. Old cream “REGRET” square (`logo.png`) is for Alpaca 256×256 upload, not the tab icon
- Brand: `BrandMark` in `web/src/components/ui.tsx` uses **Link**, not NavLink (NavLink was highlighting the logo as the active Analyze item)
- Cookie session; password **Show / Hide** on login and register
- Hero on landing is **Ask if you should.** Tagline under the heading was removed
- Em dashes in UI copy were replaced; empty values show `n/a`
- Mobile landing header (latest): logo + REGRET on top; **Sign in** and **Create account** as two equal-width buttons underneath
- Desktop Analyze: dark spine, form, no double cream logo
- Operator was unhappy with several header iterations. Do not put auth links *above* the brand again. Do not use a weak text Sign in opposite a heavy Create button. Latest intent: brand first, then two matched buttons

Public legal HTML (no SPA required): `web/public/terms.html`, `privacy.html`, `legal.css` served at `/terms`, `/privacy`.

Favicon files: `web/public/favicon.ico`, `favicon-32.png`, `favicon-48.png`, `apple-touch-icon.png`, `mark.png`.

---

## 9. Local run

```powershell
cd C:\Users\DELL\Downloads\REGRET
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
python -m regret.api
```

Other terminal:

```powershell
cd C:\Users\DELL\Downloads\REGRET\web
npm install
npm run dev
```

Web: http://127.0.0.1:5173 (proxies `/api` to `:8000`)  
API: http://127.0.0.1:8000

Tests:

```powershell
cd C:\Users\DELL\Downloads\REGRET
python -m pytest -q
```

Auth + legal subset that was green recently: `tests/test_auth_phase1.py`, `tests/test_legal_pages.py`, `tests/test_alpaca_disclosure.py`.

There is **no `.venv` in the repo right now**; system Python 3.11 is what the last session used.

---

## 10. What is done vs not done

### Done

- Multi-user REGRET accounts, isolation
- Auth Phase 1 (cookies, CSRF origin, rate limits, no browser token)
- Analyze without Alpaca
- Deterministic rules / risk / WHY NOT / verdicts
- Order preview + confirm gate + `client_order_id` idempotency
- Real order status (submitted ≠ filled) when a connection exists
- Fly HTTPS deploy
- Terms + privacy live
- Alpaca OAuth client registered; secrets on Fly
- Connect disclosure + Deny/Allow
- DDQ PDFs filled for Isheno Ebenezer
- High-contrast favicon/mark
- Password visibility toggle
- Signed-in refresh stays in the app (if cookie is valid)

### Blocked on Alpaca (hackathon-critical)

- **OAuth authorize** until compliance activates the Client ID
- Full paper journey (portfolio from Alpaca, send paper order via OAuth) until that lands
- Optional: operator can still test paper via **Settings → Broker → Advanced** with **their own** paper API keys (encrypted, per user). That is not the multi-user OAuth story

### Not in scope unless asked

- Live trading
- Google / reset / verify / MFA
- LLM commentary (`llm_configured: false`)
- PostgreSQL migration (README mentions Postgres; production is still SQLite on the volume)
- Claiming production-grade security or compliance certification

---

## 11. Next work for the incoming agent (priority)

1. **Unblock paper OAuth**
   - Confirm operator sent DDQ + security PDF + MP4 to support@alpaca.markets
   - When Alpaca activates the client, test Connect end-to-end on https://regret.fly.dev (paper)
   - Prove: Settings shows connected, `/api/account` and `/api/portfolio` return **real** Alpaca paper data, Analyze can use the book, preview + confirm submits a paper order, status is truthful
2. **Do not fake a successful OAuth** while authorize still returns unknown client
3. **UI polish only after OAuth path is honest**
   - Mobile landing header was iterated many times; if changing it, show the operator a clear layout before more deploys
   - Desktop spine branding: mark + wordmark, no cream box, no active highlight on the logo
4. **If hacking a demo before Alpaca replies:** use Advanced API keys for **one operator paper account**, never a shared key, never live
5. **Keep tests green.** Add a test if you change disclosure copy (must stay DDQ v.3 wording)
6. **Deploy:** `FLY_NO_WIREGUARD=1`, `FLY_NO_UPDATE_CHECK=1`, `fly deploy -a regret --depot`

Success for the hackathon paper story:

- User creates REGRET account
- Connects **their** Alpaca paper via OAuth (or documented key fallback)
- Analyzes an idea with real data
- Sees BUY/WAIT/REDUCE/REJECT/INCOMPLETE with structured why
- Confirms an order only after preview
- Sees real broker status back

---

## 12. Commands cheat sheet

```powershell
# health
curl.exe --ssl-no-revoke https://regret.fly.dev/api/health

# secrets names only
fly secrets list -a regret

# deploy
cd C:\Users\DELL\Downloads\REGRET
$env:FLY_NO_WIREGUARD = "1"
$env:FLY_NO_UPDATE_CHECK = "1"
fly deploy -a regret --depot

# logs
fly logs -a regret

# tests
python -m pytest -q
```

Rebuild DDQ PDFs if identity copy changes:

```powershell
python C:\Users\DELL\Downloads\REGRET\scripts\build_alpaca_ddq.py
```

---

## 13. Files the next agent should open first

- This file
- `fly.toml`
- `src/regret/api/main.py`
- `src/regret/api/routes/auth.py`
- `src/regret/api/security_http.py`
- `src/regret/services/connections.py`
- `src/regret/providers/alpaca.py`
- `web/src/pages/Settings.tsx`
- `web/src/pages/Landing.tsx`
- `web/src/App.tsx`
- `web/src/lib/alpacaDisclosure.ts`
- `tests/test_auth_phase1.py`
- `tests/test_no_fake_data.py`

Do not commit `.env`, `.env.local`, Client Secret, or the contents of Fly secrets.

---

## 14. HTTP API map

All of these go through REGRET. MCP and CLI call these; they do not call Alpaca directly.

### Auth (`/api/auth`)

| Method | Path | Notes |
|---|---|---|
| POST | `/api/auth/register` | Cookie for browsers; `token` only for CLI |
| POST | `/api/auth/login` | Same |
| POST | `/api/auth/logout` | Revokes session, clears cookie |
| GET | `/api/auth/me` | Cookie or `Authorization: Bearer` |

### Alpaca (`/api/alpaca`)

| Method | Path | Notes |
|---|---|---|
| GET | `/api/alpaca/status` | Never leak env var names |
| POST | `/api/alpaca/oauth/start?environment=paper&purpose=trade` | Returns `authorization_url` |
| GET | `/api/alpaca/callback` | OAuth redirect; CSRF-exempt |
| POST | `/api/alpaca/keys` | Per-user encrypted keys (advanced) |
| GET | `/api/alpaca/book` | |
| DELETE | `/api/alpaca/connection` | |

### Account

| Method | Path |
|---|---|
| GET/PATCH | `/api/preferences` |
| GET | `/api/account` |
| GET | `/api/portfolio` |
| GET | `/api/positions` |
| GET | `/api/broker-orders` |

### Analyze / rules / market / orders

| Method | Path |
|---|---|
| POST | `/api/analyze` |
| GET | `/api/analyses`, `/api/analyses/{id}` |
| GET | `/api/insights` |
| GET/POST | `/api/setups` |
| GET/POST/DELETE | `/api/watchlist` |
| GET/POST/PATCH/DELETE | `/api/rules` |
| POST | `/api/rules/templates` |
| GET | `/api/quote/{symbol}`, `/api/bars/{symbol}`, `/api/news/{symbol}` |
| POST | `/api/orders/preview` |
| POST | `/api/orders/confirm` | Requires `confirm: true` |
| GET | `/api/orders`, `/api/orders/{id}` |
| POST | `/api/orders/{id}/cancel` |
| GET | `/api/journal`, `/api/theses`, `/api/monitor`, `/api/alerts` |

Public (no login): `GET /api/health`, `/terms`, `/privacy`, `/mark.png`, `/favicon.ico`.

---

## 15. Web routes

| Path | Page |
|---|---|
| `/` | Landing (signed-in users are redirected into `/app/...`) |
| `/login` `/register` | Auth, password Show/Hide |
| `/app` | Overview |
| `/app/analyze` | Analyze |
| `/app/setups` | Setups |
| `/app/portfolio` | Portfolio (needs connection) |
| `/app/rules` | Rules |
| `/app/journal` | Journal |
| `/app/monitor/:symbol` | Monitor |
| `/app/settings` `/app/settings/broker` | Account / Broker / Preferences |

---

## 16. MCP tools (all via REGRET API)

`src/regret/mcp_server/server.py` uses `ApiClient` (`X-Regret-Client: cli` + bearer).

`regret_get_account`, `regret_get_portfolio`, `regret_analyze_trade`, `regret_check_rules`, `regret_calculate_risk`, `regret_find_setups`, `regret_get_portfolio_context`, `regret_create_order_proposal`, `regret_create_trade_plan`, `regret_review_order`, `regret_approve_order`, `regret_execute_approved_order`, `regret_get_order_status`, `regret_get_trade_status`, `regret_monitor_trade`, `regret_get_journal`, `regret_get_behavior_insights`, `regret_execute_trade`.

Approve/execute still require explicit `confirm=true`. The model must not send an order on its own.

---

## 17. Environment variables

From `src/regret/config.py`. Production values for public config are in `fly.toml`. Secrets are Fly secrets only.

| Name | Prod / notes |
|---|---|
| `REGRET_ENV` | `production` |
| `REGRET_PUBLIC_URL` | `https://regret.fly.dev` |
| `REGRET_CORS_ORIGINS` | `https://regret.fly.dev` |
| `REGRET_DATABASE_URL` | `sqlite:////data/regret.db` |
| `REGRET_DEFAULT_TRADING_ENVIRONMENT` | `paper` |
| `REGRET_LIVE_TRADING_ENABLED` | `false` |
| `ALPACA_OAUTH_REDIRECT_URI` | `https://regret.fly.dev/api/alpaca/callback` |
| `REGRET_WEB_DIST` | `/app/web/dist` |
| `REGRET_SECRET_KEY` | Fly secret |
| `REGRET_ENCRYPTION_KEY` | Fly secret |
| `ALPACA_OAUTH_CLIENT_ID` | Fly secret |
| `ALPACA_OAUTH_CLIENT_SECRET` | Fly secret |
| `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` | Dev-only; never a shared multi-user identity |
| `REGRET_LLM_*` | Empty on prod |

---

## 18. Upload pack (Alpaca email)

Folder: `C:\Users\DELL\Downloads\REGRET-alpaca-uploads`

- `REGRET-OAuth-DDQ-V3-responses.pdf`
- `REGRET-information-security-practices.pdf`
- `regret-logo-256.png` (cream paper mark for Alpaca 256×256 slot)
- `regret-screenshot-connect-1024x500.png` (required disclosure)
- `regret-screenshot-landing-1024x500.png`
- `regret-screenshot-analyze-1024x500.png`
- Plus the connect MP4 from `C:\Users\DELL\Videos\Captures` (not Loom)

Site favicon is **not** that cream logo. Production chrome uses `web/public/mark.png` (dark square, cream italic R).

---

## 19. Prompt to paste to the next agent

```
You are continuing REGRET, a real trading decision product at C:\Users\DELL\Downloads\REGRET.
Read HANDOVER.md in that folder first. Do not restart the product. Do not fake Alpaca or market data.
Live app: https://regret.fly.dev  Health: /api/health
OAuth Client ID/Secret are on Fly but Alpaca authorize still returns unknown client until compliance activates the app. Operator: Isheno Ebenezer, princeabel2000@gmail.com.
Paper only. Live off. Cookie sessions. Analyze works without brokerage.
Next: get Alpaca Connect approved, then prove a real paper connect + analyze + preview + confirm. Do not claim OAuth works until that path succeeds.
Deploy with FLY_NO_WIREGUARD=1 FLY_NO_UPDATE_CHECK=1 fly deploy -a regret --depot.
```
