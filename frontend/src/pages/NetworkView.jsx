import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import { LoadingSpinner, WarningBanner, Badge, EmptyState } from "../components/Shared";
import NetworkGraph from "../components/NetworkGraph";

export default function NetworkView() {
  const { gene } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    setLoading(true);
    api.getNetwork(gene, 40) // Increased limit for more interesting graph
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [gene]);

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
          Interactive Protein-Protein Interactions (PPI) from STRING-DB. Zoom and drag to explore.
        </p>
      </div>

      <WarningBanner warnings={data.warnings} />

      <div className="network-layout" style={{ display: "grid", gridTemplateColumns: selectedNode ? "1fr 320px" : "1fr", gap: "1.5rem", transition: "all 0.3s ease" }}>
        {/* Network Graph Container */}
        <div className="card" style={{ padding: "0.5rem", position: "relative" }}>
          <NetworkGraph 
            graph={data.graph} 
            onNodeTap={(node) => setSelectedNode(node)} 
          />
          {!selectedNode && (
            <div style={{ position: "absolute", top: "1.5rem", left: "1.5rem", pointerEvents: "none" }}>
              <Badge variant="glass">Click a node for details</Badge>
            </div>
          )}
        </div>

        {/* Node Sidebar (Details) */}
        {selectedNode && (
          <div className="card slide-in-right" style={{ padding: "1.2rem", height: "500px", overflowY: "auto", border: "1px solid var(--accent-blue-alpha)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
              <h3 style={{ margin: 0, color: "var(--accent-cyan)" }}>{selectedNode.label}</h3>
              <button 
                onClick={() => setSelectedNode(null)}
                style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "1.2rem" }}
              >
                &times;
              </button>
            </div>
            
            <div className="detail-item" style={{ marginBottom: "1rem" }}>
              <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Node Type</label>
              <div style={{ fontWeight: 500 }}>{selectedNode.type === "center" ? "Focused Gene" : "Interaction Partner"}</div>
            </div>

            <div className="detail-item" style={{ marginBottom: "1.5rem" }}>
              <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Actions</label>
              <div style={{ marginTop: "0.5rem" }}>
                <Link to={`/gene/${selectedNode.label}`} className="btn-glass" style={{ display: "block", textAlign: "center", marginBottom: "0.5rem" }}>
                  View Full Profile
                </Link>
                <Link to={`/network/${selectedNode.label}`} className="btn-glass" style={{ display: "block", textAlign: "center", color: "var(--accent-blue)" }}>
                  Pivot Network
                </Link>
              </div>
            </div>

            <hr style={{ border: "none", borderTop: "1px solid var(--border-color)", margin: "1rem 0" }} />
            
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              This protein interacts with <strong>{gene}</strong>. Interactions are sourced from STRING-DB with high confidence scores.
            </p>
          </div>
        )}
      </div>

      {/* Interaction Table */}
      {interactions.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <div className="section-header">
            <span className="section-title">
              <span className="icon">🔗</span>
              Tabular Data ({interactions.length})
            </span>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Protein A</th>
                <th>Protein B</th>
                <th>Combined Score</th>
                <th>Experimental</th>
                <th>Database</th>
              </tr>
            </thead>
            <tbody>
              {interactions.map((int, i) => (
                <tr key={i} style={{ opacity: selectedNode && (selectedNode.id !== int.protein_a && selectedNode.id !== int.protein_b) ? 0.4 : 1 }}>
                  <td><Link to={`/gene/${int.protein_a}`}>{int.protein_a}</Link></td>
                  <td><Link to={`/gene/${int.protein_b}`}>{int.protein_b}</Link></td>
                  <td>
                    <span style={{ fontWeight: 600, color: "var(--accent-cyan)" }}>
                      {typeof int.score === "number" ? int.score.toFixed(3) : int.score}
                    </span>
                  </td>
                  <td>{typeof int.escore === "number" ? int.escore.toFixed(3) : "—"}</td>
                  <td>{typeof int.dscore === "number" ? int.dscore.toFixed(3) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

