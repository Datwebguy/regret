import { ReactNode, useState } from "react";
import { Link } from "react-router-dom";

export function BrandMark({ to = "/" }: { to?: string }) {
  return (
    <Link to={to} className="brand" aria-label="REGRET">
      <img src="/mark.png" alt="" width={32} height={32} />
      <span className="wordmark">RE<i>GRET</i></span>
    </Link>
  );
}

export function PasswordField({
  value,
  onChange,
  autoComplete,
  label = "Password",
}: {
  value: string;
  onChange: (value: string) => void;
  autoComplete?: string;
  label?: string;
}) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="field">
      <label>{label}</label>
      <div className="password-wrap">
        <input
          type={visible ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required
          minLength={10}
          autoComplete={autoComplete}
        />
        <button
          type="button"
          className="eye"
          aria-label={visible ? "Hide password" : "Show password"}
          onClick={() => setVisible((v) => !v)}
        >
          {visible ? "Hide" : "Show"}
        </button>
      </div>
    </div>
  );
}

export function SiteFooter() {
  return (
    <footer className="site-foot">
      <a href="/" className="brand">
        <img src="/mark.png" alt="" width={28} height={28} />
        <span className="wordmark">RE<i>GRET</i></span>
      </a>
      <nav>
        <a href="/terms">Terms</a>
        <a href="/privacy">Privacy</a>
      </nav>
    </footer>
  );
}

export function Stamp({ verdict, large = false }: { verdict?: string; large?: boolean }) {
  const v = (verdict || "n/a").toUpperCase();
  const cls = ["BUY", "WAIT", "REDUCE", "REJECT", "INCOMPLETE"].includes(v) ? v : "";
  return <span className={`stamp ${cls} ${large ? "lg" : ""}`}>{v}</span>;
}

export function PageHead({ kicker, title, lead }: { kicker: string; title: string; lead?: string }) {
  return (
    <header>
      <div className="page-kicker">{kicker}</div>
      <h1>{title}</h1>
      {lead && <p className="page-lead">{lead}</p>}
    </header>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="empty">{children}</p>;
}

export function Figure({ label, value, hint }: { label: string; value?: string | null; hint?: string }) {
  const missing = value === null || value === undefined || value === "";
  return (
    <div className="figure">
      <div className="lbl">{label}</div>
      <div className="num">{missing ? "n/a" : value}</div>
      <div className="sub">{missing ? "Unavailable" : hint || ""}</div>
    </div>
  );
}

export function Status({ tone, children }: { tone?: "pass" | "fail" | "warn"; children: ReactNode }) {
  return <span className={tone}>{children}</span>;
}

export function RuleTone(status?: string) {
  if (status === "PASS") return "pass";
  if (status === "FAIL") return "fail";
  if (status === "WARNING") return "warn";
  return undefined;
}
