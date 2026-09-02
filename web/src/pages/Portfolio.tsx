import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, api } from "../api";
import { Empty, Figure, PageHead } from "../components/ui";
import { money, num } from "../lib/format";

export default function Portfolio() {
  const [data, setData] = useState<any>(null);
  const [orders, setOrders] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/api/portfolio")
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Unavailable"));
    api.get("/api/broker-orders")
      .then((r: any) => setOrders(r.orders || []))
      .catch(() => setOrders([]));
  }, []);

  if (error) {
    return (
      <div className="stack">
        <PageHead kicker="Portfolio" title="Your book." />
        <div className="notice">{error}</div>
      </div>
    );
  }
  if (!data) return <p className="empty">Loading…</p>;

  if (!data.connected) {
    return (
      <div className="stack">
        <PageHead
          kicker="Portfolio"
          title="Your portfolio"
          lead="This page shows live brokerage data. You can still analyze a trade without it."
        />
        <section className="sheet">
          <h3>Your portfolio is not connected yet.</h3>
          <Empty>{data.reason || "Portfolio check unavailable because no brokerage is connected."}</Empty>
          <Link className="btn primary" to="/app/settings/broker">Connect brokerage</Link>
        </section>
      </div>
    );
  }

  return (
    <div className="stack">
      <PageHead
        kicker={data.environment}
        title="Your portfolio"
        lead="Positions and open orders as your brokerage reports them right now."
      />
      <div className="figures">
        <Figure label="Equity" value={money(data.account?.equity)} />
        <Figure label="Cash" value={money(data.account?.cash)} />
        <Figure label="Buying power" value={money(data.account?.buying_power)} />
        <Figure label="Portfolio value" value={money(data.account?.portfolio_value)} />
      </div>
      <p className="muted">
        Status {data.account?.status || "n/a"}
        {" · "}
        Trading {data.account?.trading_status || "n/a"}
        {" · "}
        {data.account?.currency || "currency unavailable"}
        {" · "}
        Source {data.source || "alpaca"}
      </p>
      <section className="sheet">
        <div className="sheet-head"><h3>Positions</h3></div>
        {data.positions.length === 0 && <Empty>No positions.</Empty>}
        {data.positions.length > 0 && (
          <table className="table">
            <thead>
              <tr><th>Symbol</th><th>Qty</th><th>Side</th><th>Avg</th><th>Price</th><th>Value</th><th>Unrealized</th><th>Exposure</th></tr>
            </thead>
            <tbody>
              {data.positions.map((p: any) => (
                <tr key={p.symbol}>
                  <td className="mono">{p.symbol}</td>
                  <td className="num">{num(p.qty, 4)}</td>
                  <td>{p.side || "n/a"}</td>
                  <td className="num">{money(p.avg_entry_price)}</td>
                  <td className="num">{money(p.current_price)}</td>
                  <td className="num">{money(p.market_value)}</td>
                  <td className="num">{money(p.unrealized_pl)}</td>
                  <td className="num">{p.exposure_pct != null ? `${num(p.exposure_pct)}%` : "n/a"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
      <section className="sheet">
        <div className="sheet-head"><h3>Open orders</h3></div>
        {orders.length === 0 && <Empty>No open orders.</Empty>}
        {orders.length > 0 && (
          <table className="table">
            <thead><tr><th>ID</th><th>Symbol</th><th>Side</th><th>Status</th></tr></thead>
            <tbody>
              {orders.map((o: any) => (
                <tr key={o.id}>
                  <td className="mono">{o.id}</td>
                  <td className="mono">{o.symbol}</td>
                  <td>{o.side}</td>
                  <td>{o.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
