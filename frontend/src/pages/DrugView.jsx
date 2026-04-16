import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import { useWorkbench } from "../context/WorkbenchContext";
import { LoadingSpinner, WarningBanner, Badge, DetailRow, EmptyState } from "../components/Shared";
import AISynthesis from "../components/AISynthesis";

export default function DrugView() {
  const { id } = useParams();
  const { togglePin, isPinned } = useWorkbench();
  const pinned = isPinned(id, "drug");
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const [trials, setTrials] = useState([]);
  const [trialsLoading, setTrialsLoading] = useState(false);

  useEffect(() => {
    const fetchDrugData = async () => {
      setLoading(true);
      try {
        const res = await api.getDrug(id);
        setData(res);
        
        // Parallel fetch for trials to avoid waterfall
        setTrialsLoading(true);
        try {
          const trialsRes = await api.getDrugTrials(id, res.drug_name);
          setTrials(trialsRes.trials || []);
        } catch (trialErr) {
          console.error("Clinical trials fetch failed:", trialErr);
          setTrials([]);
        } finally {
          setTrialsLoading(false);
        }
      } catch (err) {
        console.error("Drug details fetch failed:", err);
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchDrugData();
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
      {/* ... prev header code ... */}
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
            <h1>{data.drug_name || id}</h1>
            {data.chembl_id && <Badge variant="purple">{data.chembl_id}</Badge>}
            {data.max_phase != null && (
              <Badge variant={phaseColor(data.max_phase)}>{phaseLabel(data.max_phase)}</Badge>
            )}
          </div>
        </div>
        <button 
          onClick={() => togglePin({ id, type: "drug", name: data.drug_name })}
          className={pinned ? "btn-active" : "btn-glass"}
          style={{ fontSize: "0.9rem", padding: "0.5rem 1rem" }}
        >
          {pinned ? "★ Pinned" : "☆ Pin to Workbench"}
        </button>
      </div>

      <WarningBanner warnings={data.warnings} />

      <div style={{ marginBottom: "1.5rem" }}>
        <AISynthesis type="drug" data={data} />
      </div>

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
            <div style={{ maxHeight: "300px", overflowY: "auto" }}>
              <table className="data-table">
                <thead>
                  <tr><th>Target</th><th>Action</th><th>Network</th></tr>
                </thead>
                <tbody>
                  {targets.map((t, i) => {
                    const geneSymbol = t.target_name || t.target_chembl_id;
                    return (
                      <tr key={i}>
                        <td style={{ fontWeight: 500 }}>
                          <Link to={`/gene/${geneSymbol}`} style={{ color: "inherit" }}>{geneSymbol}</Link>
                        </td>
                        <td>{t.action_type || t.mechanism_of_action || "—"}</td>
                        <td>
                          <Link to={`/network/${geneSymbol}`} style={{ fontSize: "0.8rem", color: "var(--accent-cyan)" }}>
                            Explore 🕸️
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Clinical Trials Section */}
      <div style={{ marginTop: "2rem" }}>
        <div className="section-header">
          <span className="section-title">
            <span className="icon">🏥</span>
            Clinical Investigations (ClinicalTrials.gov)
          </span>
          {trialsLoading && <Badge variant="glass">Loading...</Badge>}
        </div>

        {trialsLoading ? (
            <div className="card" style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>
              Fetching active clinical studies...
            </div>
        ) : trials.length === 0 ? (
          <div className="card" style={{ padding: "1.5rem", textAlign: "center", color: "var(--text-muted)" }}>
            No registered clinical trials found for this compound.
          </div>
        ) : (
          <div className="card" style={{ padding: "0.5rem" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>NCT ID</th>
                  <th>Brief Title</th>
                  <th>Status</th>
                  <th>Phase</th>
                  <th>Sponsor</th>
                </tr>
              </thead>
              <tbody>
                {trials.map((trial, i) => (
                  <tr key={i}>
                    <td>
                      <a 
                        href={`https://clinicaltrials.gov/study/${trial.nct_id}`} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{ fontFamily: "var(--font-mono)", fontWeight: 600, color: "var(--accent-cyan)" }}
                      >
                        {trial.nct_id} ↗
                      </a>
                    </td>
                    <td style={{ fontSize: "0.9rem", maxWidth: "400px" }}>{trial.title}</td>
                    <td>
                      <Badge variant={trial.status === "COMPLETED" ? "green" : trial.status === "RECRUITING" ? "cyan" : "muted"}>
                        {trial.status.replace(/_/g, " ")}
                      </Badge>
                    </td>
                    <td><Badge variant="blue">{trial.phase.join(", ") || "N/A"}</Badge></td>
                    <td style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{trial.sponsor}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
