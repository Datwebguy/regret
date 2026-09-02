import { FormEvent, useEffect, useState } from "react";
import { NavLink, useParams, useSearchParams } from "react-router-dom";
import { ApiError, api } from "../api";
import { Empty, PageHead } from "../components/ui";
import { ALPACA_DISCLOSURE_BODY, ALPACA_DISCLOSURE_TITLE } from "../lib/alpacaDisclosure";

export default function Settings() {
  const { section } = useParams();
  const tab = section || "account";
  return (
    <div className="stack">
      <PageHead
        kicker="Settings"
        title="Your account."
        lead="REGRET is your decision product. A brokerage is an optional connection that unlocks your live book and execution."
      />
      <nav className="tabs">
        <NavLink to="/app/settings/account" className={tab === "account" ? "active" : ""}>Account</NavLink>
        <NavLink to="/app/settings/broker" className={tab === "broker" ? "active" : ""}>Broker</NavLink>
        <NavLink to="/app/settings/preferences" className={tab === "preferences" ? "active" : ""}>Preferences</NavLink>
      </nav>
      {tab === "broker" ? <BrokerPanel /> : tab === "preferences" ? <PrefsPanel /> : <AccountPanel />}
    </div>
  );
}

function AccountPanel() {
  const [prefs, setPrefs] = useState<any>(null);
  useEffect(() => {
    api.get("/api/preferences").then(setPrefs).catch(() => setPrefs(null));
  }, []);
  if (!prefs) return <p className="muted">Loading…</p>;
  return (
    <section className="sheet">
      <div className="sheet-head"><h3>REGRET account</h3></div>
      <dl className="kv">
        <div><dt>Email</dt><dd>{prefs.email}</dd></div>
        <div><dt>Name</dt><dd>{prefs.display_name || "n/a"}</dd></div>
      </dl>
      <p className="muted" style={{ marginTop: 16 }}>
        This account is not a brokerage account. Connecting Alpaca later does not replace it.
        {" "}
        <a href="/terms">Terms of Use</a>
        {" · "}
        <a href="/privacy">Privacy Policy</a>
      </p>
    </section>
  );
}

function PrefsPanel() {
  const [prefs, setPrefs] = useState<any>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api.get("/api/preferences").then(setPrefs).catch((err) => setError(err.message));
  }, []);

  async function save(patch: Record<string, unknown>) {
    setError("");
    try {
      setPrefs(await api.patch("/api/preferences", patch));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to save.");
    }
  }

  if (!prefs) return <p className="muted">Loading…</p>;
  return (
    <section className="sheet">
      <div className="sheet-head"><h3>Preferences</h3></div>
      {error && <p className="error">{error}</p>}
      <div className="field">
        <label>Default brokerage environment</label>
        <select
          value={prefs.default_environment === "live" && !prefs.live_trading_enabled ? "paper" : prefs.default_environment}
          onChange={(e) => save({ default_environment: e.target.value })}
        >
          <option value="paper">Paper</option>
          {prefs.live_trading_enabled && <option value="live">Live</option>}
        </select>
      </div>
      <label className="check">
        <input
          type="checkbox"
          checked={prefs.monitoring_enabled}
          onChange={(e) => save({ monitoring_enabled: e.target.checked })}
        />
        Watch open theses after a trade is sent
      </label>
    </section>
  );
}

function BrokerPanel() {
  const [status, setStatus] = useState<any>(null);
  const [error, setError] = useState("");
  const [advanced, setAdvanced] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [keys, setKeys] = useState({ environment: "paper", api_key_id: "", api_secret: "" });
  const [params] = useSearchParams();
  const oauthNote = {
    denied: "Alpaca did not grant access. Nothing was connected.",
    invalid: "That connection request was not valid or had expired. Start again.",
    failed: "Alpaca could not complete the connection. Nothing was stored.",
    connected: "Brokerage connected.",
  }[params.get("alpaca") || ""];

  async function load() {
    setStatus(await api.get("/api/alpaca/status"));
  }
  useEffect(() => { load().catch((err) => setError(err.message)); }, []);

  async function startOauth(purpose: "read" | "trade") {
    setError("");
    const environment = status?.live_trading_enabled ? keys.environment : "paper";
    try {
      const data = await api.post<{ authorization_url: string }>(
        `/api/alpaca/oauth/start?environment=${environment}&purpose=${purpose}`
      );
      window.location.href = data.authorization_url;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Brokerage connection is currently unavailable.");
    }
  }

  async function connectKeys(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api.post("/api/alpaca/keys", keys);
      setKeys({ ...keys, api_key_id: "", api_secret: "" });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Connection failed.");
    }
  }

  async function disconnect() {
    await api.del(`/api/alpaca/connection?environment=${status?.active?.environment || keys.environment}`);
    await load();
  }

  return (
    <div className="stack">
      {error && <p className="error">{error}</p>}
      {oauthNote && <p className={params.get("alpaca") === "connected" ? "muted" : "error"}>{oauthNote}</p>}
      <section className="sheet">
        <div className="sheet-head"><h3>Connect your brokerage</h3></div>
        <p>
          Connect an existing Alpaca account. REGRET does not open a brokerage account
          for you. You authorize REGRET through Alpaca, then REGRET can read that
          account and send paper orders you explicitly approve.
        </p>
        <p className="muted">The first connection is paper. Live is not enabled on this deployment.</p>
        <aside className="disclosure" aria-label="Alpaca authorization disclosure">
          <h3>{ALPACA_DISCLOSURE_TITLE}</h3>
          {ALPACA_DISCLOSURE_BODY.map((line) => (
            <p key={line}>{line}</p>
          ))}
          <p>
            <a href="/terms">Learn more about REGRET</a>
            {" · "}
            <a href="/privacy">Privacy Policy</a>
          </p>
          {status?.connect_available && !status?.active && confirming && (
            <div className="actions" style={{ marginTop: 14 }}>
              <button className="btn danger" type="button" onClick={() => setConfirming(false)}>Deny</button>
              <button className="btn primary" type="button" onClick={() => startOauth("trade")}>Allow</button>
            </div>
          )}
        </aside>

        {status?.active ? (
          <dl className="kv">
            <div><dt>Connection</dt><dd>Connected</dd></div>
            <div><dt>Status</dt><dd>{status.reachable === false ? "Saved, but Alpaca did not respond" : "Reachable"}</dd></div>
            <div><dt>Environment</dt><dd>{status.active.environment === "live" ? "Live" : "Paper"}</dd></div>
            <div><dt>Analyze</dt><dd>Available</dd></div>
            <div><dt>Portfolio</dt><dd>{status.capabilities?.portfolio ? "Available" : "Unavailable"}</dd></div>
            <div><dt>Orders</dt><dd>{status.capabilities?.trading ? "Paper orders allowed" : "Read only"}</dd></div>
            <div><dt>Live</dt><dd>{status.capabilities?.live ? "Enabled on this deployment" : "Disabled"}</dd></div>
            <div><dt>Account</dt><dd className="mono">{status.active.alpaca_account_number || status.active.alpaca_account_id}</dd></div>
          </dl>
        ) : (
          <Empty>Not connected.</Empty>
        )}

        {status?.live_trading_enabled && (
          <div className="field" style={{ marginTop: 16, maxWidth: 240 }}>
            <label>Environment</label>
            <select value={keys.environment} onChange={(e) => setKeys({ ...keys, environment: e.target.value })}>
              <option value="paper">Paper</option>
              <option value="live">Live</option>
            </select>
          </div>
        )}

        {status?.connect_available && !status?.active && !confirming ? (
          <div className="actions" style={{ marginTop: 16 }}>
            <button className="btn primary" type="button" onClick={() => setConfirming(true)}>Connect Alpaca</button>
          </div>
        ) : status?.connect_available ? null : (
          !status?.active && (
            <div className="notice">
              Brokerage connection is currently unavailable. You can still analyze trades, write rules, and keep a journal.
            </div>
          )
        )}

        {status?.active && (
          <div style={{ marginTop: 14 }}>
            <button className="btn danger" onClick={disconnect}>Disconnect brokerage</button>
          </div>
        )}
        {status && !status.live_trading_enabled && (
          <p className="muted" style={{ marginTop: 12 }}>Live orders are not enabled on this REGRET deployment.</p>
        )}
      </section>

      <details className="advanced" open={advanced} onToggle={(e) => setAdvanced((e.target as HTMLDetailsElement).open)}>
        <summary>Advanced connection</summary>
        <form className="sheet" onSubmit={connectKeys} style={{ marginTop: 12 }}>
          <p className="muted">
            For operators only. Most people should use Connect Alpaca above.
          </p>
          <div className="field">
            <label>Key ID</label>
            <input value={keys.api_key_id} onChange={(e) => setKeys({ ...keys, api_key_id: e.target.value })} />
          </div>
          <div className="field">
            <label>Secret</label>
            <input type="password" value={keys.api_secret} onChange={(e) => setKeys({ ...keys, api_secret: e.target.value })} />
          </div>
          <button className="btn" type="submit">Save encrypted keys</button>
          <p className="muted">These stay on the server, encrypted, for this REGRET user only.</p>
        </form>
      </details>
    </div>
  );
}
