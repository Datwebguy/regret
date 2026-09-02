# REGRET Hackathon Worklog

**Date Started:** 2026-09-01  
**Project:** Alpaca AI Trading Agents Hackathon  
**Team:** Isheno Ebenezer (operator) + AI Agent  
**Critical Blocker:** OAuth authorize returns "unknown client" (waiting for Alpaca compliance)

---

## 1. Initial Status Check ✅

### Environment
- ✅ Python 3.11.9 available
- ✅ Virtual environment created and dependencies installed
- ✅ 88 tests passing, 1 skipped
- ✅ Production deployed on Fly.io (regret, iad region)

### Production Health
```json
{
  "ok": true,
  "env": "production",
  "broker_connect_available": true,       // OAuth secrets on Fly ✅
  "live_trading_enabled": false,          // Locked as required ✅
  "default_environment": "paper",         // Paper default ✅
  "llm_configured": false,                // Not required for hackathon
  "database": "ok"                        // SQLite on volume ✅
}
```

### Code Organization
- **FastAPI entry:** `src/regret/api/main.py`
- **Auth:** `src/regret/api/routes/auth.py`, `src/regret/services/auth.py`
- **Alpaca integration:** 
  - OAuth flow: `src/regret/services/connections.py`
  - Broker adapter: `src/regret/brokers/alpaca.py`
  - Market data: `src/regret/market/alpaca.py`
  - API facade: `src/regret/providers/alpaca.py`
- **Web UI:** React+Vite, Settings → Broker connects to `/api/alpaca/oauth/start`
- **Disclosure:** DDQ v.3 required copy in `web/src/lib/alpacaDisclosure.ts`

---

## 2. Critical Product Rules (DO NOT VIOLATE)

### Absolute Constraints
1. **No fake financial data** — All data must be real or labeled INSUFFICIENT
   - Check: `src/regret/services/account.py` (get_book, get_account, get_portfolio)
   - Check: `src/regret/market/alpaca.py` (quote, bars, news)
2. **AI never executes orders alone** — User must preview + confirm
   - Check: `POST /api/orders/confirm` requires `confirm: true` in body
3. **Paper and live separate** — Live trading OFF in production
   - Check: `fly.toml` has `REGRET_LIVE_TRADING_ENABLED = "false"`
   - Check: Web UI disables live option when platform flag is false
4. **User isolation** — No cross-user data leaks
   - Check: All routes get `user: User = Depends(current_user)`
   - Check: Alpaca connections per user, per environment
5. **No secrets in git or public output** — Use Fly secrets only
   - Check: `.gitignore` has `.env`, `.env.local`, etc.
   - Check: `fly.toml` has no secret values
   - Check: `oauth_status()` never leaks env var names

---

## 3. OAuth Blocker Analysis

### What's Deployed
- ✅ Client ID on Fly secret: `ALPACA_OAUTH_CLIENT_ID`
- ✅ Client Secret on Fly secret: `ALPACA_OAUTH_CLIENT_SECRET`
- ✅ Redirect URI correct: `https://regret.fly.dev/api/alpaca/callback`
- ✅ Authorization URL builds: `https://app.alpaca.markets/oauth/authorize?...`
- ✅ Token exchange flow implemented: `POST https://api.alpaca.markets/oauth/token`
- ✅ Disclosure shown before OAuth starts (DDQ v.3 requirement)

### What Users See Now
```
Alpaca OAuth Flow:
1. User clicks "Connect Alpaca" in Settings → Broker
2. Disclosure modal appears: "Authorize REGRET" + required paragraphs
3. User clicks "Allow" → redirect to Alpaca OAuth page
4. **ERROR: "Client authentication failed due to unknown client"**
5. ✋ This is NOT a REGRET bug — Alpaca hasn't activated the app yet
```

### Status (Per Handover)
- **When:** 13 August 2026, operator sent DDQ to support@alpaca.markets
- **What:** 
  - Completed OAuth DDQ v.3 (PDF)
  - REGRET Information Security Practices (PDF)
  - Screen recording of connect flow (MP4)
- **Next:** Alpaca compliance reviews and activates the Client ID
- **Timeline:** Unknown (external blocker)

### How to Verify When It Works
1. Alpaca will email: "Your application has been approved"
2. User tries Connect Alpaca → see Alpaca OAuth page (not error)
3. After authorization: `Settings → Broker → "Connected"` shows
4. `/api/alpaca/status` returns `"connected": true`
5. `/api/account` and `/api/portfolio` return **real** Alpaca paper data
6. Analyze shows real book positions in rules evaluation

---

## 4. Hackathon Critical Path

### Phase 1: Unblock OAuth (Wait on Alpaca)
- ⏳ **Blocker**: Alpaca compliance must activate Client ID
- **Owner**: Alpaca (support@alpaca.markets)
- **Our job**: Monitor inbox, confirm operator sent all materials
- **Do NOT**: Fake a successful OAuth response

### Phase 2: Validate OAuth End-to-End (When Alpaca Activates)
- [ ] Test on production: `https://regret.fly.dev`
- [ ] Create test account
- [ ] Click Settings → Broker → Connect Alpaca
- [ ] Confirm Alpaca OAuth page appears (not "unknown client" error)
- [ ] Click "Allow" → redirect back to Settings
- [ ] Verify Settings shows "Connected"
- [ ] Verify `/api/account` returns real Alpaca paper data
- [ ] **Prove**: Portfolio, positions, balances are live

### Phase 3: Validate Analyze + Order Flow (When Alpaca Activates)
- [ ] Create trade idea with real book data
- [ ] Analyze → verdict uses live Alpaca positions
- [ ] Preview order → shows real preview
- [ ] Confirm order → actually submitted to Alpaca paper
- [ ] Check order status → real Alpaca order status

### Phase 4: Hackathon Demo Ready
- [ ] All tests passing
- [ ] Production deployed with OAuth working
- [ ] User can: create account → connect Alpaca paper → analyze with real data → confirm order
- [ ] Documentation clear on what REGRET does (decision tool, not broker)

---

## 5. Code Review Checklist

### Auth Routes (`/api/auth`)
- [ ] POST `/api/auth/register` → cookie for browser, token for CLI ✅
- [ ] POST `/api/auth/login` → rotates session (fixation prevention) ✅
- [ ] POST `/api/auth/logout` → revokes session ✅
- [ ] GET `/api/auth/me` → works with cookie or bearer token ✅

### Alpaca Routes (`/api/alpaca`)
- [ ] GET `/api/alpaca/status` → never leaks env var names ✅
- [ ] POST `/api/alpaca/oauth/start` → returns authorization URL (not redirect) ✅
- [ ] GET `/api/alpaca/callback` → exchanges code, creates connection ✅
- [ ] POST `/api/alpaca/keys` → per-user encrypted storage ✅
- [ ] GET `/api/alpaca/book` → real Alpaca data only ✅
- [ ] DELETE `/api/alpaca/connection` → per environment ✅

### Order Routes (`/api/orders`)
- [ ] POST `/api/orders/preview` → deterministic, no execution ✅
- [ ] POST `/api/orders/confirm` → requires `confirm: true` ✅
- [ ] No auto-execution by AI alone ✅

### Market Data (`/api/quote`, `/api/bars`, `/api/news`)
- [ ] Never returns mocked/fake data ✅
- [ ] Returns INSUFFICIENT DATA if source fails ✅
- [ ] Respects rate limits, caches responsibly ✅

### Account Routes (`/api/account`, `/api/portfolio`, `/api/positions`)
- [ ] Only work if user has active connection ✅
- [ ] Return real Alpaca data ✅
- [ ] Per-user isolation ✅

---

## 6. Security Test Status

### Tests Passing ✅
```
tests/test_auth_phase1.py         → Browser session, CLI token, fixation prevention
tests/test_legal_pages.py         → Terms, privacy, legal routes
tests/test_alpaca_disclosure.py   → DDQ v.3 disclosure shown
tests/test_auth_security.py       → Rate limits, CSRF, auth isolation
tests/test_no_fake_data.py        → No mocked market data in paths
```

### Tests to Keep Green
- Always run before deploy: `python -m pytest -q`
- Never disable a security test
- If copy changes (disclosure, legal): add test coverage

---

## 7. Deployment Checklist

### Before Deploy
- [ ] `python -m pytest -q` passes (88+ tests)
- [ ] No secrets in code
- [ ] No `.env` file in git
- [ ] Changes are reviewed by operator

### Deploy Command
```powershell
cd C:\Users\DELL\Downloads\REGRET
$env:FLY_NO_WIREGUARD = "1"
$env:FLY_NO_UPDATE_CHECK = "1"
fly deploy -a regret --depot
```

### Post-Deploy
- [ ] `curl --ssl-no-revoke https://regret.fly.dev/api/health` → `"ok": true`
- [ ] Check logs: `fly logs -a regret | head -50`
- [ ] Test login on production
- [ ] Test Alpaca status endpoint (non-auth): `/api/alpaca/status`

---

## 8. Known Residuals (Do Not Oversell)

### Phase 1 Auth (Shipped)
- Rate limiter resets on deploy / multi-machine
- CSRF is origin allowlist, not synchronizer token
- Logout `delete_cookie` may omit Secure/HttpOnly on clear header
- SQLite on one Fly volume (not distributed)

### Not Implemented (Out of Scope)
- Google login / password reset / email verify / MFA / passkeys
- LLM commentary (llm_configured: false)
- PostgreSQL (still SQLite)
- Live trading (intentionally disabled)
- "Production-grade security" claims (audit found residuals)

---

## 9. Operator Identity (For Alpaca / Legal)

- **Name:** Isheno Ebenezer
- **Type:** Sole proprietorship (not LLC, not broker-dealer)
- **Email:** princeabel2000@gmail.com
- **Website:** https://regret.fly.dev
- **Not:** A registered broker-dealer or investment adviser
- **Product:** Trading decision tool (not execution, not copy-trading, not signal feed)

---

## 10. Files to Monitor

### If OAuth Flows
- `src/regret/services/connections.py` — OAuth state, token exchange
- `src/regret/providers/alpaca.py` — Account lookup, data fetch
- `web/src/pages/Settings.tsx` — Connect UI

### If Data Path Changes
- `src/regret/market/alpaca.py` — Quote, bars, news (no fakes!)
- `src/regret/brokers/alpaca.py` — Order submission
- `src/regret/services/orders.py` — Preview, confirm, status

### If Auth Changes
- `src/regret/api/routes/auth.py` — Endpoints
- `src/regret/services/auth.py` — Session logic
- `tests/test_auth_phase1.py` — Keep tests in sync

---

## 11. Session Memory (Updated)

- **Project:** REGRET (trading decision tool)
- **Status:** 88 tests passing, production deployed, OAuth blocked on Alpaca compliance
- **Critical:** Do not fake data, require user confirmation for orders, keep live trading OFF
- **Hackathon goal:** Unblock OAuth when Alpaca activates, validate end-to-end paper flow
- **Next action:** Monitor for Alpaca compliance email

---

## 12. Work Log

### 2026-09-01 (Session Start)
- ✅ Environment setup: venv, dependencies, tests passing
- ✅ Production health: broker_connect_available=true
- ✅ Code review: OAuth flow, auth, account routes
- ✅ Created this worklog
- **Blocked:** Waiting for Alpaca compliance to activate Client ID
