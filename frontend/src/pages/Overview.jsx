import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getStats, listIncidents, triggerScan, createIncident, investigateIncident } from "../api/client";

const DEMO_DATASETS = [
  { urn: "urn:li:dataset:(urn:li:dataPlatform:postgres,raw.orders_raw,PROD)", name: "orders_raw" },
  { urn: "urn:li:dataset:(urn:li:dataPlatform:dbt,staging.stg_orders,PROD)", name: "stg_orders" },
  { urn: "urn:li:dataset:(urn:li:dataPlatform:dbt,marts.fct_daily_revenue,PROD)", name: "fct_daily_revenue" },
  { urn: "urn:li:dataset:(urn:li:dataPlatform:looker,dashboards.revenue_dashboard,PROD)", name: "revenue_dashboard" },
  { urn: "urn:li:dataset:(urn:li:dataPlatform:mlflow,models.churn_risk_model,PROD)", name: "churn_risk_model" },
];

export default function Overview() {
  const [stats, setStats] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const [datasetUrn, setDatasetUrn] = useState(DEMO_DATASETS[1].urn);
  const [problemText, setProblemText] = useState("");
  const [severity, setSeverity] = useState("medium");

  const refresh = async () => {
    try {
      const [s, i] = await Promise.all([getStats(), listIncidents()]);
      setStats(s);
      setIncidents(i);
      setError(null);
    } catch (e) {
      setError("Could not reach the PhoenixForge AI backend. Is it running on port 8000?");
    }
  };

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleScan = async () => {
    setBusy(true);
    await triggerScan();
    await refresh();
    setBusy(false);
  };

  const deriveTitle = (text) => {
    const trimmed = text.trim();
    if (!trimmed) return "Untitled incident";
    return trimmed.length > 90 ? trimmed.slice(0, 90) + "..." : trimmed;
  };

  const handleInvestigate = async (e) => {
    e.preventDefault();
    if (!problemText.trim()) return;
    setBusy(true);
    try {
      const incident = await createIncident({
        dataset_urn: datasetUrn,
        title: deriveTitle(problemText),
        severity,
        description: problemText.trim(),
      });
      await investigateIncident(incident.id);
      setProblemText("");
      await refresh();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <div className="page-eyebrow">Operations overview</div>
      <h1 className="page-title">The forge floor</h1>
      <p className="page-sub">
        Every incident below moved through Discovery, Root Cause, Lineage Intelligence, Repair,
        Validation, GitOps, and Knowledge agents automatically. Nothing merges without the
        Validation Agent's sign-off surfacing here first.
      </p>

      {error && <div className="empty-state">{error}</div>}

      {stats && (
        <div className="stat-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.total_incidents}</div>
            <div className="stat-label">Total incidents</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.repaired}</div>
            <div className="stat-label">Auto-repaired</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.awaiting_review}</div>
            <div className="stat-label">Awaiting review</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.investigating}</div>
            <div className="stat-label">Investigating</div>
          </div>
        </div>
      )}

      <div className="section-label">Report a problem</div>
      <form onSubmit={handleInvestigate} className="card" style={{ marginBottom: 24 }}>
        <label style={{ display: "block", marginBottom: 12 }}>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 6 }}>Which dataset is affected?</div>
          <select
            value={datasetUrn}
            onChange={(e) => setDatasetUrn(e.target.value)}
            className="btn"
            style={{ width: "100%", textAlign: "left" }}
          >
            {DEMO_DATASETS.map((d) => (
              <option key={d.urn} value={d.urn}>
                {d.name}
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: "block", marginBottom: 12 }}>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 6 }}>Describe the problem in your own words</div>
          <textarea
            value={problemText}
            onChange={(e) => setProblemText(e.target.value)}
            placeholder="e.g. Our revenue dashboard has shown $0 since this morning's dbt run failed..."
            rows={4}
            style={{
              width: "100%",
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 8,
              color: "inherit",
              padding: 12,
              fontFamily: "inherit",
              fontSize: 14,
              resize: "vertical",
            }}
          />
        </label>

        <label style={{ display: "block", marginBottom: 16 }}>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 6 }}>Severity</div>
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="btn"
            style={{ width: "100%", textAlign: "left" }}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </label>

        <div className="btn-row">
          <button className="btn btn-primary" type="submit" disabled={busy || !problemText.trim()}>
            {busy ? "Running agent pipeline..." : "Investigate this problem"}
          </button>
          <button className="btn" type="button" onClick={handleScan} disabled={busy}>
            Scan DataHub for anomalies
          </button>
        </div>
      </form>

      <div className="section-label">Incidents</div>
      {incidents.length === 0 ? (
        <div className="empty-state">
          No incidents yet. Describe a problem above to watch the full seven-agent
          pipeline investigate and fix it.
        </div>
      ) : (
        <div className="incident-list">
          {incidents.map((inc) => (
            <Link to={`/incidents/${inc.id}`} key={inc.id} className="incident-row">
              <div>
                <div className="incident-title">{inc.title}</div>
                <div className="incident-meta">{inc.dataset_urn}</div>
              </div>
              <span className={`badge badge-${inc.status}`}>{inc.status.replace("_", " ")}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
