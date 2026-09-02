# OAuth Validation Workflow — For When Alpaca Activates

**When Alpaca sends:** "Your OAuth application has been approved for production use"

**Do this immediately:**

---

## Step 1: Confirm Alpaca Activation (5 min)

1. Forward Alpaca's approval email to AI agent
2. Check Fly dashboard for any deploy issues: https://fly.io/apps/regret
3. Verify health endpoint:
   ```powershell
   curl.exe --ssl-no-revoke https://regret.fly.dev/api/health
   # Should show: "broker_connect_available": true
   ```

---

## Step 2: Test OAuth Flow on Production (15 min)

### 2A. Create a clean test REGRET account
1. Visit: https://regret.fly.dev
2. Click "Create account"
3. Email: `test-oauth-YYYY-MM-DD@example.com` (use today's date)
4. Password: Something secure (you'll delete this account after)
5. Verify logged in

### 2B. Test OAuth Initiation
1. Go to: Settings → Broker
2. Click: "Connect Alpaca"
3. **Should see:** "Authorize REGRET" disclosure with Deny/Allow buttons
4. **Should NOT see:** "Client authentication failed"
5. Click: "Allow"

### 2C. Alpaca OAuth Page
1. **Should see:** Alpaca login page (or "you're already signed in")
2. **Should NOT see:** "unknown client" or "invalid application"
3. Sign in with your real Alpaca credentials (or click through if already signed in)
4. Review permissions
5. Click: "Authorize"

### 2D. OAuth Callback
1. **Should redirect back** to https://regret.fly.dev/app/settings/broker
2. **Should see:** Green message "Brokerage connected."
3. **Should see:** Connection details:
   - Status: Reachable
   - Environment: Paper
   - Account: Your Alpaca account number
   - Analyze: Available
   - Portfolio: Available
   - Orders: Paper orders allowed

### 2E. Verify Real Data
1. Go to: Analyze
2. Write: "Show my current positions"
3. Click: Analyze
4. **Should show:** Your real Alpaca paper positions (not empty, not fake)
5. If you have open positions, verify they match your Alpaca dashboard

---

## Step 3: Test Order Flow (10 min)

### 3A. Preview an Order
1. In Analyze, write: "Buy 1 AAPL at market"
2. Click: Analyze
3. Verdict should be: BUY or WAIT (not REJECT if AAPL is tradeable)
4. Click: "Preview order"
5. **Should show:**
   - Symbol: AAPL
   - Qty: 1
   - Order type: market
   - Estimated impact on your account

### 3B. Confirm & Submit (Real Order!)
1. Click: "Confirm order"
2. **Should redirect** to Orders page or status page
3. **Should show:** Order status = submitted or filled
4. **Check Alpaca dashboard:** Order should appear there too

### 3C. Cancel Order (If Still Open)
1. In REGRET, cancel the order
2. Verify status changes to "cancelled"
3. Verify it cancels in Alpaca dashboard too

---

## Step 4: Verify Test Results

| Check | Expected | ✅ or ❌ |
|-------|----------|-----------|
| Settings shows "Connected" | Yes | |
| Real Alpaca account number visible | Yes | |
| Portfolio loads real positions | Yes | |
| Analyze can use the book | Yes | |
| Order preview works | Yes | |
| Order confirm requires explicit action | Yes | |
| Order appears in Alpaca dashboard | Yes | |
| Tests still pass | 88/89 | |

---

## Step 5: Sign Off

### If All Tests Pass ✅
1. Delete test REGRET account (or leave it)
2. Notify AI agent: "OAuth validation passed, ready for submission"
3. AI agent will verify code one more time
4. Deploy final version (if needed)
5. **Submit to hackathon** with this workflow as proof

### If Any Test Fails ❌
1. Take a screenshot of the error
2. Note the exact step it failed
3. Forward to AI agent with details
4. AI agent will debug and fix

---

## Fallback (If Alpaca Takes Too Long)

**If you haven't heard from Alpaca after 7 days:**

1. You can test the paper flow manually using your own keys (Settings → Broker → Advanced)
2. AI agent can build a demo with your operator account
3. This won't be multi-user OAuth, but it proves the flow works
4. When Alpaca activates, switch to OAuth (same code path)

---

## Submit to Hackathon After Validation

**When ready, submit with:**
- [ ] This validation workflow completed
- [ ] All tests passing: `python -m pytest -q`
- [ ] Production URL: https://regret.fly.dev
- [ ] User can: sign up → connect Alpaca → analyze → order
- [ ] Live trading disabled
- [ ] No fake data
- [ ] Code available on GitHub (if needed)

---

## Support

- **OAuth broken?** Check: https://docs.alpaca.markets/us/docs/using-oauth2-and-trading-api
- **Need help?** Forward error to AI agent with screenshot
- **Questions?** Email Alpaca: support@alpaca.markets

---

**Expected Timeline:** 2-3 hours from Alpaca activation email to "ready for submission"
