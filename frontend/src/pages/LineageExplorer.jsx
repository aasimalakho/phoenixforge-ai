import React, { useEffect, useMemo, useState } from "react";
import ReactFlow, { Background, Controls, MiniMap } from "reactflow";
import "reactflow/dist/style.css";
import { getLineageGraph } from "../api/client";

function layout(datasets, edges) {
  // Simple left-to-right layered layout based on topological depth.
  const depth = {};
  const outgoing = {};
  datasets.forEach((d) => (depth[d.urn] = 0));
  edges.forEach((e) => {
    outgoing[e.source] = outgoing[e.source] || [];
    outgoing[e.source].push(e.target);
  });

  // repeat a few passes to propagate depth downstream
  for (let pass = 0; pass < datasets.length; pass++) {
    edges.forEach((e) => {
      if (depth[e.target] <= depth[e.source]) {
        depth[e.target] = depth[e.source] + 1;
      }
    });
  }

  const columns = {};
  datasets.forEach((d) => {
    const col = depth[d.urn] || 0;
    columns[col] = columns[col] || [];
    columns[col].push(d);
  });

  const nodes = [];
  Object.entries(columns).forEach(([col, items]) => {
    items.forEach((d, row) => {
      nodes.push({
        id: d.urn,
        data: { label: `${d.name}\n(${d.platform})` },
        position: { x: Number(col) * 260, y: row * 120 },
        style: {
          background: "#1c2023",
          color: "#f2efe9",
          border: "1px solid #262b2f",
          borderRadius: 6,
          fontFamily: "IBM Plex Mono, monospace",
          fontSize: 12,
          padding: 10,
          whiteSpace: "pre-line",
        },
      });
    });
  });

  return nodes;
}

export default function LineageExplorer() {
  const [graph, setGraph] = useState(null);

  useEffect(() => {
    getLineageGraph().then(setGraph);
  }, []);

  const nodes = useMemo(() => (graph ? layout(graph.datasets, graph.edges) : []), [graph]);
  const edges = useMemo(
    () =>
      graph
        ? graph.edges.map((e, i) => ({
            id: `e${i}`,
            source: e.source,
            target: e.target,
            animated: true,
            style: { stroke: "#3fd2c7" },
          }))
        : [],
    [graph]
  );

  return (
    <div>
      <div className="page-eyebrow">Lineage intelligence</div>
      <h1 className="page-title">Lineage Explorer</h1>
      <p className="page-sub">
        The full DataHub lineage graph PhoenixForge AI's agents traverse to compute blast radius.
        Drag to pan, scroll to zoom.
      </p>

      <div className="card" style={{ height: "65vh", padding: 0 }}>
        {!graph ? (
          <div className="loading-line" style={{ padding: 20 }}>// loading lineage graph...</div>
        ) : (
          <ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }}>
            <Background color="#262b2f" gap={20} />
            <Controls />
            <MiniMap
              nodeColor={() => "#ff5a1f"}
              maskColor="rgba(12,14,15,0.85)"
              style={{ background: "#15181b" }}
            />
          </ReactFlow>
        )}
      </div>
    </div>
  );
}
