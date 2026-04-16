import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { useWorkbench } from "../context/WorkbenchContext";
import { LoadingSpinner, WarningBanner, RiskBadge, DetailRow, EmptyState, Badge } from "../components/Shared";

export default function VariantView() {
  const { id } = useParams();
  const { togglePin, isPinned } = useWorkbench();
  const pinned = isPinned(id, "variant");
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getVariant(id).then(setData).catch(console.error).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <LoadingSpinner text={`Loading variant ${id}...`} />;
  if (!data || data.error) {
    return <EmptyState title="Variant Not Found" message={data?.error || `No data for: ${id}`} />;
  }

  const clinvar = data.clinvar || {};
  const risk = data.risk_assessment || {};

  return (
    <div className="fade-in">
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
            <h1>{data.rsid || data.variant_id}</h1>
            <RiskBadge level={risk.risk_level || "uncertain"} />
          </div>
          {data.variant_id !== data.rsid && (
            <p style={{ color: "var(--text-muted)", marginTop: "0.3rem" }}>
              <code>{data.variant_id}</code>
            </p>
          )}
        </div>
        <button 
          onClick={() => togglePin({ id, type: "variant", name: data.rsid || data.variant_id })}
          className={pinned ? "btn-active" : "btn-glass"}
          style={{ fontSize: "0.9rem", padding: "0.5rem 1rem" }}
        >
          {pinned ? "★ Pinned" : "☆ Pin to Workbench"}
        </button>
      </div>

      <WarningBanner warnings={data.warnings} />

      <div className="card-grid">
        {/* Risk Assessment */}
        <div className="card">
          <div className="card-header">
            <span style={{ fontSize: "1.3rem" }}>⚠️</span>
            <h3>Risk Assessment</h3>
          </div>
          <DetailRow label="Risk Level" value={<RiskBadge level={risk.risk_level} />} />
          <DetailRow label="Risk Score" value={`${Math.round((risk.risk_score || 0) * 100)}%`} />
          <DetailRow label="Clinical Sig." value={risk.clinical_significance} />
          <DetailRow label="CADD Phred" value={
            data.cadd_phred != null
              ? <span>
                  {data.cadd_phred.toFixed(1)}
                  {data.cadd_phred >= 30 && <Badge variant="red" style={{marginLeft: "0.5rem"}}>Deleterious</Badge>}
                  {data.cadd_phred >= 20 && data.cadd_phred < 30 && <Badge variant="orange" style={{marginLeft: "0.5rem"}}>Moderate</Badge>}
                  {data.cadd_phred < 20 && <Badge variant="green" style={{marginLeft: "0.5rem"}}>Tolerated</Badge>}
                </span> 
              : "N/A"
          } />
          <DetailRow label="Allele Freq." value={
            data.allele_frequency != null 
              ? `${(data.allele_frequency * 100).toFixed(4)}%`
              : "N/A"
          } />
        </div>

        {/* ClinVar Details */}
        <div className="card">
          <div className="card-header">
            <span style={{ fontSize: "1.3rem" }}>🏥</span>
            <h3>ClinVar Details</h3>
          </div>
          <DetailRow label="Significance" value={clinvar.clinical_significance} />
          <DetailRow label="Review Status" value={clinvar.review_status} />
          <DetailRow label="Variation ID" value={clinvar.variation_id} />
          <DetailRow label="Allele ID" value={clinvar.allele_id} />
          {clinvar.conditions && clinvar.conditions.length > 0 && (
            <div style={{ marginTop: "0.75rem" }}>
              <span className="detail-label">Associated Conditions</span>
              <div style={{ marginTop: "0.5rem", display: "flex", flexWrap: "wrap", gap: "0.3rem" }}>
                {clinvar.conditions.map((c, i) => (
                  <Badge key={i} variant="orange">{c}</Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
