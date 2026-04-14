import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import { LoadingSpinner, WarningBanner, Badge, DetailRow, EmptyState } from "../components/Shared";

export default function DrugView() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getDrug(id).then(setData).catch(console.error).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <LoadingSpinner text={`Loading drug ${id}...`} />;
  if (!data) return <EmptyState title="Drug Not Found" message={`No data for: ${id}`} />;

  const props = data.properties || {};
  const targets = data.targets || [];

  const phaseLabel = (phase) => {
    const labels = { 4: "Approved", 3: "Phase III", 2: "Phase II", 1: "Phase I", 0: "Preclinical" };
    return labels[phase] || `Phase ${phase}`;
  };

  const phaseColor = (phase) => {
    if (phase >= 4) return "green";
    if (phase >= 3) return "cyan";
    if (phase >= 2) return "blue";
    return "muted";
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
          <h1>{data.drug_name || id}</h1>
          {data.chembl_id && <Badge variant="purple">{data.chembl_id}</Badge>}
          {data.max_phase != null && (
            <Badge variant={phaseColor(data.max_phase)}>{phaseLabel(data.max_phase)}</Badge>
          )}
        </div>
      </div>

      <WarningBanner warnings={data.warnings} />

      <div className="card-grid">
        {/* Drug Properties */}
        <div className="card">
          <div className="card-header">
            <span style={{ fontSize: "1.3rem" }}>💊</span>
            <h3>Properties</h3>
          </div>
          <DetailRow label="Name" value={data.drug_name} />
          <DetailRow label="Type" value={data.molecule_type} />
          <DetailRow label="ChEMBL ID" value={data.chembl_id} />
          <DetailRow label="RxCUI" value={data.rxcui} />
          <DetailRow label="Formula" value={props.molecular_formula} />
          <DetailRow label="MW" value={props.molecular_weight ? `${props.molecular_weight} Da` : null} />
          <DetailRow label="ALogP" value={props.alogp} />
          <DetailRow label="Ro5 Violations" value={props.num_ro5_violations} />
          {data.synonyms && data.synonyms.length > 0 && (
            <div style={{ marginTop: "0.75rem" }}>
              <span className="detail-label">Synonyms</span>
              <div style={{ marginTop: "0.3rem", display: "flex", flexWrap: "wrap", gap: "0.3rem" }}>
                {data.synonyms.slice(0, 8).map((s, i) => (
                  <Badge key={i} variant="muted">{s}</Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Targets & Mechanisms */}
        <div className="card">
          <div className="card-header">
            <span style={{ fontSize: "1.3rem" }}>🎯</span>
            <h3>Targets & Mechanisms ({targets.length})</h3>
          </div>
          {targets.length === 0 ? (
            <p style={{ color: "var(--text-muted)" }}>No target data available.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Target</th>
                  <th>Action</th>
                  <th>Type</th>
                </tr>
              </thead>
              <tbody>
                {targets.map((t, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 500 }}>{t.target_name || t.target_chembl_id}</td>
                    <td>{t.action_type || t.mechanism_of_action || "—"}</td>
                    <td><Badge variant="muted">{t.target_type || "—"}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
