import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, api } from "../api";
import { Empty, Figure, PageHead, RuleTone, Stamp } from "../components/ui";
import { money, num, when } from "../lib/format";

function ideaLine(intent: any, fallback: string) {
  if (!intent?.symbol) return fallback;
  const side = intent.side === "sell" ? "Sell" : "Buy";
  if (intent.notional) return `${side} ${money(intent.notional)} of ${intent.symbol}`;
  if (intent.quantity) return `${side} ${intent.quantity} ${intent.symbol}`;
  return `${side} ${intent.symbol}`;
}

export default function Analyze() {
  const [text, setText] = useState("");
  const [stop, setStop] = useState("");
  const [target, setTarget] = useState("");
  const [proposeStop, setProposeStop] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<any>(null);
  const [preview, setPreview] = useState<any>(null);
  const [execution, setExecution] = useState<any>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    setPreview(null);
    setExecution(null);
    try {
      setResult(await api.post("/api/analyze", {
        text,
        stop_price: stop || null,
        target_price: target || null,
        propose_stop: proposeStop,
      }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The analysis could not be completed.");
    } finally {
      setLoading(false);
    }
  }

  async function previewOrder() {
    setError("");
    try {
      setPreview(await api.post("/api/orders/preview", { analysis_id: result.analysis_id }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The trade could not be prepared for review.");
    }
  }

  async function execute(acceptSuggested = false) {
    if (!preview) return;
    setError("");
    try {
      setExecution(await api.post("/api/orders/confirm", {
        approval_id: preview.approval_id,
        confirm: true,
        accept_suggested_size: acceptSuggested,
      }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The order was not sent.");
    }
  }

  const [mode, setMode] = useState<"options" | "equity">("options");
  const [optionsSymbols, setOptionsSymbols] = useState("SPY, QQQ, NVDA");
  const [minIvRank, setMinIvRank] = useState(40);
  const [optionsResult, setOptionsResult] = useState<any>(null);
  const [optionsLoading, setOptionsLoading] = useState(false);

  async function scanOptions() {
    setOptionsLoading(true);
    setError("");
    try {
      const symList = optionsSymbols.split(",").map((s) => s.trim().toUpperCase()).filter(Boolean);
      const res: any = await api.post("/api/analyze/options", {
        symbols: symList,
        min_iv_rank: minIvRank,
      });
      setOptionsResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Options scan could not be completed.");
    } finally {
      setOptionsLoading(false);
    }
  }

  const decision = result?.decision;
  const market = decision?.market;
  const risk = decision?.risk;
  const portfolio = decision?.portfolio;
  const rules = decision?.rules?.checks || [];
  const why = decision?.why_not?.items || [];
  const intent = result?.intent;
  const verdict = result?.verdict;
  const nextCondition = decision?.next_condition;
  const primaryWhy = (decision?.reasons || []).filter((r: string) => r && !r.startsWith("Portfolio check unavailable"))[0]
    || result?.summary;
  const marketData = result?.market_data || result?.report?.market;
  const setup = decision?.setup || decision?.entry;

  return (
    <div className="stack">
      <PageHead
        kicker="Analyze & Strategy Screener"
        title="Options & Equity Analysis"
        lead="Screen elevated IV Rank options spreads with Featherless AI reasoning and deterministic hard risk gates."
      />

      <nav className="tabs" style={{ marginBottom: 16 }}>
        <button 
          className={`tab-btn ${mode === "options" ? "active" : ""}`} 
          onClick={() => setMode("options")}
          style={{ background: mode === "options" ? "var(--accent)" : "transparent", color: mode === "options" ? "#fff" : "inherit", padding: "8px 16px", borderRadius: 6, border: "1px solid var(--rule)", marginRight: 8, cursor: "pointer" }}
        >
          ⚡ Options Screener & AI Spreads
        </button>
        <button 
          className={`tab-btn ${mode === "equity" ? "active" : ""}`} 
          onClick={() => setMode("equity")}
          style={{ background: mode === "equity" ? "var(--accent)" : "transparent", color: mode === "equity" ? "#fff" : "inherit", padding: "8px 16px", borderRadius: 6, border: "1px solid var(--rule)", cursor: "pointer" }}
        >
          Equity / Manual Trade
        </button>
      </nav>

      {mode === "options" && (
        <section className="sheet">
          <div className="sheet-head">
            <h3>IV Rank Mean Reversion Options Screener</h3>
          </div>
          <div className="grid cols-2" style={{ marginTop: 12 }}>
            <div className="field">
              <label>Symbols to Scan</label>
              <input 
                value={optionsSymbols} 
                onChange={(e) => setOptionsSymbols(e.target.value)} 
                placeholder="SPY, QQQ, NVDA, IWM" 
              />
            </div>
            <div className="field">
              <label>Minimum IV Rank Threshold ({minIvRank}%)</label>
              <input 
                type="range" 
                min={10} 
                max={90} 
                value={minIvRank} 
                onChange={(e) => setMinIvRank(Number(e.target.value))} 
              />
            </div>
          </div>
          <button 
            className="btn primary" 
            onClick={scanOptions} 
            disabled={optionsLoading}
            style={{ marginTop: 12 }}
          >
            {optionsLoading ? "Scanning Chains & Querying Featherless AI..." : "Scan Options & Generate Setups"}
          </button>

          {optionsResult && (
            <div style={{ marginTop: 20 }}>
              <div style={{ padding: "8px 12px", background: "rgba(56, 189, 248, 0.1)", borderRadius: 6, marginBottom: 16 }}>
                <strong>Scan Summary:</strong> Scanned {optionsResult.summary?.total_scanned} symbols | Found {optionsResult.summary?.opportunities_found} setups | Proposals generated: {optionsResult.summary?.proposals_generated}
              </div>

              <div className="stack" style={{ gap: 16 }}>
                {optionsResult.scans?.map((s: any) => (
                  <div key={s.symbol} style={{ border: "1px solid var(--rule)", borderRadius: 8, padding: 16, background: "rgba(0,0,0,0.2)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <h4 style={{ margin: 0, fontSize: "1.2rem", color: "#38bdf8" }}>{s.symbol}</h4>
                      <span style={{ padding: "4px 8px", background: s.opportunity ? "#166534" : "#374151", borderRadius: 4, fontSize: "0.8rem", color: "#fff" }}>
                        {s.opportunity ? "OPPORTUNITY IDENTIFIED" : "NO ELEVATED IV"}
                      </span>
                    </div>

                    {s.iv_metrics && (
                      <div className="figures" style={{ marginTop: 10 }}>
                        <Figure label="Stock Price" value={`$${s.iv_metrics.stock_price?.toFixed(2)}`} />
                        <Figure label="Current IV" value={`${(s.iv_metrics.current_iv * 100)?.toFixed(1)}%`} />
                        <Figure label="IV Rank" value={`${s.iv_metrics.iv_rank?.toFixed(1)}%`} hint={s.iv_metrics.iv_rank >= minIvRank ? "Elevated" : "Normal"} />
                      </div>
                    )}

                    {s.best_candidate && (
                      <div style={{ marginTop: 14, padding: 12, background: "rgba(255,255,255,0.03)", borderRadius: 6 }}>
                        <div style={{ fontWeight: 600, color: "#4ade80", marginBottom: 6 }}>
                          Setup: {s.best_candidate.setup_type?.replace(/_/g, " ").toUpperCase()} (Exp: {s.best_candidate.expiration})
                        </div>
                        <div style={{ fontSize: "0.9rem", color: "var(--muted)" }}>
                          Short Strike: <strong>${s.best_candidate.short_strike}</strong> ({s.best_candidate.short_symbol}) | 
                          Long Strike: <strong>${s.best_candidate.long_strike}</strong> ({s.best_candidate.long_symbol})
                        </div>
                        <div style={{ fontSize: "0.9rem", marginTop: 4 }}>
                          Credit: <strong>${s.best_candidate.estimated_credit}</strong> | Max Loss: <strong>${s.best_candidate.max_loss}</strong> | Win Rate: <strong>{(s.best_candidate.win_rate_target * 100)?.toFixed(0)}%</strong>
                        </div>
                      </div>
                    )}

                    {s.proposal && (
                      <div style={{ marginTop: 12, padding: 12, background: "rgba(30, 41, 59, 0.5)", borderRadius: 6, borderLeft: "4px solid #38bdf8" }}>
                        <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "#38bdf8", marginBottom: 4 }}>
                          🧠 Featherless AI Strategic Reasoning:
                        </div>
                        <p style={{ margin: 0, fontSize: "0.9rem", lineHeight: 1.5 }}>{s.proposal.reasoning}</p>
                      </div>
                    )}

                    {s.validation && (
                      <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
                        {s.validation.gates?.map((g: any) => (
                          <span 
                            key={g.gate} 
                            style={{ 
                              padding: "3px 8px", 
                              borderRadius: 4, 
                              fontSize: "0.75rem", 
                              background: g.status === "PASS" ? "rgba(34, 197, 94, 0.2)" : "rgba(239, 68, 68, 0.2)",
                              color: g.status === "PASS" ? "#4ade80" : "#f87171",
                              border: `1px solid ${g.status === "PASS" ? "rgba(34, 197, 94, 0.4)" : "rgba(239, 68, 68, 0.4)"}`
                            }}
                          >
                            {g.gate}: {g.status}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {mode === "equity" && (
        <form onSubmit={submit}>
          <div className="field">
            <label>What do you want to trade?</label>
            <textarea
              placeholder="I want to buy $1,000 of NVDA."
              value={text}
              onChange={(e) => setText(e.target.value)}
              required
            />
          </div>
          <div className="grid cols-2">
            <div className="field">
              <label>Stop, where you are wrong</label>
              <input value={stop} onChange={(e) => setStop(e.target.value)} placeholder="Optional" />
            </div>
            <div className="field">
              <label>Target, where you take profit</label>
              <input value={target} onChange={(e) => setTarget(e.target.value)} placeholder="Optional" />
            </div>
          </div>
          <label className="check">
            <input type="checkbox" checked={proposeStop} onChange={(e) => setProposeStop(e.target.checked)} />
            If I leave the stop blank, suggest one from recent price and mark it as a suggestion.
          </label>
          <div style={{ height: 16 }} />
          <button className="btn primary" disabled={loading}>{loading ? "Analyzing…" : "Analyze this trade"}</button>
        </form>
      )}

      {error && <p className="error">{error}</p>}


      {result && (
        <article>
          <header className="verdict-hero">
            <div className="q">Verdict</div>
            <Stamp verdict={verdict} large />
            <h2>
              {verdict === "BUY" && "This idea is acceptable on the data we have."}
              {verdict === "WAIT" && "Do not enter at this price."}
              {verdict === "REDUCE" && "The idea may be fine. The size is not."}
              {verdict === "REJECT" && "Do not take this trade."}
              {verdict === "INCOMPLETE" && "The verdict cannot be completed with the data we have."}
            </h2>
            <p className="why">{primaryWhy}</p>
            {verdict === "WAIT" && nextCondition && (
              <p className="muted">What would change this: {nextCondition}</p>
            )}
            {verdict === "INCOMPLETE" && nextCondition && (
              <p className="muted">What would complete this: {nextCondition}</p>
            )}
            {verdict === "REDUCE" && decision?.suggested_notional && (
              <p className="muted">Largest size that fits your rules: {money(decision.suggested_notional)}</p>
            )}
            {verdict !== "REJECT" && verdict !== "INCOMPLETE" && !preview && !execution && (
              result.broker_connected ? (
                <button className="btn primary" onClick={previewOrder}>Review trade</button>
              ) : (
                <p className="muted">
                  Connect a brokerage when you want this checked against your real portfolio, or to send the order.{" "}
                  <Link to="/app/settings/broker">Connect brokerage</Link>
                </p>
              )
            )}
          </header>

          <section className="section-q">
            <h3>What you asked</h3>
            <p className="ask">The idea REGRET evaluated</p>
            <p className="idea-line">{ideaLine(intent, text)}</p>
            {(intent?.stop_price || intent?.target_price) && (
              <p className="muted">
                {intent.stop_price ? `Stop ${num(intent.stop_price)}` : "No stop given"}
                {intent.target_price ? ` · Target ${num(intent.target_price)}` : ""}
              </p>
            )}
          </section>

          <section className="section-q">
            <h3>Market</h3>
            <p className="ask">What is actually happening, only from retrieved data</p>
            <dl className="kv">
              <div><dt>Symbol</dt><dd className="mono">{marketData?.symbol || intent?.symbol || "n/a"}</dd></div>
              <div><dt>Asset type</dt><dd>{marketData?.asset_type || "n/a"}</dd></div>
              <div><dt>Available</dt><dd>{marketData?.available || market?.available ? "Yes" : "No"}</dd></div>
              <div><dt>Source</dt><dd className="mono">{marketData?.source || result?.market_source || "n/a"}</dd></div>
              <div><dt>Timestamp</dt><dd className="mono">{when(marketData?.timestamp || result?.data_timestamp)}</dd></div>
              <div><dt>Freshness</dt><dd>{marketData?.current === false || result?.freshness?.ok === false ? "Not current" : marketData?.live ? "Current" : result?.freshness?.message || "n/a"}</dd></div>
            </dl>
            {!market?.available && (
              <Empty>{market?.unavailable_reason || marketData?.unavailable_reason || "Market data is unavailable. The analysis cannot describe a live tape."}</Empty>
            )}
            {result?.freshness?.ok === false && (
              <Empty>{result.freshness.message}</Empty>
            )}
            {market?.available && (
              <dl className="kv">
                <div><dt>Trend</dt><dd>{market.trend || "n/a"}</dd></div>
                <div><dt>Momentum</dt><dd>{market.momentum || "n/a"}</dd></div>
                <div><dt>How wild the price is</dt><dd>{market.volatility || "n/a"}</dd></div>
                <div><dt>Where price sits</dt><dd>{market.price_location || "n/a"}</dd></div>
                <div><dt>Last price used</dt><dd className="mono">{num(market.last_close)}</dd></div>
                <div><dt>Today’s move</dt><dd className="mono">{market.daily_change_pct != null ? `${num(market.daily_change_pct)}%` : "n/a"}</dd></div>
              </dl>
            )}
          </section>

          <section className="section-q">
            <h3>Setup</h3>
            <p className="ask">Does the requested trade have the required setup?</p>
            {!market?.available ? (
              <Empty>{market?.unavailable_reason || "Setup cannot be judged because market data is unavailable."}</Empty>
            ) : (
              <dl className="kv">
                <div><dt>Trend</dt><dd>{setup?.trend || "n/a"}</dd></div>
                <div><dt>Momentum</dt><dd>{setup?.momentum || "n/a"}</dd></div>
                <div><dt>Location</dt><dd>{setup?.location || "n/a"}</dd></div>
                <div><dt>Risk / reward</dt><dd className="mono">{setup?.risk_reward ?? "n/a"}</dd></div>
                <div><dt>Invalidation</dt><dd className="mono">{setup?.invalidation ?? "n/a"}</dd></div>
                <div><dt>Target</dt><dd className="mono">{setup?.target ?? "n/a"}</dd></div>
              </dl>
            )}
            {(setup?.notes || []).length > 0 && (
              <p className="muted">{setup.notes.filter(Boolean).join(" ")}</p>
            )}
          </section>

          <section className="section-q">
            <h3>Rules</h3>
            <p className="ask">Deterministic checks. The model does not decide pass or fail.</p>
            {rules.length === 0 && (
              <Empty>
                You have not written any rules yet. REGRET still analyzed the idea.{" "}
                <Link to="/app/rules">Add rules</Link>
              </Empty>
            )}
            {rules.length > 0 && (
              <div className="table-wrap">
                <table className="table">
                  <thead><tr><th>Rule</th><th>Result</th><th>Actual</th><th>Required</th><th>Difference</th></tr></thead>
                  <tbody>
                    {rules.map((r: any) => (
                      <tr key={r.rule_id}>
                        <td>
                          {r.name}
                          <div className="faint">{r.reason || r.message}</div>
                        </td>
                        <td className={RuleTone(r.status)}>
                          {r.result || (r.status === "PASS" ? "PASS" : r.status === "FAIL" ? "FAILED" : r.status === "WARNING" ? "WARNING" : "INSUFFICIENT DATA")}
                        </td>
                        <td className="num">{r.actual ?? "n/a"}</td>
                        <td className="num">{r.required ?? r.threshold ?? "n/a"}</td>
                        <td className="num">{r.difference ?? "n/a"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="section-q">
            <h3>Portfolio</h3>
            <p className="ask">What happens to the actual book if this trade is taken</p>
            {portfolio?.available === false ? (
              <Empty>{portfolio.reason || "Portfolio check unavailable because no brokerage is connected."}</Empty>
            ) : (
              <dl className="kv">
                <div><dt>Account value</dt><dd className="mono">{money(portfolio?.equity)}</dd></div>
                <div><dt>Buying power</dt><dd className="mono">{money(portfolio?.buying_power)}</dd></div>
                <div><dt>This name now</dt><dd className="mono">{money(portfolio?.current_exposure)}</dd></div>
                <div><dt>This name after</dt><dd className="mono">{money(portfolio?.after_trade)}</dd></div>
                <div><dt>Share of account after</dt><dd className="mono">{portfolio?.portfolio_percentage_after != null ? `${num(portfolio.portfolio_percentage_after)}%` : "n/a"}</dd></div>
                <div><dt>Concentration after</dt><dd className="mono">{risk?.concentration_pct != null ? `${num(risk.concentration_pct)}%` : "n/a"}</dd></div>
              </dl>
            )}
          </section>

          <section className="section-q">
            <h3>Risk</h3>
            <p className="ask">Calculated from retrieved inputs only. Missing inputs are not guessed.</p>
            {risk?.available === false ? (
              <Empty>{risk?.unavailable_reason || "INSUFFICIENT DATA"}</Empty>
            ) : (
              <dl className="kv">
                <div><dt>Entry used</dt><dd className="mono">{num(risk?.entry_price)}</dd></div>
                <div><dt>Size</dt><dd className="mono">{intent?.notional ? money(risk?.notional) : num(risk?.quantity, 6)}</dd></div>
                <div><dt>Money at risk</dt><dd className="mono">{risk?.risk_dollars == null ? "INSUFFICIENT DATA" : money(risk.risk_dollars)}</dd></div>
                <div><dt>Of the account</dt><dd className="mono">{risk?.risk_percentage != null ? `${num(risk.risk_percentage)}%` : "INSUFFICIENT DATA"}</dd></div>
                <div><dt>Reward vs risk</dt><dd className="mono">{risk?.risk_reward ?? "n/a"}</dd></div>
                {risk?.stop_was_proposed && <div><dt>Stop used</dt><dd>Suggested from recent lows · {num(risk.stop_used)}</dd></div>}
              </dl>
            )}
            {risk?.available !== false && risk?.unavailable_reason && (
              <p className="muted">{risk.unavailable_reason}</p>
            )}
          </section>

          <section className="section-q">
            <h3>Why not enter</h3>
            <p className="ask">Structured reasons from the engines, not a model paragraph</p>
            {why.length === 0 && <Empty>No extra objections beyond the verdict above.</Empty>}
            {why.length > 0 && (
              <ol style={{ margin: 0, paddingLeft: 18 }}>
                {why.map((item: any, i: number) => (
                  <li key={i} style={{ marginBottom: 12 }}>
                    <strong>{item.title || item.code}</strong>
                    <div>{item.message}</div>
                    {(item.actual != null || item.required != null) && (
                      <div className="faint">
                        Actual {item.actual ?? "n/a"}
                        {item.required != null ? ` · Required ${item.required}` : ""}
                        {item.difference != null ? ` · Difference ${item.difference}` : ""}
                      </div>
                    )}
                  </li>
                ))}
              </ol>
            )}
          </section>

          {result.order_proposal && (
            <section className="section-q">
              <h3>Order review</h3>
              <p className="ask">A proposal only. Nothing has been sent.</p>
              {!result.order_proposal.allowed ? (
                <Empty>{result.order_proposal.reason || "This verdict cannot become an order."}</Empty>
              ) : (
                <dl className="kv">
                  <div><dt>Symbol</dt><dd className="mono">{result.order_proposal.symbol}</dd></div>
                  <div><dt>Side</dt><dd>{result.order_proposal.side}</dd></div>
                  <div><dt>Quantity</dt><dd className="mono">{result.order_proposal.quantity ?? "n/a"}</dd></div>
                  <div><dt>Order type</dt><dd>{result.order_proposal.order_type}</dd></div>
                  <div><dt>Estimated notional</dt><dd className="mono">{money(result.order_proposal.estimated_notional)}</dd></div>
                  <div><dt>Entry basis</dt><dd>{result.order_proposal.entry_basis || "n/a"}</dd></div>
                  <div><dt>Risk</dt><dd className="mono">{result.order_proposal.risk != null ? money(result.order_proposal.risk) : "INSUFFICIENT DATA"}</dd></div>
                  <div><dt>Exposure after</dt><dd className="mono">{result.order_proposal.portfolio_exposure_after != null ? `${num(result.order_proposal.portfolio_exposure_after)}%` : "n/a"}</dd></div>
                  <div><dt>Rules</dt><dd>{result.order_proposal.rules}</dd></div>
                  <div><dt>Risk checks</dt><dd>{result.order_proposal.risk_checks}</dd></div>
                </dl>
              )}
            </section>
          )}

          {result.ai_explanation && (
            <section className="section-q">
              <h3>In plain language</h3>
              <p className="ask">An explanation of the numbers above, not a new source of facts</p>
              <p>{result.ai_explanation}</p>
            </section>
          )}

          {verdict !== "REJECT" && verdict !== "INCOMPLETE" && !preview && !execution && (
            <div className="cta-bar">
              {result.broker_connected ? (
                <>
                  <p>A BUY or WAIT verdict is not an order. Review the trade before anything is sent.</p>
                  <button className="btn primary" onClick={previewOrder}>Review trade</button>
                </>
              ) : (
                <p className="muted">
                  You can keep using REGRET without a brokerage. Connect one only when you want the real book included, or to send the order.{" "}
                  <Link to="/app/settings/broker">Connect brokerage</Link>
                </p>
              )}
            </div>
          )}
        </article>
      )}

      {preview && !execution && (
        <section className="cta-bar">
          <div className="q" style={{ fontFamily: "var(--mono)", letterSpacing: "0.16em", textTransform: "uppercase", fontSize: 11, color: "var(--oxblood)" }}>Review this trade</div>
          <h2>Nothing has been sent yet.</h2>
          <p className="muted">Confirming will send this order to your connected brokerage. REGRET will not send it unless you say so.</p>
          <dl className="kv">
            <div><dt>Trade</dt><dd className="mono">{preview.preview?.side} {preview.preview?.symbol} {preview.preview?.amount_notional ? money(preview.preview.amount_notional) : preview.preview?.quantity}</dd></div>
            <div><dt>Order type</dt><dd>{preview.preview?.order_type}</dd></div>
            <div><dt>Account</dt><dd>{preview.preview?.environment === "live" ? "Live" : "Paper"}</dd></div>
            <div><dt>Verdict</dt><dd><Stamp verdict={preview.preview?.verdict} /></dd></div>
            <div><dt>Review expires</dt><dd>{when(preview.expires_at)}</dd></div>
          </dl>
          <div className="actions" style={{ marginTop: 16 }}>
            <button className="btn ghost" onClick={() => setPreview(null)}>Do not send</button>
            <button className="btn primary" onClick={() => execute(false)}>Send this order</button>
            {preview.preview?.suggested_notional && (
              <button className="btn" onClick={() => execute(true)}>
                Send the smaller size ({money(preview.preview.suggested_notional)})
              </button>
            )}
          </div>
        </section>
      )}

      {execution && (
        <section className="cta-bar">
          <h2>Order sent.</h2>
          <p className="muted">The status below is what the brokerage returned. Sent is not the same as filled.</p>
          <dl className="kv">
            <div><dt>Brokerage order</dt><dd className="mono">{execution.order?.alpaca_order_id || "n/a"}</dd></div>
            <div><dt>Brokerage status</dt><dd>{execution.order?.alpaca_status || execution.order?.status || execution.status}</dd></div>
            <div><dt>Filled</dt><dd>{execution.executed || execution.order?.filled ? "Yes" : "No. Submitted is not filled"}</dd></div>
            <div><dt>Account</dt><dd>{execution.environment === "live" ? "Live" : "Paper"}</dd></div>
            <div><dt>Filled quantity</dt><dd className="mono">{execution.order?.filled_qty ?? "n/a"}</dd></div>
            <div><dt>Average price</dt><dd className="mono">{execution.order?.filled_avg_price ?? "n/a"}</dd></div>
            {execution.override && <div><dt>Note</dt><dd>You sent this after a WAIT or REDUCE verdict.</dd></div>}
          </dl>
          <div className="actions" style={{ marginTop: 16 }}>
            {intent?.symbol && <Link className="btn primary" to={`/app/monitor/${intent.symbol}`}>Watch this trade</Link>}
            <Link className="btn" to="/app/journal">Open the journal</Link>
          </div>
        </section>
      )}
    </div>
  );
}
