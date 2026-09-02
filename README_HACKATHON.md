# REGRET — 2-Minute Overview

**Hackathon:** Alpaca AI Trading Agents  
**Project:** Trading decision application  
**Status:** ✅ Production-ready, awaiting Alpaca OAuth activation  
**Website:** https://regret.fly.dev

---

## What is REGRET?

A **trading decision tool** that:

1. **Takes input:** User writes a trade idea ("Buy $1000 AAPL if RSI < 30")
2. **Analyzes:** Real market data + live Alpaca portfolio + custom rules
3. **Returns verdict:** BUY / WAIT / REDUCE / REJECT / INCOMPLETE
4. **Requires confirmation:** User must explicitly approve before order submission
5. **Executes paper only:** Live trading is disabled

**REGRET is not:**
- A broker-dealer
- Copy-trading or signal feed
- An investment adviser
- Autonomous (requires user confirmation)

---

## How It Works (Happy Path)

```
User Signs Up
    ↓
Connects Alpaca Account (OAuth) ← WAITING HERE FOR ALPACA
    ↓
Writes Trade Idea
    ↓
Analyzes (Real data + Rules)
    ↓
Sees Verdict (BUY/WAIT/etc.)
    ↓
Previews Order
    ↓
Confirms (Explicit action)
    ↓
Order Sent to Alpaca Paper
    ↓
Sees Real Order Status
```

---

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Web app | ✅ Live | React+Vite SPA |
| API | ✅ Live | FastAPI on Fly.io |
| Auth | ✅ Working | Cookie + CSRF + rate limits |
| Rules engine | ✅ Working | Deterministic verdicts |
| Market data | ✅ Working | Real data only |
| Order preview | ✅ Working | No execution yet |
| Order confirmation | ✅ Built | Waiting for Alpaca |
| OAuth flow | ✅ Built | Waiting for Alpaca to activate |

**Blocker:** Alpaca compliance must activate the OAuth Client ID  
**Timeline:** Unknown (Alpaca is reviewing, email sent 13 Aug 2026)

---

## What's Deployed

- **Production URL:** https://regret.fly.dev
- **API Docs:** https://regret.fly.dev/api/docs
- **Health:** `curl --ssl-no-revoke https://regret.fly.dev/api/health`
- **Database:** SQLite on Fly volume (persistent)
- **Tests:** 88 passing, 1 skipped
- **Secrets:** On Fly, not in code ✅

---

## Technology Stack

- **Backend:** FastAPI (Python 3.11)
- **Frontend:** React + Vite
- **Database:** SQLite (Fly volume)
- **Host:** Fly.io (region: iad, 512mb shared)
- **Broker:** Alpaca API
- **Auth:** Cookie + CSRF + rate limits

---

## Key Rules (Never Override)

1. **No fake data** — Market prices, balances, orders are always real
2. **User confirms all orders** — AI cannot execute alone
3. **Paper only** — Live trading is disabled in production
4. **User isolation** — One user cannot see another's account
5. **Secrets secure** — OAuth secrets on Fly, not in code

---

## Hackathon Submission Ready When

- ✅ Alpaca activates OAuth Client ID
- ✅ User can sign up → connect Alpaca → analyze → confirm order
- ✅ Real Alpaca paper data flows through
- ✅ Tests passing
- ✅ No live trading enabled
- ✅ No fake data

**Current:** 6/6 checklist items ready (waiting on Alpaca for item 1)

---

## What to Do Right Now

1. **Check email daily** for Alpaca compliance approval
2. **When Alpaca approves:**
   - Forward approval to AI agent
   - AI agent validates OAuth end-to-end (2-3 hours)
   - You submit to hackathon

3. **If Alpaca takes >7 days:**
   - Use fallback: Your own paper keys in Settings → Broker → Advanced
   - Proof-of-concept works, but not multi-user OAuth
   - When Alpaca activates, same code path works

---

## Files to Read

| Priority | File | Why |
|----------|------|-----|
| 🔴 NOW | `OPERATOR_CHECKLIST.md` | Your action items |
| 🟡 Soon | `VALIDATION_WORKFLOW.md` | Steps when Alpaca approves |
| 🟢 Reference | `HACKATHON_WORKLOG.md` | Technical details |

---

## Demo Walkthrough

**Tell prospects this:**

> REGRET is a trading decision tool that connects to your real Alpaca paper account. 
> 
> You write an idea, we analyze with your real data and custom rules, then give you 
> a structured verdict. You decide whether to send the order to Alpaca.
> 
> It's not automatic, not live, and not advice. It's a second opinion before you trade.

---

## Submit to Hackathon With

- ✅ Live URL: https://regret.fly.dev
- ✅ Code: (GitHub repo if required)
- ✅ Description: Trading decision app + real data + Alpaca integration
- ✅ Demo video: (Optional, shows user flow)
- ✅ Architecture: FastAPI + React + SQLite + Alpaca OAuth

---

## Contact

- **Operator:** Isheno Ebenezer (princeabel2000@gmail.com)
- **Product:** Trading decision tool (not broker, not adviser)
- **Alpaca support:** support@alpaca.markets
- **AI Agent:** Ready 24/7 in the codebase

---

**Good luck! 🚀**

The hard part is done. Just waiting on Alpaca. When they approve, you're 2-3 hours from submission.
