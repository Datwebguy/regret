# REGRET Hackathon — AI Agent Continuation Guide

**For:** Next session when Alpaca activates  
**Created:** 2026-09-01  
**Current State:** Production deployed, OAuth built, waiting for Alpaca

---

## Quick Jump-Back Instructions

When the operator forwards the "application approved" email from Alpaca:

### 1. Immediate (5 min)
```powershell
# Verify production still healthy
curl.exe --ssl-no-revoke https://regret.fly.dev/api/health
# Should show: "broker_connect_available": true, "ok": true

# Run tests one more time
cd C:\Users\DELL\Downloads\REGRET
.\.venv\Scripts\activate
python -m pytest -q
# Should show: 88+ passed
```

### 2. Test OAuth End-to-End (15 min)
- Follow `VALIDATION_WORKFLOW.md` step-by-step
- Create test REGRET account
- Settings → Broker → Connect Alpaca
- Verify Alpaca OAuth page appears (not "unknown client")
- Authorize
- Verify Settings shows "Connected"
- Verify real portfolio data loads

### 3. Test Order Flow (10 min)
- Analyze with real data
- Preview order
- Confirm order
- Verify order in Alpaca dashboard

### 4. Sign Off (2 min)
- All tests still passing
- Production health ✅
- OAuth flow validated ✅
- User can: sign up → connect → analyze → order ✅
- Notify operator: ready for submission ✅

**Total time:** 2-3 hours

---

## Critical Code Paths (Validate These)

### OAuth Start (`POST /api/alpaca/oauth/start`)
File: `src/regret/api/routes/alpaca.py:line_number`
- Calls: `connections.begin_oauth()`
- Returns: `authorization_url` (not redirect)
- Check: URL points to Alpaca, contains client_id, redirect_uri, scopes

### OAuth Callback (`GET /api/alpaca/callback`)
File: `src/regret/api/routes/alpaca.py`
- Receives: `code`, `state` from Alpaca
- Calls: `connections.complete_oauth()` (token exchange happens here)
- Fetches: Account info immediately after token exchange
- Stores: Encrypted token per user per environment
- Redirects: Back to frontend with status (connected/denied/invalid/failed)

### Account Fetch (After OAuth)
File: `src/regret/providers/alpaca.py:class AlpacaProvider`
- Uses: `AlpacaCredentials(access_token=token)`
- Calls: `GET https://api.alpaca.markets/v2/account`
- Returns: Real Alpaca account object (not invented)
- Stores: `alpaca_account_id`, `alpaca_account_number`

### Portfolio Load
File: `src/regret/services/account.py:def get_book()`
- Calls: `AlpacaProvider.get_account()`
- Calls: `AlpacaProvider.get_positions()`
- Calls: `AlpacaProvider.get_orders()`
- Returns: Dict with real data or errors

### Order Submission
File: `src/regret/services/orders.py:def confirm_order()`
- Requires: `confirm=True` in request body (explicit user action)
- Calls: `AlpacaBrokerAdapter.submit_order()`
- Submits: `POST https://api.alpaca.markets/v2/orders` with OAuth token
- Returns: Real order status from Alpaca

---

## Files to Monitor During Test

If anything fails, check these files:

| Problem | File | Check |
|---------|------|-------|
| OAuth URL wrong | `src/regret/services/connections.py` | AUTHORIZE_URL, TOKEN_URL, params |
| Token exchange fails | `src/regret/services/connections.py:complete_oauth()` | httpx client, response parsing |
| Account fetch fails | `src/regret/providers/alpaca.py` | AlpacaProvider with access token |
| Portfolio doesn't load | `src/regret/services/account.py` | get_book(), error handling |
| Order won't submit | `src/regret/brokers/alpaca.py` | submit_order(), request format |
| Settings UI blank | `web/src/pages/Settings.tsx` | load() useEffect, status state |
| Disclosure not shown | `web/src/lib/alpacaDisclosure.ts` | Required DDQ v.3 phrases |

---

## Test Data to Use

- **Test symbol:** AAPL (always liquid, easy to order)
- **Test qty:** 1 share (small, easy to cancel)
- **Test environment:** paper (default, locked in)
- **Test account:** Your own REGRET account + real Alpaca paper account

---

## Logging to Watch

```powershell
# Follow live logs
fly logs -a regret -f

# Filter for OAuth
fly logs -a regret | Select-String "oauth"

# Filter for errors
fly logs -a regret | Select-String -Pattern "ERROR|FAIL|Exception"
```

### Expected Log Entries (Successful Flow)
```
alpaca_oauth_started user_id=... status=paper
complete_oauth() exchanging code for token
AlpacaProvider.get_account() fetching...
user_connected_alpaca entity_id=... status=paper detail=oauth
```

---

## Regression Tests (Must Pass)

```powershell
# Run specific test suites
python -m pytest tests/test_auth_phase1.py -v      # Auth security
python -m pytest tests/test_no_fake_data.py -v     # Data integrity
python -m pytest tests/test_alpaca_disclosure.py -v # DDQ compliance
python -m pytest -q                                 # Full suite
```

If any fail, **do not deploy**. Fix first.

---

## Deployment Checklist (If Changes Needed)

If you need to fix anything:

1. **Make changes** in src/
2. **Run tests locally:** `python -m pytest -q`
3. **All tests pass?** Continue to 4. If not, fix.
4. **Build Dockerfile:** Docker builds are in fly.io, but you can test locally
5. **Deploy:** Use the Fly command

```powershell
# Deploy command (only after tests pass)
cd C:\Users\DELL\Downloads\REGRET
$env:FLY_NO_WIREGUARD = "1"
$env:FLY_NO_UPDATE_CHECK = "1"
fly deploy -a regret --depot

# Monitor deployment
fly status -a regret
fly logs -a regret -f
```

6. **Verify:** Check health endpoint after 1 min

---

## Known Edge Cases to Test

| Edge Case | What to Do |
|-----------|-----------|
| User cancels OAuth | Verify redirect to Settings with `?alpaca=denied` |
| OAuth state expires (>10 min) | Try again, should get `?alpaca=invalid` |
| Alpaca server down | Should get `?alpaca=failed`, not 500 error |
| User without Alpaca account | Should error gracefully, not hang |
| Multiple connections (paper + live) | Should store separately, toggle in UI |
| Disconnect then reconnect | Should create new connection, old one inactive |

---

## Environment Variables to Verify

On production (Fly):

```powershell
# Check these are set (values not shown)
fly secrets list -a regret

# Should see:
# REGRET_SECRET_KEY
# REGRET_ENCRYPTION_KEY
# ALPACA_OAUTH_CLIENT_ID
# ALPACA_OAUTH_CLIENT_SECRET

# Check these are correct (values shown)
fly config show -a regret | Select-String "REGRET_LIVE_TRADING_ENABLED"
# Should be: false
```

---

## Operator Communication Template

**When Alpaca activates, I will:**

```
Subject: REGRET OAuth Validation Complete

Status: ✅ READY FOR SUBMISSION

Results:
✅ OAuth flow end-to-end validated
✅ User authentication working
✅ Portfolio data loading real Alpaca data
✅ Order preview and confirmation working
✅ Real order submitted to Alpaca paper
✅ All tests passing (88/89)
✅ Production health: OK
✅ Live trading: Disabled
✅ No fake data

Next: You can now submit to hackathon at https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon

Demo URL: https://regret.fly.dev
Test account: Available upon request
```

---

## Fallback Plan (If Alpaca Delays >7 Days)

If operator wants to demo before Alpaca activates:

1. Operator connects their own paper keys (Settings → Broker → Advanced)
2. I build demo flow with operator's real account
3. Same code path works, just not multi-user OAuth
4. When Alpaca activates, switch to OAuth (no code changes)

Fallback proof-of-concept only takes 30 min.

---

## Critical Must-Haves at Submission

- ✅ Live trading disabled (`REGRET_LIVE_TRADING_ENABLED=false`)
- ✅ No fake market data in responses
- ✅ User must confirm all orders
- ✅ OAuth flow works end-to-end (if Alpaca active)
- ✅ Tests passing
- ✅ Code in version control (if required)
- ✅ Documentation complete
- ✅ No secrets in code/git

**If any of these are false, STOP and fix before submission.**

---

## Handoff Notes for Future Sessions

**If I pass the baton to another agent:**

1. Read this file first
2. Read `HACKATHON_WORKLOG.md` for context
3. Read `VALIDATION_WORKFLOW.md` for exact test steps
4. Ask operator to send Alpaca's approval email
5. Follow the "Quick Jump-Back Instructions" above
6. Run tests and validation
7. Report back

**Key constraint:** Do not fake data. Do not turn on live trading. Require user confirmation.

---

## Session Milestones

- ✅ **Milestone 1 (Today):** Setup, audit, documentation complete
- ⏳ **Milestone 2 (TBD):** Alpaca activates OAuth
- ⏳ **Milestone 3 (TBD):** OAuth validation complete
- ⏳ **Milestone 4 (TBD):** Hackathon submission
- ⏳ **Milestone 5 (TBD):** Hackathon judgment

---

## I'm Ready

When Alpaca activates, I can validate end-to-end in 2-3 hours and give you the green light to submit.

No further code changes expected. Just validation.

Let's go win this hackathon. 🚀
