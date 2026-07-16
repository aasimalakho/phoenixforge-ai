import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getStats, listIncidents, triggerScan, createIncident, investigateIncident } from "../api/client";

const DEMO_DATASET_URN =
  "urn:li:dataset:(urn:li:dataPlatform:dbt,staging.stg_orders,PROD)";

export default function Overview() {
  const [stats, setStats] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

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

  const handleSimulate = async () => {
    setBusy(true);
    const incident = await createIncident({
      dataset_urn: DEMO_DATASET_URN,
      title: "stg_orders dbt run failing - column 'order_total' missing",
      severity: "high",
    });
    await investigateIncident(incident.id);
    await refresh();
    setBusy(false);
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

      <div className="btn-row">
        <button className="btn btn-primary" onClick={handleSimulate} disabled={busy}>
          {busy ? "Running agent pipeline..." : "Simulate schema-drift incident"}
        </button>
        <button className="btn" onClick={handleScan} disabled={busy}>
          Scan DataHub for anomalies
        </button>
      </div>

      <div className="section-label">Incidents</div>
      {incidents.length === 0 ? (
        <div className="empty-state">
          No incidents yet. Click "Simulate schema-drift incident" to watch the full
          seven-agent pipeline run against the demo scenario.
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
