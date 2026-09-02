import { Navigate, NavLink, Outlet, Route, Routes } from "react-router-dom";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import Analyze from "./pages/Analyze";
import Portfolio from "./pages/Portfolio";
import Rules from "./pages/Rules";
import Journal from "./pages/Journal";
import Setups from "./pages/Setups";
import Settings from "./pages/Settings";
import Monitor from "./pages/Monitor";
import { BrandMark, SiteFooter } from "./components/ui";

const NAV = [
  { to: "/app", label: "Overview", idx: "01", end: true },
  { to: "/app/analyze", label: "Analyze", idx: "02" },
  { to: "/app/setups", label: "Setups", idx: "03" },
  { to: "/app/portfolio", label: "Portfolio", idx: "04" },
  { to: "/app/rules", label: "Rules", idx: "05" },
  { to: "/app/journal", label: "Journal", idx: "06" },
];

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Navigate to="/app" replace />} />
      <Route path="/register" element={<Navigate to="/app" replace />} />
      <Route path="/app" element={<Shell />}>
        <Route index element={<Dashboard />} />
        <Route path="analyze" element={<Analyze />} />
        <Route path="setups" element={<Setups />} />
        <Route path="portfolio" element={<Portfolio />} />
        <Route path="rules" element={<Rules />} />
        <Route path="journal" element={<Journal />} />
        <Route path="monitor/:symbol" element={<Monitor />} />
        <Route path="settings" element={<Settings />} />
        <Route path="settings/:section" element={<Settings />} />
        <Route path="*" element={<Navigate to="/app" replace />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
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
        <Outlet />
        <SiteFooter />
      </main>
    </div>
  );
}
