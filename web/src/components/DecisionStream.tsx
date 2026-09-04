import { useState } from "react";

export interface StreamEvent {
  id: string;
  seq: number;
  time: string;
  category: "SCAN" | "THESIS" | "RISK_GATE" | "ABSTAIN" | "ROUTED" | "LIFECYCLE" | "AUTO_EXIT";
  symbol: string;
  title: string;
  detail: string;
  status: "PASS" | "FAIL" | "INFO" | "SUCCESS";
}

const EVENTS: StreamEvent[] = [
  {
    id: "evt-010",
    seq: 142,
    time: "14:32:05",
    category: "LIFECYCLE",
    symbol: "SPY",
    title: "Active Position Manager: Profit Target Check",
    detail: "SPY 585P/580P Bull Put Spread current unrealized gain +$54.00 (47.0% of max profit). Approaching 50% auto-take-profit threshold ($57.50).",
    status: "INFO",
  },
  {
    id: "evt-009",
    seq: 141,
    time: "14:30:18",
    category: "ROUTED",
    symbol: "NVDA",
    title: "Alpaca Multi-Leg Order Executed",
    detail: "Order #apca-98231 filled: SELL_TO_OPEN 1x NVDA 125P @ $2.10, BUY_TO_OPEN 1x NVDA 120P @ $0.68. Net credit collected: +$142.00. Max loss: $358.00.",
    status: "SUCCESS",
  },
  {
    id: "evt-008",
    seq: 140,
    time: "14:30:15",
    category: "RISK_GATE",
    symbol: "NVDA",
    title: "Deterministic Risk Engine: 100% Passed (6/6)",
    detail: "NVDA 125P/120P Bull Put Spread cleared all 6 gates (Max loss $358 <= $500, Delta -0.19, Bid-Ask 2.8% <= 10%, Theta +$5.20/day, DTE 26). Approved for execution.",
    status: "PASS",
  },
  {
    id: "evt-007",
    seq: 139,
    time: "14:30:12",
    category: "THESIS",
    symbol: "NVDA",
    title: "Featherless AI (Qwen 2.5 72B): Strategic Setup",
    detail: "Generated 26 DTE Bull Put Spread (125P/120P) to harvest elevated variance risk premium (IV Rank 68.5%) above strong volume support at $122.50.",
    status: "INFO",
  },
  {
    id: "evt-006",
    seq: 138,
    time: "14:28:44",
    category: "ABSTAIN",
    symbol: "AAPL",
    title: "Market Regime Veto: Low Volatility Abstention",
    detail: "AAPL 52-week IV Rank 38.2% is below the required 50.0% threshold. Strategic engine logged deterministic abstention to preserve capital.",
    status: "FAIL",
  },
  {
    id: "evt-005",
    seq: 137,
    time: "14:28:40",
    category: "ABSTAIN",
    symbol: "MSFT",
    title: "Market Regime Veto: Low Volatility Abstention",
    detail: "MSFT 52-week IV Rank 31.4% below 50.0% hurdle. Trade entry blocked by regime filter.",
    status: "FAIL",
  },
  {
    id: "evt-004",
    seq: 136,
    time: "14:25:01",
    category: "SCAN",
    symbol: "ALL",
    title: "Autonomous Options Surface Sweep",
    detail: "Scanned option chains for SPY, QQQ, NVDA, IWM, AAPL, MSFT across 7 to 45 DTE expirations. Filtered 340 contracts for bid-ask liquidity.",
    status: "INFO",
  },
  {
    id: "evt-003",
    seq: 135,
    time: "14:15:22",
    category: "ROUTED",
    symbol: "QQQ",
    title: "Alpaca Multi-Leg Order Executed",
    detail: "Order #apca-98104 filled: SELL_TO_OPEN 1x QQQ 515C @ $1.85, BUY_TO_OPEN 1x QQQ 520C @ $0.60. Net credit collected: +$125.00. Max loss: $375.00.",
    status: "SUCCESS",
  },
  {
    id: "evt-002",
    seq: 134,
    time: "14:15:19",
    category: "RISK_GATE",
    symbol: "QQQ",
    title: "Deterministic Risk Engine: 100% Passed (6/6)",
    detail: "QQQ 515C/520C Bear Call Spread verified. Max loss $375 <= $500, Delta +0.16, Net Theta +$3.80/day, DTE 24. Approved for execution.",
    status: "PASS",
  },
  {
    id: "evt-001",
    seq: 133,
    time: "14:10:00",
    category: "LIFECYCLE",
    symbol: "IWM",
    title: "Pin-Risk & Expiration Safety Monitor",
    detail: "Verified active book DTE >= 18 days. Zero pin-risk or assignment vulnerability detected. Automatic early-exercise hedge active.",
    status: "INFO",
  },
];

export default function DecisionStream() {
  const [filter, setFilter] = useState<"ALL" | "PASS" | "ABSTAIN" | "ROUTED">("ALL");

  const filteredEvents = EVENTS.filter((e) => {
    if (filter === "ALL") return true;
    if (filter === "PASS") return e.status === "PASS" || e.category === "RISK_GATE";
    if (filter === "ABSTAIN") return e.category === "ABSTAIN" || e.status === "FAIL";
    if (filter === "ROUTED") return e.category === "ROUTED" || e.category === "AUTO_EXIT";
    return true;
  });

  return (
    <section className="stream-container" id="decision-stream" style={{ marginTop: 32 }}>
      <header style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        borderBottom: "1px solid var(--rule)",
        paddingBottom: 14,
        marginBottom: 20,
        flexWrap: "wrap",
        gap: 12
      }}>
        <div>
          <div className="eyebrow" style={{ margin: 0 }}>Agent 2 &amp; 3 · Chronological Audit Stream</div>
          <h2 style={{ fontSize: 24, margin: "4px 0 0" }}>Live Decision Stream &amp; Refusal Ledger</h2>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {(["ALL", "ROUTED", "PASS", "ABSTAIN"] as const).map((tab) => {
            const isSelected = filter === tab;
            const labels = {
              ALL: "All Events",
              ROUTED: "Broker Fills",
              PASS: "Gate Passes",
              ABSTAIN: "Refusals & Vetoes",
            };
            return (
              <button
                key={tab}
                type="button"
                onClick={() => setFilter(tab)}
                style={{
                  padding: "5px 10px",
                  fontSize: 11,
                  fontFamily: "var(--mono)",
                  textTransform: "uppercase",
                  borderRadius: 2,
                  border: isSelected ? "1px solid var(--ink)" : "1px solid var(--rule)",
                  background: isSelected ? "var(--ink)" : "transparent",
                  color: isSelected ? "var(--sheet)" : "var(--soft)",
                  cursor: "pointer",
                }}
              >
                {labels[tab]}
              </button>
            );
          })}
        </div>
      </header>

      <p style={{ color: "var(--soft)", fontSize: 14, margin: "0 0 18px", maxWidth: "72ch" }}>
        Every autonomous cycle leaves an immutable trail. The stream records scanner sweeps, Featherless LLM theses, deterministic code passes, and intelligent abstentions.
      </p>

      {/* Stream Box */}
      <div style={{
        background: "var(--sheet)",
        border: "1px solid var(--rule-strong)",
        borderRadius: 4,
        overflow: "hidden",
      }}>
        <div style={{
          display: "grid",
          gridTemplateColumns: "50px 75px 100px 70px 1fr",
          gap: 10,
          padding: "10px 14px",
          background: "rgba(26, 22, 18, 0.05)",
          borderBottom: "1px solid var(--rule)",
          fontFamily: "var(--mono)",
          fontSize: 10.5,
          color: "var(--faint)",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
        }}>
          <span>Seq</span>
          <span>Time</span>
          <span>Category</span>
          <span>Asset</span>
          <span>Event &amp; Rationale</span>
        </div>

        <div style={{ maxHeight: 420, overflowY: "auto", display: "flex", flexDirection: "column" }}>
          {filteredEvents.map((evt) => {
            const badgeBg = evt.category === "ROUTED" 
              ? "rgba(42, 70, 56, 0.15)" 
              : evt.category === "ABSTAIN" 
              ? "var(--err-bg)" 
              : evt.category === "RISK_GATE" 
              ? "rgba(42, 70, 56, 0.12)" 
              : "rgba(26, 22, 18, 0.06)";

            const badgeColor = evt.category === "ROUTED" 
              ? "var(--forest)" 
              : evt.category === "ABSTAIN" 
              ? "var(--oxblood)" 
              : evt.category === "RISK_GATE" 
              ? "var(--forest)" 
              : "var(--soft)";

            return (
              <div
                key={evt.id}
                style={{
                  display: "grid",
                  gridTemplateColumns: "50px 75px 100px 70px 1fr",
                  gap: 10,
                  padding: "12px 14px",
                  borderBottom: "1px solid var(--rule)",
                  fontSize: 12.5,
                  alignItems: "flex-start",
                }}
              >
                <span className="mono" style={{ color: "var(--faint)", fontSize: 11 }}>
                  #{evt.seq}
                </span>
                <span className="mono" style={{ color: "var(--soft)", fontSize: 11 }}>
                  {evt.time}
                </span>
                <div>
                  <span
                    style={{
                      fontFamily: "var(--mono)",
                      fontSize: 9.5,
                      fontWeight: 700,
                      padding: "2px 5px",
                      borderRadius: 2,
                      background: badgeBg,
                      color: badgeColor,
                      textTransform: "uppercase",
                    }}
                  >
                    {evt.category}
                  </span>
                </div>
                <span className="mono" style={{ fontWeight: 600, color: "var(--ink)", fontSize: 12 }}>
                  {evt.symbol}
                </span>
                <div>
                  <div style={{ fontWeight: 600, color: "var(--ink)", marginBottom: 2 }}>
                    {evt.title}
                  </div>
                  <div style={{ color: "var(--soft)", fontSize: 12, lineHeight: 1.4 }}>
                    {evt.detail}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
