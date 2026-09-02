import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, api } from "../api";
import { Empty, PageHead } from "../components/ui";
import { money } from "../lib/format";

export default function Monitor() {
  const { symbol } = useParams();
  const [data, setData] = useState<any>(null);
  const [book, setBook] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/api/monitor").then(setBook).catch(() => setBook(null));
    if (!symbol) return;
    api.get(`/api/monitor/${symbol}`)
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "This trade cannot be watched right now."));
  }, [symbol]);

  return (
    <div className="stack">
      <PageHead
        kicker="Watch"
        title={symbol ? symbol.toUpperCase() : "Orders"}
        lead="Open and submitted orders as the brokerage reports them. Submitted is not filled."
      />
      {book && (
        <section className="sheet">
          <h3>Brokerage orders</h3>
          {!book.available && <Empty>{book.reason}</Empty>}
          {book.available && (
            <dl className="kv">
              <div><dt>Open</dt><dd>{book.open?.length ?? 0}</dd></div>
              <div><dt>Pending</dt><dd>{book.pending?.length ?? 0}</dd></div>
              <div><dt>Filled</dt><dd>{book.filled?.length ?? 0}</dd></div>
              <div><dt>Cancelled</dt><dd>{book.cancelled?.length ?? 0}</dd></div>
              <div><dt>Rejected</dt><dd>{book.rejected?.length ?? 0}</dd></div>
            </dl>
          )}
        </section>
      )}
      {error && (
        <section className="sheet">
          <Empty>{error}</Empty>
          <p className="muted">You can still read past decisions in the journal.</p>
          <Link className="btn" to="/app/journal">Open the journal</Link>
        </section>
      )}
      {data && !data.available && (
        <section className="sheet">
          <Empty>{data.message || "Live data for this thesis is unavailable."}</Empty>
        </section>
      )}
      {data?.available && (
        <section>
          <dl className="kv">
            <div><dt>Current price</dt><dd className="mono">{data.review?.current_price ?? "n/a"}</dd></div>
            <div><dt>Entry</dt><dd className="mono">{data.thesis?.entry ?? "n/a"}</dd></div>
            <div><dt>Stop</dt><dd className="mono">{data.thesis?.invalidation ?? "n/a"}</dd></div>
            <div><dt>Target</dt><dd className="mono">{data.thesis?.target ?? "n/a"}</dd></div>
            <div><dt>Open P/L</dt><dd className="mono">{data.review?.unrealized_pl != null ? money(data.review.unrealized_pl) : "n/a"}</dd></div>
            <div><dt>State</dt><dd>{data.review?.state || data.thesis?.state || "n/a"}</dd></div>
          </dl>
          {(data.review?.reasons || []).map((r: string) => <p key={r}>{r}</p>)}
          {data.review?.position == null && (
            <Empty>There is no open position in this name on the connected account.</Empty>
          )}
        </section>
      )}
    </div>
  );
}
