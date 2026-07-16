import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getIncident } from "../api/client";

export default function IncidentDetail() {
  const { id } = useParams();
  const [incident, setIncident] = useState(null);
  const [expanded, setExpanded] = useState({});

  useEffect(() => {
    let interval;
    const load = async () => {
      const data = await getIncident(id);
      setIncident(data);
      if (data.status === "investigating") {
        interval = setTimeout(load, 2000);
      }
    };
    load();
    return () => clearTimeout(interval);
  }, [id]);

  if (!incident) {
    return <div className="loading-line">// loading incident...</div>;
  }

  return (
    <div>
      <div className="page-eyebrow">Incident {incident.id.slice(0, 8)}</div>
      <h1 className="page-title">{incident.title}</h1>
      <p className="page-sub">
        Dataset: <span className="mono">{incident.dataset_urn}</span>
        <br />
        Status: <span className={`badge badge-${incident.status}`}>{incident.status.replace("_", " ")}</span>
        {incident.pr_url && (
          <>
            {" "}
            &middot; Pull Request:{" "}
            <a href={incident.pr_url.startsWith("http") ? incident.pr_url : "#"} target="_blank" rel="noreferrer">
              {incident.pr_url.startsWith("http") ? "view PR" : incident.pr_url}
            </a>
          </>
        )}
      </p>

      <div className="section-label">Agent reasoning trace</div>
      <div className="card">
        {incident.traces
          .sort((a, b) => a.step_order - b.step_order)
          .map((t, idx) => (
            <div className="trace-step" key={idx}>
              <div className="trace-index">{t.step_order}</div>
              <div>
                <div className="trace-agent">{t.agent_name}</div>
                <div className="trace-summary">{t.summary}</div>
                {t.detail && (
                  <>
                    <button
                      className="btn"
                      style={{ fontSize: 11, padding: "5px 10px", marginBottom: 8 }}
                      onClick={() => setExpanded((e) => ({ ...e, [idx]: !e[idx] }))}
                    >
                      {expanded[idx] ? "Hide detail" : "Show detail"}
                    </button>
                    {expanded[idx] && <div className="trace-detail">{t.detail}</div>}
                  </>
                )}
              </div>
            </div>
          ))}
        {incident.status === "investigating" && (
          <div className="loading-line">// agents still working, refreshing automatically...</div>
        )}
      </div>

      {incident.repair_code && (
        <>
          <div className="section-label">Generated repair: {incident.repair_file_path}</div>
          <div className="card">
            <div className="trace-detail" style={{ maxHeight: 400 }}>{incident.repair_code}</div>
          </div>
        </>
      )}
    </div>
  );
}
