import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import { useWorkbench } from "../context/WorkbenchContext";
import { LoadingSpinner, WarningBanner, Badge, ScoreBar, DetailRow, EmptyState } from "../components/Shared";
import AISynthesis from "../components/AISynthesis";

export default function DiseaseView() {
  const { id } = useParams();
  const { togglePin, isPinned } = useWorkbench();
  const pinned = isPinned(id, "disease");
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getDisease(id).then(setData).catch(console.error).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <LoadingSpinner text={`Loading disease ${id}...`} />;
  if (!data) return <EmptyState title="Disease Not Found" message={`No data for: ${id}`} />;

  const genes = data.associated_genes || [];
  const drugs = data.known_drugs || [];
  const icd10 = data.icd10_codes || [];

  return (
    <div className="fade-in">
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
            <h1>{data.disease_name || id}</h1>
            {data.disease_id && <Badge variant="green">{data.disease_id}</Badge>}
          </div>
          {data.description && (
            <p style={{ color: "var(--text-secondary)", marginTop: "0.5rem", maxWidth: "700px" }}>
              {data.description.substring(0, 300)}{data.description.length > 300 ? "..." : ""}
            </p>
          )}
        </div>
        <button 
          onClick={() => togglePin({ id, type: "disease", name: data.disease_name })}
          className={pinned ? "btn-active" : "btn-glass"}
          style={{ fontSize: "0.9rem", padding: "0.5rem 1rem" }}
        >
          {pinned ? "★ Pinned" : "☆ Pin to Workbench"}
        </button>
      </div>

      <WarningBanner warnings={data.warnings} />

      <div style={{ marginBottom: "1.5rem" }}>
        <AISynthesis type="disease" data={data} />
      </div>

      <div className="card-grid">
        {/* ICD-10 Codes */}
        <div className="card">
          <div className="card-header">
            <span style={{ fontSize: "1.3rem" }}>🏷️</span>
            <h3>ICD-10 Codes</h3>
          </div>
          {icd10.length === 0 ? (
            <p style={{ color: "var(--text-muted)" }}>No matching ICD-10 codes found.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr><th>Code</th><th>Description</th><th>Category</th></tr>
              </thead>
              <tbody>
                {icd10.map((c, i) => (
                  <tr key={i}>
                    <td><Badge variant="blue">{c.code}</Badge></td>
                    <td>{c.description}</td>
                    <td><Badge variant="muted">{c.category}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Known Drugs */}
        <div className="card">
          <div className="card-header">
            <span style={{ fontSize: "1.3rem" }}>💊</span>
            <h3>Known Drugs ({drugs.length})</h3>
          </div>
          {drugs.length === 0 ? (
            <p style={{ color: "var(--text-muted)" }}>No known drugs found.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr><th>Drug</th><th>Type</th><th>Status</th></tr>
              </thead>
              <tbody>
                {drugs.slice(0, 10).map((d, i) => {
                  const phase = (d.max_phase || d.indication_stage || "").replace(/_/g, " ");
                  const isApproved = phase.toUpperCase().includes("APPROVAL");
                  return (
                    <tr key={i}>
                      <td>
                        <Link to={`/drug/${d.drug_id || d.drug_name}`} style={{ fontWeight: 500 }}>
                          {d.drug_name}
                        </Link>
                      </td>
                      <td style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{d.drug_type || "—"}</td>
                      <td><Badge variant={isApproved ? "green" : "muted"}>{phase || "Unknown"}</Badge></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Associated Genes */}
      {genes.length > 0 && (
        <div style={{ marginTop: "1.5rem" }}>
          <div className="section-header">
            <span className="section-title">
              <span className="icon">🧬</span>
              Associated Genes ({genes.length})
            </span>
          </div>
          <table className="data-table">
            <thead>
              <tr><th>Gene</th><th>Name</th><th>Score</th><th>Action</th></tr>
            </thead>
            <tbody>
              {genes.slice(0, 20).map((g, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>
                    <Link to={`/gene/${g.ensembl_id || g.gene_symbol}`}>{g.gene_symbol}</Link>
                  </td>
                  <td style={{ color: "var(--text-secondary)" }}>{g.gene_name}</td>
                  <td><ScoreBar score={g.overall_score || 0} /></td>
                  <td>
                    <Link to={`/gene/${g.ensembl_id || g.gene_symbol}`} className="btn btn-sm">View</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
