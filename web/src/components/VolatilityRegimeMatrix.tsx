import React, { useState } from "react";

export interface RegimeItem {
  symbol: string;
  name: string;
  lastPrice: number;
  ivRank: number;
  iv30Hv60Ratio: number;
  trend: "Bullish" | "Bearish" | "Neutral";
  rsi: number;
  stance: "Bull Put Spread" | "Bear Call Spread" | "Abstain (IV Low)" | "Abstain (Earnings)";
  edgeActive: boolean;
  conviction: "High" | "Moderate" | "Low";
  reasoning: string;
}

const REGIME_DATA: RegimeItem[] = [
  {
    symbol: "SPY",
    name: "S&P 500 ETF Trust",
    lastPrice: 593.42,
    ivRank: 62.4,
    iv30Hv60Ratio: 1.28,
    trend: "Bullish",
    rsi: 54.2,
    stance: "Bull Put Spread",
    edgeActive: true,
    conviction: "High",
    reasoning: "IV Rank 62.4% > 50% threshold. S&P 500 trading above 50-day EMA support. Elevated put skew offers strong statistical edge for out-of-the-money credit collection.",
  },
  {
    symbol: "QQQ",
    name: "Invesco QQQ Trust (Nasdaq 100)",
    lastPrice: 512.80,
    ivRank: 58.1,
    iv30Hv60Ratio: 1.22,
    trend: "Neutral",
    rsi: 48.6,
    stance: "Bear Call Spread",
    edgeActive: true,
    conviction: "High",
    reasoning: "IV Rank 58.1% elevated due to semiconductor sector dispersion. Heavy overhead resistance at 520 level favors defined-risk credit call vertical.",
  },
  {
    symbol: "NVDA",
    name: "NVIDIA Corporation",
    lastPrice: 128.95,
    ivRank: 68.5,
    iv30Hv60Ratio: 1.35,
    trend: "Bullish",
    rsi: 58.1,
    stance: "Bull Put Spread",
    edgeActive: true,
    conviction: "High",
    reasoning: "Rich options premium (IV Rank 68.5%). High variance risk premium enables collecting $1.40+ credit on 20 delta puts backed by deep institutional demand zone at $120.",
  },
  {
    symbol: "IWM",
    name: "iShares Russell 2000 ETF",
    lastPrice: 221.30,
    ivRank: 52.0,
    iv30Hv60Ratio: 1.15,
    trend: "Bullish",
    rsi: 52.8,
    stance: "Bull Put Spread",
    edgeActive: true,
    conviction: "Moderate",
    reasoning: "Small-caps clearing 50% IV Rank hurdle. Bull Put spread structured with 10-point wing width to isolate positive Theta decay.",
  },
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    lastPrice: 229.80,
    ivRank: 38.2,
    iv30Hv60Ratio: 0.94,
    trend: "Neutral",
    rsi: 49.0,
    stance: "Abstain (IV Low)",
    edgeActive: false,
    conviction: "Low",
    reasoning: "IV Rank 38.2% is below the required 50% statistical threshold. Net selling premium does not offer sufficient compensation for directional risk.",
  },
  {
    symbol: "MSFT",
    name: "Microsoft Corporation",
    lastPrice: 422.15,
    ivRank: 31.4,
    iv30Hv60Ratio: 0.88,
    trend: "Bullish",
    rsi: 51.5,
    stance: "Abstain (IV Low)",
    edgeActive: false,
    conviction: "Low",
    reasoning: "Suppressed implied volatility regime (IV Rank 31.4%). AI agent automatically abstains to protect capital from low-reward setups.",
  },
];

export default function VolatilityRegimeMatrix() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>("SPY");
  const selectedItem = REGIME_DATA.find((r) => r.symbol === selectedSymbol) || REGIME_DATA[0];

  return (
    <section className="regime-container" id="volatility-regime" style={{ marginTop: 32 }}>
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
          <div className="eyebrow" style={{ margin: 0 }}>Agent 1 · Volatility Regime Readout</div>
          <h2 style={{ fontSize: 24, margin: "4px 0 0" }}>52-Week Implied Volatility Surface</h2>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="chip" style={{ color: "var(--forest)", borderColor: "var(--forest)" }}>
            IV Rank &gt; 50% Filter
          </span>
          <span className="chip" style={{ color: "var(--soft)", borderColor: "var(--rule-strong)" }}>
            Variance Risk Premium
          </span>
        </div>
      </header>

      <p style={{ color: "var(--soft)", fontSize: 14, margin: "0 0 18px", maxWidth: "72ch" }}>
        REGRET only enters when option prices are statistically expensive relative to historical volatility.
        Click any asset to inspect its live regime synthesis and open-source LLM thesis.
      </p>

      {/* Main Table */}
      <div style={{
        overflowX: "auto",
        border: "1px solid var(--rule-strong)",
        background: "var(--sheet)",
        borderRadius: 4,
        marginBottom: 20,
      }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, textAlign: "left" }}>
          <thead>
            <tr style={{
              background: "rgba(26, 22, 18, 0.04)",
              borderBottom: "1px solid var(--rule)",
              fontFamily: "var(--mono)",
              fontSize: 11,
              color: "var(--faint)",
              textTransform: "uppercase",
              letterSpacing: "0.08em"
            }}>
              <th style={{ padding: "10px 14px" }}>Symbol</th>
              <th style={{ padding: "10px 14px", textAlign: "right" }}>Last</th>
              <th style={{ padding: "10px 14px", width: "28%" }}>52-Wk IV Rank</th>
              <th style={{ padding: "10px 14px", textAlign: "right" }}>IV/HV Ratio</th>
              <th style={{ padding: "10px 14px" }}>Trend</th>
              <th style={{ padding: "10px 14px" }}>AI Stance</th>
              <th style={{ padding: "10px 14px", textAlign: "right" }}>Statistical Edge</th>
            </tr>
          </thead>
          <tbody>
            {REGIME_DATA.map((item) => {
              const isSelected = item.symbol === selectedSymbol;
              const hasEdge = item.edgeActive;
              return (
                <tr
                  key={item.symbol}
                  onClick={() => setSelectedSymbol(item.symbol)}
                  style={{
                    borderBottom: "1px solid var(--rule)",
                    cursor: "pointer",
                    background: isSelected ? "rgba(244, 238, 224, 0.9)" : "transparent",
                    transition: "background 0.15s ease",
                  }}
                >
                  <td style={{ padding: "12px 14px", fontWeight: 600 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span className="mono" style={{ color: "var(--ink)", fontSize: 14 }}>{item.symbol}</span>
                      <span style={{ fontSize: 11, color: "var(--faint)", fontWeight: 400 }}>{item.name}</span>
                    </div>
                  </td>
                  <td className="mono" style={{ padding: "12px 14px", textAlign: "right", color: "var(--ink)" }}>
                    ${item.lastPrice.toFixed(2)}
                  </td>
                  <td style={{ padding: "12px 14px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <div style={{
                        flex: 1,
                        height: 6,
                        background: "rgba(26, 22, 18, 0.1)",
                        borderRadius: 3,
                        overflow: "hidden",
                      }}>
                        <div
                          style={{
                            height: "100%",
                            width: `${item.ivRank}%`,
                            background: item.ivRank >= 50 ? "var(--forest)" : "var(--rule-strong)",
                            borderRadius: 3,
                          }}
                        />
                      </div>
                      <span className="mono" style={{
                        fontSize: 11,
                        width: 44,
                        textAlign: "right",
                        fontWeight: 600,
                        color: item.ivRank >= 50 ? "var(--forest)" : "var(--faint)",
                      }}>
                        {item.ivRank.toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className="mono" style={{ padding: "12px 14px", textAlign: "right", color: "var(--soft)" }}>
                    {item.iv30Hv60Ratio.toFixed(2)}x
                  </td>
                  <td style={{ padding: "12px 14px" }}>
                    <span style={{
                      fontSize: 11,
                      fontFamily: "var(--mono)",
                      color: item.trend === "Bullish" ? "var(--forest)" : item.trend === "Bearish" ? "var(--oxblood)" : "var(--soft)",
                      fontWeight: 600,
                    }}>
                      {item.trend === "Bullish" ? "↗ Bullish" : item.trend === "Bearish" ? "↘ Bearish" : "→ Neutral"}
                    </span>
                  </td>
                  <td style={{ padding: "12px 14px" }}>
                    <span style={{
                      fontSize: 11,
                      fontFamily: "var(--mono)",
                      padding: "2px 8px",
                      borderRadius: 2,
                      fontWeight: 600,
                      background: hasEdge ? "rgba(42, 70, 56, 0.12)" : "rgba(26, 22, 18, 0.05)",
                      color: hasEdge ? "var(--forest)" : "var(--faint)",
                    }}>
                      {item.stance}
                    </span>
                  </td>
                  <td style={{ padding: "12px 14px", textAlign: "right" }}>
                    <span style={{
                      fontFamily: "var(--mono)",
                      fontSize: 11,
                      fontWeight: 700,
                      color: hasEdge ? "var(--forest)" : "var(--faint)",
                    }}>
                      {hasEdge ? "ACTIVE EDGE" : "ABSTAINED"}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Selected Underlying Deep Dive Panel */}
      <div style={{
        background: "var(--sheet)",
        border: "1px solid var(--rule-strong)",
        borderRadius: 4,
        padding: 18,
        display: "grid",
        gridTemplateColumns: "1fr 2fr",
        gap: 20,
      }}>
        <div>
          <div className="mono" style={{ fontSize: 11, color: "var(--faint)", textTransform: "uppercase", letterSpacing: "0.1em" }}>
            LLM Strategic Thesis · {selectedItem.symbol}
          </div>
          <div style={{ fontSize: 18, fontWeight: 600, marginTop: 4, color: "var(--ink)" }}>
            {selectedItem.name}
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
            <span className="chip" style={{ color: selectedItem.edgeActive ? "var(--forest)" : "var(--oxblood)" }}>
              {selectedItem.edgeActive ? "IV Edge Qualified" : "Filtered (Low IV)"}
            </span>
            <span className="chip" style={{ color: "var(--soft)" }}>
              Conviction: {selectedItem.conviction}
            </span>
          </div>
        </div>

        <div>
          <div className="mono" style={{ fontSize: 11, color: "var(--faint)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>
            Featherless Reasoning (Qwen 2.5 72B / Llama 3.3)
          </div>
          <p style={{ fontSize: 13.5, color: "var(--ink)", lineHeight: 1.55, margin: 0 }}>
            {selectedItem.reasoning}
          </p>
        </div>
      </div>
    </section>
  );
}
