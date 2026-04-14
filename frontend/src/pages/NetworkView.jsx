import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import { LoadingSpinner, WarningBanner, Badge, EmptyState } from "../components/Shared";

export default function NetworkView() {
  const { gene } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const canvasRef = useRef(null);

  useEffect(() => {
    setLoading(true);
    api.getNetwork(gene, 20).then(setData).catch(console.error).finally(() => setLoading(false));
  }, [gene]);

  useEffect(() => {
    if (data && data.graph && canvasRef.current) {
      drawGraph(canvasRef.current, data.graph);
    }
  }, [data]);

  if (loading) return <LoadingSpinner text={`Loading PPI network for ${gene}...`} />;
  if (!data) return <EmptyState title="Network Not Found" message={`No interaction data for: ${gene}`} />;

  const interactions = data.interactions || [];

  return (
    <div className="fade-in">
      <div className="page-header">
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
          <h1>PPI Network: {gene}</h1>
          <Badge variant="cyan">{data.graph?.node_count || 0} nodes</Badge>
          <Badge variant="blue">{data.graph?.edge_count || 0} edges</Badge>
        </div>
        <p style={{ color: "var(--text-muted)", marginTop: "0.3rem" }}>
          Protein-protein interactions from STRING-DB (top {interactions.length}, score &ge; 400)
        </p>
      </div>

      <WarningBanner warnings={data.warnings} />

      {/* Network Canvas */}
      <canvas ref={canvasRef} className="network-canvas" id="network-graph"></canvas>

      {/* Interaction Table */}
      {interactions.length > 0 && (
        <div style={{ marginTop: "1.5rem" }}>
          <div className="section-header">
            <span className="section-title">
              <span className="icon">🔗</span>
              Interactions ({interactions.length})
            </span>
          </div>
          <table className="data-table" id="interaction-table">
            <thead>
              <tr>
                <th>Protein A</th>
                <th>Protein B</th>
                <th>Combined Score</th>
                <th>Experimental</th>
                <th>Database</th>
                <th>Text Mining</th>
              </tr>
            </thead>
            <tbody>
              {interactions.map((int, i) => (
                <tr key={i}>
                  <td>
                    <Link to={`/gene/${int.protein_a}`} style={{ fontWeight: 500 }}>
                      {int.protein_a}
                    </Link>
                  </td>
                  <td>
                    <Link to={`/gene/${int.protein_b}`} style={{ fontWeight: 500 }}>
                      {int.protein_b}
                    </Link>
                  </td>
                  <td>
                    <span style={{
                      fontFamily: "var(--font-mono)",
                      color: int.score >= 0.9 ? "var(--accent-green)" :
                             int.score >= 0.7 ? "var(--accent-cyan)" :
                             "var(--text-secondary)",
                      fontWeight: 600,
                    }}>
                      {typeof int.score === "number" ? int.score.toFixed(3) : int.score}
                    </span>
                  </td>
                  <td>{typeof int.escore === "number" ? int.escore.toFixed(3) : "—"}</td>
                  <td>{typeof int.dscore === "number" ? int.dscore.toFixed(3) : "—"}</td>
                  <td>{typeof int.tscore === "number" ? int.tscore.toFixed(3) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {interactions.length === 0 && (
        <EmptyState title="No Interactions" message="No protein-protein interactions found for this gene." />
      )}
    </div>
  );
}

/**
 * Draw a simple force-directed-like graph on canvas.
 * Lightweight: no heavy libraries, just raw Canvas2D.
 */
function drawGraph(canvas, graph) {
  if (!graph || !graph.nodes || graph.nodes.length === 0) return;

  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();

  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const W = rect.width;
  const H = rect.height;
  const nodes = graph.nodes;
  const edges = graph.edges;

  // Position nodes in a circle with center node in the middle
  const centerIdx = nodes.findIndex((n) => n.type === "center");
  const partners = nodes.filter((n) => n.type !== "center");
  const positions = {};

  // Center node
  if (centerIdx >= 0) {
    positions[nodes[centerIdx].id] = { x: W / 2, y: H / 2 };
  }

  // Partner nodes in a circle
  const radius = Math.min(W, H) * 0.35;
  partners.forEach((node, i) => {
    const angle = (2 * Math.PI * i) / partners.length - Math.PI / 2;
    positions[node.id] = {
      x: W / 2 + radius * Math.cos(angle),
      y: H / 2 + radius * Math.sin(angle),
    };
  });

  // Clear
  ctx.fillStyle = "#151d2e";
  ctx.fillRect(0, 0, W, H);

  // Draw edges
  edges.forEach((edge) => {
    const src = positions[edge.source];
    const tgt = positions[edge.target];
    if (!src || !tgt) return;

    const weight = edge.weight || 0.5;
    ctx.beginPath();
    ctx.moveTo(src.x, src.y);
    ctx.lineTo(tgt.x, tgt.y);
    ctx.strokeStyle = `rgba(59, 130, 246, ${0.15 + weight * 0.4})`;
    ctx.lineWidth = 0.5 + weight * 2;
    ctx.stroke();
  });

  // Draw nodes
  nodes.forEach((node) => {
    const pos = positions[node.id];
    if (!pos) return;

    const isCenter = node.type === "center";
    const r = isCenter ? 18 : 10;

    // Glow
    if (isCenter) {
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, r + 6, 0, 2 * Math.PI);
      ctx.fillStyle = "rgba(6, 182, 212, 0.15)";
      ctx.fill();
    }

    // Node circle
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, r, 0, 2 * Math.PI);
    ctx.fillStyle = isCenter ? "#06b6d4" : "#3b82f6";
    ctx.fill();
    ctx.strokeStyle = isCenter ? "#0891b2" : "#2563eb";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Label
    ctx.fillStyle = "#e2e8f0";
    ctx.font = `${isCenter ? "bold 13" : "11"}px Inter, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillText(node.label, pos.x, pos.y + r + 5);
  });
}
