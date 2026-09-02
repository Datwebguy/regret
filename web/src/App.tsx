import { Navigate, NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "./api";
import Landing from "./pages/Landing";
import Auth from "./pages/Auth";
import Dashboard from "./pages/Dashboard";
import Analyze from "./pages/Analyze";
import Portfolio from "./pages/Portfolio";
import Rules from "./pages/Rules";
import Journal from "./pages/Journal";
import Setups from "./pages/Setups";
import Settings from "./pages/Settings";
import Monitor from "./pages/Monitor";
import { BrandMark, SiteFooter } from "./components/ui";

type User = { id: string; email: string; display_name: string };

const LAST_APP = "regret_last_app";
const NAV = [
  { to: "/app", label: "Overview", idx: "01", end: true },
  { to: "/app/analyze", label: "Analyze", idx: "02" },
  { to: "/app/setups", label: "Setups", idx: "03" },
  { to: "/app/portfolio", label: "Portfolio", idx: "04" },
  { to: "/app/rules", label: "Rules", idx: "05" },
  { to: "/app/journal", label: "Journal", idx: "06" },
];

function lastAppPath(): string {
  try {
    const saved = sessionStorage.getItem(LAST_APP);
    if (saved && saved.startsWith("/app")) return saved;
  } catch {
    /* private mode */
  }
  return "/app/analyze";
}

function rememberAppPath(path: string) {
  if (!path.startsWith("/app")) return;
  try {
    sessionStorage.setItem(LAST_APP, path);
  } catch {
    /* private mode */
  }
}

export default function App() {
  const location = useLocation();

  useEffect(() => {
    rememberAppPath(location.pathname);
  }, [location.pathname]);

  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Navigate to="/app" replace />} />
      <Route path="/register" element={<Navigate to="/app" replace />} />
      <Route path="/app/*" element={<Shell />} />
    </Routes>
  );
}

function Shell() {
  return (
    <div className="shell">
      <nav className="mobile-nav">
        <div className="mobile-nav-bar">
          <BrandMark to="/" />
        </div>
        <div className="mobile-nav-links">
          <NavLink to="/">Home</NavLink>
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end}>{item.label}</NavLink>
          ))}
          <NavLink to="/app/settings">Settings</NavLink>
        </div>
      </nav>
      <aside className="spine">
        <BrandMark to="/" />
        <NavLink to="/" style={{ opacity: 0.8, marginBottom: 6 }}>
          <span className="idx">←</span>
          <span>Landing Page</span>
        </NavLink>
        {NAV.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end}>
            <span className="idx">{item.idx}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
        <div className="grow" />
        <div className="who" style={{ fontSize: "11px", color: "var(--muted)", padding: "8px 0" }}>
          Alpaca Paper Trading<br /><span className="mono">PA3XUIGQ0VGB</span>
        </div>
      </aside>

      <main className="page">
        <Routes>
          <Route index element={<Dashboard />} />
          <Route path="analyze" element={<Analyze />} />
          <Route path="setups" element={<Setups />} />
          <Route path="portfolio" element={<Portfolio />} />
          <Route path="rules" element={<Rules />} />
          <Route path="journal" element={<Journal />} />
          <Route path="monitor/:symbol" element={<Monitor />} />
          <Route path="settings" element={<Settings />} />
          <Route path="settings/:section" element={<Settings />} />
        </Routes>
        <SiteFooter />
      </main>
    </div>
  );
}

