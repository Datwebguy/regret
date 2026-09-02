import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, api } from "../api";
import { BrandMark, PasswordField, SiteFooter } from "../components/ui";

export default function Auth({
  mode,
  onAuth,
}: {
  mode: "login" | "register";
  onAuth: (user: { id: string; email: string; display_name: string }) => void;
}) {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const path = mode === "login" ? "/api/auth/login" : "/api/auth/register";
      const result = await api.post<{ user: any }>(path, { email, password });
      onAuth(result.user);
      navigate("/app/analyze", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to authenticate.");
    }
  }

  return (
    <div className="auth-wrap">
      <section className="auth-panel">
        <BrandMark />
        <div style={{ height: 48 }} />
        <div className="eyebrow">{mode === "login" ? "Welcome back" : "New account"}</div>
        <h1>{mode === "login" ? "Sign in." : "Create a REGRET account."}</h1>
        <p className="page-lead">
          This is your REGRET account. A brokerage is separate.
        </p>
        <form onSubmit={submit} style={{ maxWidth: 420 }}>
          <div className="field">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
          </div>
          <PasswordField
            value={password}
            onChange={setPassword}
            label={mode === "register" ? "Password, at least 10 characters" : "Password"}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
          />
          {error && <p className="error">{error}</p>}
          <div className="actions">
            <button className="btn primary" type="submit">{mode === "login" ? "Enter" : "Create account"}</button>
            {mode === "login"
              ? <Link to="/register">Need an account</Link>
              : <Link to="/login">Already have one</Link>}
          </div>
        </form>
        <SiteFooter />
      </section>
      <aside className="auth-side">
        <div>
          <div className="eyebrow" style={{ color: "#d36a5f" }}>Before the order</div>
          <h2>The expensive trade is often the one you should not have placed.</h2>
        </div>
        <p>You can create this account and analyze an idea without connecting a brokerage.</p>
      </aside>
    </div>
  );
}
