import { FormEvent, useEffect, useState } from "react";
import { ApiError, api } from "../api";
import { Empty, PageHead, Stamp } from "../components/ui";

export default function Setups() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [symbol, setSymbol] = useState("");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [scanning, setScanning] = useState(false);

  async function load() {
    setSymbols((await api.get<{ symbols: string[] }>("/api/watchlist")).symbols);
  }
  useEffect(() => { load().catch((err) => setError(err.message)); }, []);

  async function add(event: FormEvent) {
    event.preventDefault();
    setSymbols((await api.post<{ symbols: string[] }>("/api/watchlist", { symbol })).symbols);
    setSymbol("");
  }

  async function scan() {
    setError("");
    setScanning(true);
    try {
      setResult(await api.post("/api/setups", { notional: "1000", side: "buy" }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Scan failed.");
    } finally {
      setScanning(false);
    }
  }

  return (
    <div className="stack">
      <PageHead
        kicker="Setups"
        title="Only what is on the list."
        lead="Add symbols you care about. REGRET reviews them with the same engine as Analyze. A brokerage is only needed if you want portfolio impact in those reviews."
      />
      {error && <p className="error">{error}</p>}

      <section className="sheet">
        <div className="sheet-head"><h3>Watchlist</h3></div>
        {symbols.length === 0 && <Empty>No universe is selected. Add symbols before scanning.</Empty>}
        <div className="row" style={{ marginBottom: 14 }}>
          {symbols.map((s) => <span key={s} className="chip">{s}</span>)}
        </div>
        <form className="row" onSubmit={add}>
          <input value={symbol} onChange={(e) => setSymbol(e.target.value)} placeholder="AAPL" style={{ maxWidth: 160 }} />
          <button className="btn">Add</button>
          <button className="btn primary" type="button" onClick={scan} disabled={scanning}>
            {scanning ? "Reading the tape…" : "Scan the list"}
          </button>
        </form>
      </section>

      {result && (
        <section className="sheet">
          <div className="sheet-head"><h3>Reading</h3></div>
          {result.message && <p className="muted">{result.message}</p>}
          {(result.setups || []).length === 0 && <Empty>No setup currently matches your rules.</Empty>}
          {(result.setups || []).map((s: any) => (
            <div key={s.analysis_id} className="row" style={{ justifyContent: "space-between", padding: "12px 0", borderBottom: "1px dashed var(--rule)" }}>
              <div>
                <strong className="mono">{s.symbol}</strong>
                <div className="muted">{s.summary}</div>
              </div>
              <Stamp verdict={s.verdict} />
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
