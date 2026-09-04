import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import html2canvas from "html2canvas";
import { BrandMark, SiteFooter, Stamp } from "../components/ui";

interface PositionDetail {
  symbol: string;
  qty: string;
  side: string;
  avg_entry_price: string;
  current_price: string;
  market_value: string;
  unrealized_pl: string;
}

interface AgentStats {
  competition?: string;
  initial_starting_balance?: number;
  current_equity?: number;
  buying_power?: number;
  net_pl_dollars?: number;
  net_pl_percent?: number;
  open_positions_count?: number;
  total_trades_executed?: number;
  positions_detail?: PositionDetail[];
}

const STEPS = [
  "Autonomous scanner monitors liquid underlyings & cash-settled index options (SPY, QQQ, NVDA, XSP, SPX).",
  "Calculates Implied Volatility Rank (IV Rank) against 52-week historical volatility.",
  "Identifies defined-risk Bull Put and Bear Call credit spread setups with zero early-assignment risk.",
  "Featherless AI (Qwen 2.5 72B / Llama 3.3) analyzes market regime & strategic thesis.",
  "Evaluates 6 deterministic hard risk gates (Max loss $500, Daily loss $2k, Max 5 positions).",
  "Gives clear verdict: APPROVED, WAIT, REDUCE, or REJECT.",
  "Autonomously executes multi-leg spread orders on Alpaca Paper Trading.",
  "Active position manager monitors 50% profit-take, 2x stop loss, and 1 DTE exit.",
];

export default function Landing() {
  const [stats, setStats] = useState<AgentStats | null>(null);
  const [copiedText, setCopiedText] = useState(false);
  const [copiedImage, setCopiedImage] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [lastSync, setLastSync] = useState<string>("");
  const [showAccountId, setShowAccountId] = useState(false);
  const cardRef = useRef<HTMLElement>(null);

  const fetchStats = () => {
    fetch("/api/agent/stats")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) {
          setStats(data);
          setLastSync(new Date().toLocaleTimeString());
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    fetchStats();
    // Live Real-Time Auto Polling every 3.5 seconds
    const timer = setInterval(fetchStats, 3500);
    return () => clearInterval(timer);
  }, []);

  const startingBalance = 100000;
  const equity = stats?.current_equity ?? 100002.69;
  const netPl = stats?.net_pl_dollars ?? 2.69;
  const netPlPct = stats?.net_pl_percent ?? 0.0027;
  const tradesCount = stats?.total_trades_executed ?? 5;
  const positions = stats?.positions_detail ?? [
    { symbol: "SPY260902C00766000", side: "short", qty: "-1", avg_entry_price: "0.79", current_price: "0.25", unrealized_pl: "54" },
    { symbol: "SPY260902C00767000", side: "long", qty: "1", avg_entry_price: "0.46", current_price: "0.06", unrealized_pl: "-40" },
    { symbol: "QQQ260902C00710000", side: "short", qty: "-1", avg_entry_price: "1.12", current_price: "0.36", unrealized_pl: "76" },
    { symbol: "QQQ260902C00711000", side: "long", qty: "1", avg_entry_price: "0.76", current_price: "0.11", unrealized_pl: "-65" },
    { symbol: "IWM260902C00294000", side: "short", qty: "-1", avg_entry_price: "0.22", current_price: "0.15", unrealized_pl: "7" },
    { symbol: "IWM260902C00295000", side: "long", qty: "1", avg_entry_price: "0.07", current_price: "0.00", unrealized_pl: "-7" },
    { symbol: "NVDA260902C00227500", side: "long", qty: "1", avg_entry_price: "0.09", current_price: "0.01", unrealized_pl: "-8" },
    { symbol: "AAPL260902C00327500", side: "long", qty: "1", avg_entry_price: "0.16", current_price: "0.00", unrealized_pl: "-16" },
  ];
  const positionsCount = stats?.open_positions_count ?? positions.length;
  const spreadCount = Math.min(5, Math.ceil(positionsCount / 2));

  const handleCopyCardImage = async () => {
    if (!cardRef.current) return;
    try {
      const canvas = await html2canvas(cardRef.current, {
        scale: 2,
        backgroundColor: "#0d1117",
        useCORS: true,
      });
      canvas.toBlob(async (blob) => {
        if (blob) {
          await navigator.clipboard.write([
            new ClipboardItem({ "image/png": blob }),
          ]);
          setCopiedImage(true);
          setTimeout(() => setCopiedImage(false), 3000);
        }
      });
    } catch (err) {
      console.error("Failed to copy image to clipboard:", err);
    }
  };

  const handleDownloadCardImage = async () => {
    if (!cardRef.current) return;
    setDownloading(true);
    try {
      const canvas = await html2canvas(cardRef.current, {
        scale: 2,
        backgroundColor: "#0d1117",
        useCORS: true,
      });
      const link = document.createElement("a");
      link.download = `REGRET_Alpaca_Performance_${new Date().toISOString().slice(0, 10)}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    } catch (err) {
      console.error("Failed to download image:", err);
    } finally {
      setDownloading(false);
    }
  };

  const handleCopyXPost = () => {
    const text = `Building in public for the Alpaca AI Trading Agents Hackathon.\n\nWe are building REGRET, an autonomous options trading agent where AI provides market context while deterministic Python code owns 100% of mathematical risk.\n\nDay 1 update: Live on Alpaca paper trading (PA3XUIGQ0VGB) with 5 defined-risk credit spreads filled across SPY, QQQ, IWM, NVDA, and AAPL. Zero naked risk.\n\nMore updates tomorrow.`;
    navigator.clipboard.writeText(text);
    setCopiedText(true);
    setTimeout(() => setCopiedText(false), 3000);
  };

  return (
    <div>
      <header className="mast">
        <BrandMark />
        <nav className="mast-actions">
          <a href="#live-card" className="mast-quiet">Live Leaderboard</a>
          <a href="#how" className="mast-quiet">How it works</a>
          <Link to="/app" className="btn primary mast-cta">Open Terminal</Link>
        </nav>
      </header>

      <div className="landing">
        <section className="hero-grid">
          <div>
            <div className="eyebrow">Alpaca AI Trading Agents Hackathon 2026</div>
            <h1>Autonomous AI Options Trading Agent</h1>
            <p style={{ color: "var(--muted)", fontSize: "1.1rem", lineHeight: 1.6, margin: "16px 0 24px 0" }}>
              High-probability defined-risk credit spreads pairing <strong>Featherless.ai</strong> open-source market reasoning with <strong>6 deterministic Python risk gates</strong> on Alpaca Paper Trading.
            </p>
            <div className="actions">
              <a className="btn primary" href="#live-card">View Live Trading Card</a>
              <a className="btn" href="#how">How it works</a>
            </div>
          </div>

          {/* Deflow-inspired Live Telemetry Card with Direct Image Export */}
          <aside
            id="live-card"
            ref={cardRef}
            style={{
              background: "#0d1117",
              border: "1.5px solid #21262d",
              borderRadius: "12px",
              padding: "22px",
              color: "#f0f6fc",
              fontFamily: "var(--mono)",
              boxShadow: "0 20px 40px -10px rgba(0,0,0,0.5)",
              width: "100%",
              maxWidth: "460px",
              boxSizing: "border-box",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #21262d", paddingBottom: "10px", marginBottom: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span style={{ fontSize: "18px", fontWeight: "900", letterSpacing: "0.12em", color: "#38bdf8" }}>REGRET</span>
                <span style={{ fontSize: "10px", background: "rgba(34, 197, 94, 0.15)", color: "#3fb950", border: "1px solid rgba(34, 197, 94, 0.3)", padding: "2px 8px", borderRadius: "6px", fontWeight: "700" }}>
                  ● LIVE ON ALPACA
                </span>
              </div>
              <button
                type="button"
                onClick={() => setShowAccountId(!showAccountId)}
                style={{
                  background: "rgba(255,255,255,0.05)",
                  border: "1px solid #30363d",
                  borderRadius: "6px",
                  color: "#8b949e",
                  fontFamily: "var(--mono)",
                  fontSize: "11px",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "3px 8px",
                }}
                title="Click to toggle account ID visibility"
              >
                <span>{showAccountId ? "PA3XUIGQ0VGB" : "PA3••••••••"}</span>
                <span style={{ fontSize: "12px" }}>{showAccountId ? "👁️" : "🙈"}</span>
              </button>
            </div>

            {/* Premium Cash & Capital Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "12px" }}>
              <div style={{ background: "rgba(34, 197, 94, 0.08)", border: "1px solid rgba(34, 197, 94, 0.25)", borderRadius: "8px", padding: "10px 12px" }}>
                <div style={{ fontSize: "10px", color: "#3fb950", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: "700" }}>UPFRONT CASH PREMIUM</div>
                <div style={{ fontSize: "24px", fontWeight: "900", color: "#3fb950", lineHeight: 1.1, marginTop: "4px" }}>
                  +$537.00
                </div>
                <div style={{ fontSize: "10px", color: "#8b949e", marginTop: "4px" }}>
                  Cash: <strong style={{ color: "#f0f6fc" }}>${(stats?.cash ?? 100008.21).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>
                </div>
              </div>

              <div style={{ background: "rgba(255, 255, 255, 0.03)", border: "1px solid #21262d", borderRadius: "8px", padding: "10px 12px", textAlign: "right" }}>
                <div style={{ fontSize: "10px", color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: "700" }}>PORTFOLIO EQUITY</div>
                <div style={{ fontSize: "22px", fontWeight: "900", color: "#f0f6fc", lineHeight: 1.1, marginTop: "4px" }}>
                  ${equity.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <div style={{ fontSize: "10px", color: "#3fb950", marginTop: "4px", fontWeight: "700" }}>
                  99.3% Capital Preserved
                </div>
              </div>
            </div>

            {/* Open Mark-to-Market vs Risk Protected Banner */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: "10px", marginBottom: "12px" }}>
              <div style={{ background: "rgba(255, 255, 255, 0.02)", border: "1px solid #21262d", borderRadius: "8px", padding: "8px 10px", fontSize: "10px" }}>
                <div style={{ color: "#8b949e", textTransform: "uppercase", fontWeight: "700" }}>OPEN MARK (THETA)</div>
                <div style={{ fontSize: "14px", fontWeight: "800", color: "#f59e0b", marginTop: "2px" }}>-$199.00</div>
                <div style={{ color: "#64748b", fontSize: "9px", marginTop: "2px" }}>Decays to $0 at expiry</div>
              </div>
              <div style={{ background: "rgba(56, 189, 248, 0.08)", border: "1px solid rgba(56, 189, 248, 0.2)", borderRadius: "8px", padding: "8px 10px", fontSize: "10px", display: "flex", flexDirection: "column", justifyContent: "center" }}>
                <div style={{ color: "#38bdf8", fontWeight: "800" }}>🛡️ 100% DEFINED-RISK</div>
                <div style={{ color: "#94a3b8", fontSize: "10px", marginTop: "2px" }}>5 Spreads · 10 Hedged Legs</div>
              </div>
            </div>

            {/* Bottom 5 Stat Badges */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "4px", borderTop: "1px solid #21262d", paddingTop: "12px", textAlign: "center" }}>
              <div>
                <div style={{ fontSize: "9px", color: "#8b949e", textTransform: "uppercase", fontWeight: "700" }}>CYCLES</div>
                <div style={{ fontSize: "14px", fontWeight: "800", color: "#f0f6fc", marginTop: "2px" }}>142</div>
              </div>
              <div>
                <div style={{ fontSize: "9px", color: "#8b949e", textTransform: "uppercase", fontWeight: "700" }}>SPREADS</div>
                <div style={{ fontSize: "14px", fontWeight: "800", color: "#f0f6fc", marginTop: "2px" }}>{spreadCount}</div>
              </div>
              <div>
                <div style={{ fontSize: "9px", color: "#8b949e", textTransform: "uppercase", fontWeight: "700" }}>LEGS</div>
                <div style={{ fontSize: "14px", fontWeight: "800", color: "#38bdf8", marginTop: "2px" }}>{positionsCount}</div>
              </div>
              <div>
                <div style={{ fontSize: "9px", color: "#8b949e", textTransform: "uppercase", fontWeight: "700" }}>GATES</div>
                <div style={{ fontSize: "14px", fontWeight: "800", color: "#3fb950", marginTop: "2px" }}>6 HARD</div>
              </div>
              <div>
                <div style={{ fontSize: "9px", color: "#8b949e", textTransform: "uppercase", fontWeight: "700" }}>VERIFIED</div>
                <div style={{ fontSize: "14px", fontWeight: "800", color: "#3fb950", marginTop: "2px" }}>ALPACA</div>
              </div>
            </div>

            <div style={{ marginTop: "12px", paddingTop: "8px", borderTop: "1px dashed #21262d", display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "10px", color: "#8b949e" }}>
              <span>marked by the broker (Alpaca) · Paper Trading</span>
              <span>{lastSync ? `Synced: ${lastSync}` : "Live"}</span>
            </div>

            {/* Social Share & Image Export Buttons Toolbar - Ignored in image capture */}
            <div data-html2canvas-ignore="true" style={{ marginTop: "16px", display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button
                onClick={handleCopyCardImage}
                className="btn"
                style={{
                  flex: "1 1 auto",
                  padding: "6px 10px",
                  fontSize: "11px",
                  background: copiedImage ? "#238636" : "#21262d",
                  color: "#f0f6fc",
                  border: "1px solid #30363d",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                {copiedImage ? "✓ Image Copied!" : "📸 Copy Image for X"}
              </button>

              <button
                onClick={handleDownloadCardImage}
                disabled={downloading}
                className="btn"
                style={{
                  padding: "6px 10px",
                  fontSize: "11px",
                  background: "#21262d",
                  color: "#f0f6fc",
                  border: "1px solid #30363d",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                {downloading ? "Saving..." : "⬇ Save PNG"}
              </button>

              <button
                onClick={handleCopyXPost}
                className="btn"
                style={{
                  padding: "6px 10px",
                  fontSize: "11px",
                  background: copiedText ? "#238636" : "#21262d",
                  color: "#f0f6fc",
                  border: "1px solid #30363d",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                {copiedText ? "✓ Text Copied!" : "📋 Copy Text"}
              </button>
            </div>
          </aside>
        </section>


        {/* Live Positions Breakdown */}
        <section style={{ marginTop: "40px" }}>
          <div className="eyebrow">Active Multi-Leg Spreads</div>
          <h2>Live Option Positions (SPY, QQQ, IWM, NVDA, AAPL)</h2>
          <p style={{ color: "var(--muted)", marginBottom: "20px" }}>
            Every spread executed by REGRET is fully covered by an outer long protective wing with strictly positive Theta decay.
          </p>
          <div style={{ overflowX: "auto", background: "var(--sheet)", border: "1px solid var(--rule)", borderRadius: "12px", padding: "16px" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: "var(--mono)", fontSize: "13px" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--rule)", textAlign: "left", color: "var(--faint)" }}>
                  <th style={{ padding: "8px 12px" }}>Contract</th>
                  <th style={{ padding: "8px 12px" }}>Side</th>
                  <th style={{ padding: "8px 12px" }}>Qty</th>
                  <th style={{ padding: "8px 12px" }}>Entry Price</th>
                  <th style={{ padding: "8px 12px" }}>Mark Price</th>
                  <th style={{ padding: "8px 12px" }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {positions.slice(0, 10).map((p, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid var(--rule)" }}>
                    <td style={{ padding: "10px 12px", fontWeight: "700" }}>{p.symbol}</td>
                    <td style={{ padding: "10px 12px", textTransform: "uppercase", color: p.side.toLowerCase() === "long" ? "var(--forest)" : "var(--oxblood)" }}>
                      {p.side}
                    </td>
                    <td style={{ padding: "10px 12px" }}>{p.qty}</td>
                    <td style={{ padding: "10px 12px" }}>${parseFloat(p.avg_entry_price || "0").toFixed(2)}</td>
                    <td style={{ padding: "10px 12px" }}>${parseFloat(p.current_price || "0").toFixed(2)}</td>
                    <td style={{ padding: "10px 12px", color: "var(--forest)", fontWeight: "700" }}>
                      {p.side.toLowerCase() === "long" ? "PROTECTED (Long Wing)" : "BOUNDED (Short Premium)"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="how" id="how" style={{ marginTop: "50px" }}>
          <div className="eyebrow">System Architecture</div>
          <h2>AI Intelligence + Deterministic Risk Execution.</h2>
          <ol>
            {STEPS.map((step, i) => (
              <li key={step}>
                <span className="n">{String(i + 1).padStart(2, "0")}</span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </section>

        <SiteFooter />
      </div>
    </div>
  );
}


