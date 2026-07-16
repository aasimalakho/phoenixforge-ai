import React from "react";
import { Routes, Route, NavLink } from "react-router-dom";
import Overview from "./pages/Overview.jsx";
import IncidentDetail from "./pages/IncidentDetail.jsx";
import LineageExplorer from "./pages/LineageExplorer.jsx";
import KnowledgeBase from "./pages/KnowledgeBase.jsx";
import Chat from "./pages/Chat.jsx";

const NAV_ITEMS = [
  { to: "/", label: "Overview", index: "01" },
  { to: "/lineage", label: "Lineage Explorer", index: "02" },
  { to: "/knowledge", label: "Knowledge Base", index: "03" },
  { to: "/chat", label: "Ask PhoenixForge", index: "04" },
];

export default function App() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div>
          <div className="brand">
            <span className="brand-mark" />
            <span className="brand-name">PhoenixForge AI</span>
          </div>
          <div className="brand-tag">Self-healing data systems</div>
        </div>

        <nav className="nav-list">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}
            >
              <span className="nav-index">{item.index}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="pulse-row">
            <span className="pulse-dot" />
            Agents idle, watching DataHub
          </div>
          Built on DataHub's Context Platform
        </div>
      </aside>

      <main className="content">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/incidents/:id" element={<IncidentDetail />} />
          <Route path="/lineage" element={<LineageExplorer />} />
          <Route path="/knowledge" element={<KnowledgeBase />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </main>
    </div>
  );
}
