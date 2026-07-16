import React, { useEffect, useState } from "react";
import { searchKnowledge } from "../api/client";

export default function KnowledgeBase() {
  const [entries, setEntries] = useState([]);
  const [query, setQuery] = useState("");

  const load = async (q = "") => {
    const data = await searchKnowledge(q);
    setEntries(data.slice().reverse());
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <div className="page-eyebrow">Institutional memory</div>
      <h1 className="page-title">Knowledge Base</h1>
      <p className="page-sub">
        Every resolved incident gets distilled into a reusable runbook and written back into
        DataHub. Future incidents on the same pattern are recognized instantly instead of being
        re-investigated from scratch.
      </p>

      <div className="btn-row">
        <input
          className="mono"
          style={{
            flex: 1,
            background: "var(--bg-panel)",
            border: "1px solid var(--line)",
            borderRadius: 6,
            padding: "10px 14px",
            color: "var(--text-hi)",
          }}
          placeholder="Search runbooks (e.g. 'schema drift')"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load(query)}
        />
        <button className="btn btn-primary" onClick={() => load(query)}>
          Search
        </button>
      </div>

      {entries.length === 0 ? (
        <div className="empty-state">
          No knowledge entries yet. They're created automatically after an incident is fully
          investigated and repaired.
        </div>
      ) : (
        entries.map((e) => (
          <div className="knowledge-entry" key={e.urn}>
            <div className="incident-title">{e.incident_title}</div>
            <div className="incident-meta" style={{ marginBottom: 8 }}>{e.dataset_urn}</div>
            <div className="runbook">{e.runbook}</div>
          </div>
        ))
      )}
    </div>
  );
}
