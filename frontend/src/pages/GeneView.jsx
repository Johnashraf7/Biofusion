import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import { LoadingSpinner, WarningBanner, Badge, ScoreBar, DetailRow, EmptyState } from "../components/Shared";

export default function GeneView() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pathwaysLoading, setPathwaysLoading] = useState(false);
  const [pathways, setPathways] = useState(null);

  useEffect(() => {
    setLoading(true);
    api.getGene(id).then(setData).catch(console.error).finally(() => setLoading(false));
  }, [id]);

  const loadPathways = async () => {
    setPathwaysLoading(true);
    try {
      const full = await api.getGene(id, "pathways,kegg");
      setPathways({
        reactome: full.pathways_reactome || [],
        kegg: full.pathways_kegg || [],
      });
    } catch (e) {
      console.error(e);
    } finally {
      setPathwaysLoading(false);
    }
  };

  if (loading) return <LoadingSpinner text={`Loading gene ${id}...`} />;
  if (!data) return <EmptyState title="Gene Not Found" message={`No data for: ${id}`} />;

  const protein = data.protein || {};
  const diseases = data.diseases || [];

  return (
    <div className="fade-in">
      <div className="page-header">
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
          <h1>{data.gene_symbol || id}</h1>
          {data.ensembl_id && <Badge variant="cyan">{data.ensembl_id}</Badge>}
          {data.uniprot_accession && <Badge variant="blue">UniProt: {data.uniprot_accession}</Badge>}
          {data.biotype && <Badge variant="muted">{data.biotype}</Badge>}
        </div>
        {data.description && (
          <p style={{ color: "var(--text-secondary)", marginTop: "0.5rem" }}>
            {data.description.replace(/\[Source:.*\]/, "").trim()}
          </p>
        )}
      </div>

      <WarningBanner warnings={data.warnings} />

      <div className="card-grid">
        {/* Genomic Info */}
        <div className="card">
          <div className="card-header">
            <span style={{ fontSize: "1.3rem" }}>🧬</span>
            <h3>Genomic Info</h3>
          </div>
          <DetailRow label="Symbol" value={data.gene_symbol} />
          <DetailRow label="Full Name" value={data.gene_name} />
          <DetailRow label="Chromosome" value={data.chromosome} />
          <DetailRow label="Position" value={data.position} />
          <DetailRow label="Biotype" value={data.biotype} />
          {data.ensembl_id && (
            <DetailRow label="Network" value={
              <Link to={`/network/${data.gene_symbol || id}`} className="btn btn-sm" style={{marginTop: "0.3rem"}}>
                View PPI Network →
              </Link>
            } />
          )}
        </div>

        {/* Protein Info */}
        <div className="card">
          <div className="card-header">
            <span style={{ fontSize: "1.3rem" }}>🔬</span>
            <h3>Protein</h3>
          </div>
          <DetailRow label="Protein Name" value={protein.name} />
          <DetailRow label="Length" value={protein.length ? `${protein.length} aa` : null} />
          <DetailRow label="PDB Structures" value={
            protein.pdb_ids && protein.pdb_ids.length > 0
              ? protein.pdb_ids.map((id, i) => <Badge key={i} variant="purple">{id}</Badge>)
              : "None available"
          } />
          {protein.subcellular_locations && protein.subcellular_locations.length > 0 && (
            <DetailRow label="Location" value={protein.subcellular_locations.join(", ")} />
          )}
          {protein.functions && protein.functions.length > 0 && (
            <div style={{ marginTop: "0.75rem" }}>
              <span className="detail-label">Function</span>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginTop: "0.3rem", lineHeight: 1.5 }}>
                {protein.functions[0].substring(0, 300)}{protein.functions[0].length > 300 ? "..." : ""}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Disease Associations */}
      {diseases.length > 0 && (
        <div style={{ marginTop: "1.5rem" }}>
          <div className="section-header">
            <span className="section-title">
              <span className="icon">🏥</span>
              Disease Associations ({diseases.length})
            </span>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Disease</th>
                <th>Score</th>
                <th>ID</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {diseases.slice(0, 15).map((d, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 500 }}>{d.disease_name}</td>
                  <td><ScoreBar score={d.overall_score || 0} /></td>
                  <td><code style={{ fontSize: "0.75rem" }}>{d.disease_id}</code></td>
                  <td>
                    <Link to={`/disease/${d.disease_id}`} className="btn btn-sm">View</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pathways (Lazy Loaded) */}
      <div style={{ marginTop: "1.5rem" }}>
        <div className="section-header">
          <span className="section-title">
            <span className="icon">🛤️</span>
            Pathways
          </span>
          {!pathways && (
            <button className="btn btn-sm" onClick={loadPathways} disabled={pathwaysLoading}>
              {pathwaysLoading ? "Loading..." : "Load Pathways"}
            </button>
          )}
        </div>

        {pathwaysLoading && <LoadingSpinner text="Fetching pathways from Reactome & KEGG..." />}

        {pathways && (
          <div className="fade-in">
            {/* Reactome */}
            {pathways.reactome.length > 0 && (
              <div style={{ marginBottom: "1rem" }}>
                <h4 style={{ marginBottom: "0.5rem", color: "var(--text-secondary)" }}>
                  Reactome <Badge variant="green">{pathways.reactome.length}</Badge>
                </h4>
                <table className="data-table">
                  <thead>
                    <tr><th>Pathway</th><th>ID</th></tr>
                  </thead>
                  <tbody>
                    {pathways.reactome.map((p, i) => (
                      <tr key={i}>
                        <td>{p.name}</td>
                        <td><code>{p.pathway_id}</code></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* KEGG */}
            {pathways.kegg.length > 0 && (
              <div>
                <h4 style={{ marginBottom: "0.5rem", color: "var(--text-secondary)" }}>
                  KEGG <Badge variant="orange">{pathways.kegg.length}</Badge>
                </h4>
                <table className="data-table">
                  <thead>
                    <tr><th>Pathway</th><th>ID</th></tr>
                  </thead>
                  <tbody>
                    {pathways.kegg.map((p, i) => (
                      <tr key={i}>
                        <td>{p.name || p.kegg_pathway_id}</td>
                        <td><code>{p.kegg_pathway_id}</code></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {pathways.reactome.length === 0 && pathways.kegg.length === 0 && (
              <EmptyState title="No Pathways" message="No pathway data found for this gene." />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
