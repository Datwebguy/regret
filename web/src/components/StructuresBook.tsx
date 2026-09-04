import { useState } from "react";

export interface StructureItem {
  id: string;
  symbol: string;
  strategy: "Bull Put Spread" | "Bear Call Spread";
  shortLeg: string;
  longLeg: string;
  shortStrike: number;
  longStrike: number;
  expiryDate: string;
  dte: number;
  netCredit: number;
  maxLoss: number;
  profitTarget50Pct: number;
  stopLoss2x: number;
  currentPl: number;
  status: "ACTIVE" | "CLOSING" | "CLOSED";
}

const STRUCTURES: StructureItem[] = [
  {
    id: "str-spy",
    symbol: "SPY",
    strategy: "Bull Put Spread",
    shortLeg: "SPY 585 Put",
    longLeg: "SPY 580 Put",
    shortStrike: 585,
    longStrike: 580,
    expiryDate: "2026-09-25",
    dte: 21,
    netCredit: 115.00,
    maxLoss: 385.00,
    profitTarget50Pct: 57.50,
    stopLoss2x: 230.00,
    currentPl: 54.00,
    status: "ACTIVE",
  },
  {
    id: "str-qqq",
    symbol: "QQQ",
    strategy: "Bear Call Spread",
    shortLeg: "QQQ 515 Call",
    longLeg: "QQQ 520 Call",
    shortStrike: 515,
    longStrike: 520,
    expiryDate: "2026-09-28",
    dte: 24,
    netCredit: 125.00,
    maxLoss: 375.00,
    profitTarget50Pct: 62.50,
    stopLoss2x: 250.00,
    currentPl: 76.00,
    status: "ACTIVE",
  },
  {
    id: "str-nvda",
    symbol: "NVDA",
    strategy: "Bull Put Spread",
    shortLeg: "NVDA 125 Put",
    longLeg: "NVDA 120 Put",
    shortStrike: 125,
    longStrike: 120,
    expiryDate: "2026-09-30",
    dte: 26,
    netCredit: 142.00,
    maxLoss: 358.00,
    profitTarget50Pct: 71.00,
    stopLoss2x: 284.00,
    currentPl: 55.00,
    status: "ACTIVE",
  },
  {
    id: "str-iwm",
    symbol: "IWM",
    strategy: "Bull Put Spread",
    shortLeg: "IWM 215 Put",
    longLeg: "IWM 210 Put",
    shortStrike: 215,
    longStrike: 210,
    expiryDate: "2026-09-22",
    dte: 18,
    netCredit: 98.00,
    maxLoss: 402.00,
    profitTarget50Pct: 49.00,
    stopLoss2x: 196.00,
    currentPl: 7.00,
    status: "ACTIVE",
  },
  {
    id: "str-aapl",
    symbol: "AAPL",
    strategy: "Bear Call Spread",
    shortLeg: "AAPL 225 Call",
    longLeg: "AAPL 230 Call",
    shortStrike: 225,
    longStrike: 230,
    expiryDate: "2026-09-26",
    dte: 22,
    netCredit: 57.00,
    maxLoss: 443.00,
    profitTarget50Pct: 28.50,
    stopLoss2x: 114.00,
    currentPl: -16.00,
    status: "ACTIVE",
  },
];

export default function StructuresBook() {
  const [structures] = useState<StructureItem[]>(STRUCTURES);

  const totalCredit = structures.reduce((sum, s) => sum + s.netCredit, 0);
  const totalMaxRisk = structures.reduce((sum, s) => sum + s.maxLoss, 0);
  const totalOpenPl = structures.reduce((sum, s) => sum + s.currentPl, 0);

  return (
    <section className="structures-container" id="structures-book" style={{ marginTop: 32 }}>
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
          <div className="eyebrow" style={{ margin: 0 }}>Agent 4 · Alpaca Multi-Leg Book</div>
          <h2 style={{ fontSize: 24, margin: "4px 0 0" }}>Defined-Risk Open Structures (5/5 Max)</h2>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="chip" style={{ color: "var(--forest)", borderColor: "var(--forest)" }}>
            50% Profit Target Active
          </span>
          <span className="chip" style={{ color: "var(--oxblood)", borderColor: "var(--oxblood)" }}>
            2.0x Stop Loss Guard
          </span>
        </div>
      </header>

      {/* Summary Metrics Strip */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
        gap: 12,
        marginBottom: 20,
      }}>
        <div style={{ background: "var(--sheet)", border: "1px solid var(--rule-strong)", padding: "12px 14px", borderRadius: 3 }}>
          <div className="mono" style={{ fontSize: 10.5, color: "var(--faint)", textTransform: "uppercase" }}>Upfront Cash Credit</div>
          <div className="mono" style={{ fontSize: 20, fontWeight: 700, color: "var(--forest)", marginTop: 4 }}>+${totalCredit.toFixed(2)}</div>
          <div style={{ fontSize: 11, color: "var(--soft)", marginTop: 2 }}>5 credit verticals</div>
        </div>

        <div style={{ background: "var(--sheet)", border: "1px solid var(--rule-strong)", padding: "12px 14px", borderRadius: 3 }}>
          <div className="mono" style={{ fontSize: 10.5, color: "var(--faint)", textTransform: "uppercase" }}>Aggregate Max Loss</div>
          <div className="mono" style={{ fontSize: 20, fontWeight: 700, color: "var(--ink)", marginTop: 4 }}>${totalMaxRisk.toFixed(2)}</div>
          <div style={{ fontSize: 11, color: "var(--soft)", marginTop: 2 }}>1.96% portfolio cap</div>
        </div>

        <div style={{ background: "var(--sheet)", border: "1px solid var(--rule-strong)", padding: "12px 14px", borderRadius: 3 }}>
          <div className="mono" style={{ fontSize: 10.5, color: "var(--faint)", textTransform: "uppercase" }}>Open Mark P&amp;L</div>
          <div className="mono" style={{ fontSize: 20, fontWeight: 700, color: totalOpenPl >= 0 ? "var(--forest)" : "var(--oxblood)", marginTop: 4 }}>
            {totalOpenPl >= 0 ? "+" : ""}${totalOpenPl.toFixed(2)}
          </div>
          <div style={{ fontSize: 11, color: "var(--soft)", marginTop: 2 }}>Mark-to-market spread</div>
        </div>

        <div style={{ background: "var(--sheet)", border: "1px solid var(--rule-strong)", padding: "12px 14px", borderRadius: 3 }}>
          <div className="mono" style={{ fontSize: 10.5, color: "var(--faint)", textTransform: "uppercase" }}>Assignment Risk</div>
          <div className="mono" style={{ fontSize: 20, fontWeight: 700, color: "var(--forest)", marginTop: 4 }}>0.0% (Covered)</div>
          <div style={{ fontSize: 11, color: "var(--soft)", marginTop: 2 }}>100% Defined risk</div>
        </div>
      </div>

      {/* Main Structures Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
        gap: 14,
      }}>
        {structures.map((s) => {
          const progressPct = Math.min(100, Math.max(0, (s.currentPl / s.profitTarget50Pct) * 100));
          return (
            <div
              key={s.id}
              style={{
                background: "var(--sheet)",
                border: "1px solid var(--rule-strong)",
                borderRadius: 4,
                padding: 16,
                display: "flex",
                flexDirection: "column",
                gap: 12,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span className="mono" style={{ fontSize: 16, fontWeight: 700, color: "var(--ink)" }}>{s.symbol}</span>
                    <span className="mono" style={{ fontSize: 11, color: "var(--soft)", background: "rgba(26, 22, 18, 0.05)", padding: "2px 6px", borderRadius: 2 }}>
                      {s.strategy}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: "var(--faint)", marginTop: 2 }}>
                    {s.shortLeg} / {s.longLeg}
                  </div>
                </div>

                <span style={{
                  fontFamily: "var(--mono)",
                  fontSize: 10,
                  fontWeight: 700,
                  padding: "2px 6px",
                  borderRadius: 2,
                  textTransform: "uppercase",
                  background: "rgba(42, 70, 56, 0.12)",
                  color: "var(--forest)",
                }}>
                  {s.status} · {s.dte} DTE
                </span>
              </div>

              {/* Spread Financial Metrics */}
              <div style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr 1fr",
                gap: 8,
                background: "rgba(26, 22, 18, 0.03)",
                padding: 10,
                borderRadius: 3,
                fontSize: 11.5,
                fontFamily: "var(--mono)",
              }}>
                <div>
                  <div style={{ color: "var(--faint)" }}>Credit:</div>
                  <strong style={{ color: "var(--forest)" }}>+${s.netCredit.toFixed(2)}</strong>
                </div>
                <div>
                  <div style={{ color: "var(--faint)" }}>Max Loss:</div>
                  <strong>${s.maxLoss.toFixed(2)}</strong>
                </div>
                <div>
                  <div style={{ color: "var(--faint)" }}>Open P&amp;L:</div>
                  <strong style={{ color: s.currentPl >= 0 ? "var(--forest)" : "var(--oxblood)" }}>
                    {s.currentPl >= 0 ? "+" : ""}${s.currentPl.toFixed(2)}
                  </strong>
                </div>
              </div>

              {/* Profit Target Progress Bar */}
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, fontFamily: "var(--mono)", color: "var(--soft)", marginBottom: 4 }}>
                  <span>50% Target: ${s.profitTarget50Pct.toFixed(2)}</span>
                  <span>Stop: -${s.stopLoss2x.toFixed(2)}</span>
                </div>
                <div style={{
                  height: 6,
                  background: "rgba(26, 22, 18, 0.1)",
                  borderRadius: 3,
                  overflow: "hidden",
                }}>
                  <div
                    style={{
                      height: "100%",
                      width: `${progressPct}%`,
                      background: s.currentPl >= 0 ? "var(--forest)" : "var(--oxblood)",
                      borderRadius: 3,
                      transition: "width 0.3s ease",
                    }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
