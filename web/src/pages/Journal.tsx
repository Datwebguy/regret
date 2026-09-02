import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Empty, PageHead, Stamp } from "../components/ui";
import { money, num, when } from "../lib/format";

export default function Journal() {
  const [entries, setEntries] = useState<any[] | null>(null);
  const [insights, setInsights] = useState<any>(null);
  const [open, setOpen] = useState<any>(null);

  useEffect(() => {
    api.get<{ entries: any[] }>("/api/journal").then((r) => setEntries(r.entries));
    api.get("/api/insights").then(setInsights);
  }, []);

  async function openEntry(id: string) {
    setOpen(await api.get(`/api/journal/${id}`));
  }

  return (
    <div className="stack">
      <PageHead
        kicker="Journal"
        title="What you actually did"
        lead="Every analysis and every sent order is recorded. Thinking about a trade is not the same as sending one."
      />

      <section>
        <h3>What the record shows</h3>
        {!insights && <p className="muted">Loading…</p>}
        {insights && !insights.available && (
          <Empty>{insights.message} Analyze more trades, or send one, before expecting a pattern.</Empty>
        )}
        {insights?.insights?.map((line: string) => <p key={line}>{line}</p>)}
      </section>

      <section>
        <h3>History</h3>
        {entries && entries.length === 0 && (
          <Empty>Nothing here yet. Start with an idea on Analyze.</Empty>
        )}
        {entries && entries.length > 0 && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>When</th>
                  <th>What</th>
                  <th>Name</th>
                  <th>Verdict</th>
                  <th>You did</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {entries.map((e) => (
                  <tr key={e.id}>
                    <td className="faint">{when(e.created_at)}</td>
                    <td>{e.entry_type === "execution" ? "Order sent" : e.entry_type === "analysis" ? "Analysis" : e.entry_type}</td>
                    <td className="mono">{e.symbol || "n/a"}</td>
                    <td>{e.verdict ? <Stamp verdict={e.verdict} /> : "n/a"}</td>
                    <td>{e.user_action === "executed" ? "Sent" : e.user_action === "analyzed" ? "Asked" : e.user_action || "n/a"}</td>
                    <td>
                      <button className="btn" onClick={() => openEntry(e.id)}>Open</button>
                      {e.symbol && e.entry_type === "execution" && (
                        <Link to={`/app/monitor/${e.symbol}`}>Watch</Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {open && (
        <section className="sheet">
          <div className="sheet-head">
            <h3>Record {when(open.created_at)}</h3>
            <button className="btn" onClick={() => setOpen(null)}>Close</button>
          </div>
          <p>{open.summary}</p>
          <dl className="kv">
            <div><dt>Verdict</dt><dd><Stamp verdict={open.verdict} /></dd></div>
            <div><dt>Idea</dt><dd>{typeof open.snapshot?.idea === "string" ? open.snapshot.idea : open.symbol}</dd></div>
            <div><dt>Data used</dt><dd>{when(open.snapshot?.data_timestamp)}</dd></div>
            <div><dt>Alpaca order</dt><dd className="mono">{open.alpaca_order_id || "n/a"}</dd></div>
            <div><dt>Outcome</dt><dd>{open.outcome || "n/a"}</dd></div>
          </dl>
          {open.snapshot?.why_not?.items?.length > 0 && (
            <ol>
              {open.snapshot.why_not.items.map((item: any, i: number) => (
                <li key={i}>{item.title}: {item.message}</li>
              ))}
            </ol>
          )}
          {open.snapshot?.order_proposal?.allowed && (
            <p className="muted">
              Proposal {open.snapshot.order_proposal.side} {open.snapshot.order_proposal.symbol}
              {" "}{open.snapshot.order_proposal.estimated_notional ? money(open.snapshot.order_proposal.estimated_notional) : ""}
              {" · "}rules {open.snapshot.order_proposal.rules}
            </p>
          )}
          {open.snapshot?.risk && (
            <p className="muted">
              Risk {open.snapshot.risk.risk_dollars != null ? money(open.snapshot.risk.risk_dollars) : "unavailable"}
              {open.snapshot.risk.risk_percentage != null ? ` (${num(open.snapshot.risk.risk_percentage)}%)` : ""}
            </p>
          )}
        </section>
      )}
    </div>
  );
}
