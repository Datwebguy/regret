import { FormEvent, useEffect, useState } from "react";
import { ApiError, api } from "../api";
import { Empty, PageHead } from "../components/ui";

export default function Rules() {
  const [rules, setRules] = useState<any[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    rule_type: "max_position_pct",
    name: "",
    severity: "HARD",
    threshold: "",
    description: "",
  });

  async function load() {
    const data = await api.get<{ rules: any[]; templates: any[] }>("/api/rules");
    setRules(data.rules);
    setTemplates(data.templates);
  }

  useEffect(() => { load().catch((err) => setError(err.message)); }, []);

  async function create(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api.post("/api/rules", form);
      setForm({ ...form, name: "", threshold: "", description: "" });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to save rule.");
    }
  }

  async function applyTemplates() {
    await api.post("/api/rules/templates", {});
    await load();
  }

  async function remove(id: string) {
    await api.del(`/api/rules/${id}`);
    await load();
  }

  return (
    <div className="stack">
      <PageHead
        kicker="Rules"
        title="Your trading rules"
        lead="Tell REGRET how you want to trade. These rules are used whenever your ideas are analyzed."
      />
      {error && <p className="error">{error}</p>}
      <div className="grid cols-2">
        <form className="sheet" onSubmit={create}>
          <div className="sheet-head"><h3>Add a rule</h3></div>
          <div className="field">
            <label>Type</label>
            <select value={form.rule_type} onChange={(e) => setForm({ ...form, rule_type: e.target.value })}>
              {templates.map((t) => <option key={t.rule_type} value={t.rule_type}>{t.name}</option>)}
              <option value="custom">Custom</option>
            </select>
          </div>
          <div className="field">
            <label>Name</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </div>
          <div className="field">
            <label>Limit</label>
            <input value={form.threshold} onChange={(e) => setForm({ ...form, threshold: e.target.value })} />
          </div>
          <div className="field">
            <label>If broken</label>
            <select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })}>
              <option value="HARD">Block the trade</option>
              <option value="SOFT">Warn only</option>
            </select>
          </div>
          <button className="btn primary" type="submit">Save rule</button>
        </form>

        <section className="sheet">
          <div className="sheet-head"><h3>In use</h3><span className="faint">{rules.length}</span></div>
          {rules.length === 0 && <Empty>No rules yet. Analyses will still run; nothing is assumed for you.</Empty>}
          {rules.map((r) => (
            <div key={r.id} style={{ padding: "14px 0", borderBottom: "1px solid var(--rule)" }}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <strong>{r.name}</strong>
                <span className="chip">{r.severity === "HARD" ? "Blocks" : "Warns"}</span>
              </div>
              <div className="faint" style={{ marginTop: 4 }}>
                Limit {r.threshold ?? "n/a"}
              </div>
              <div style={{ marginTop: 8 }}>
                <button className="btn danger" onClick={() => remove(r.id)}>Remove</button>
              </div>
            </div>
          ))}
          <div style={{ marginTop: 16 }}>
            <button className="btn ghost" onClick={applyTemplates}>Add starter rules</button>
          </div>
        </section>
      </div>
    </div>
  );
}
