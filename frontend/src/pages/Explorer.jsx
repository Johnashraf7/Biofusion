import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../api/client";
import { LoadingSpinner, Badge, WarningBanner, EmptyState } from "../components/Shared";

export default function Explorer() {
  const [query, setQuery] = useState("");
  const [queryType, setQueryType] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const data = await api.search(query.trim(), queryType || null);
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getLink = (item) => {
    const type = item.type;
    const id = item.id;
    if (type === "gene") return `/gene/${id}`;
    if (type === "variant") return `/variant/${encodeURIComponent(id)}`;
    if (type === "drug") return `/drug/${id}`;
    if (type === "disease") return `/disease/${id}`;
    return `/gene/${id}`;
  };

  const sourceBadge = (source) => {
    const variants = {
      Ensembl: "cyan",
      UniProt: "blue",
      OpenTargets: "green",
      ChEMBL: "purple",
      "MyVariant.info": "orange",
    };
    return <Badge variant={variants[source] || "muted"}>{source}</Badge>;
  };

  return (
    <div className="fade-in">
      {/* Hero */}
      <div style={{ textAlign: "center", padding: "2rem 0 2.5rem" }}>
        <h1 style={{ fontSize: "2.4rem", marginBottom: "0.5rem", letterSpacing: "-0.02em" }}>
          <span style={{ color: "var(--accent-cyan)" }}>Bio</span>Fusion
        </h1>
        <p style={{ color: "var(--text-muted)", maxWidth: "520px", margin: "0 auto" }}>
          Free bioinformatics data fusion. Search genes, variants, drugs, and diseases
          across UniProt, Ensembl, ClinVar, ChEMBL, Open Targets, and more.
        </p>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} style={{ maxWidth: "700px", margin: "0 auto 2rem" }}>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <input
            className="input"
            type="text"
            placeholder="Search genes (BRCA1), variants (rs121913529), drugs (imatinib), diseases..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
            id="search-input"
          />
          <select
            className="input"
            value={queryType}
            onChange={(e) => setQueryType(e.target.value)}
            style={{ width: "130px", flexShrink: 0 }}
            id="search-type"
          >
            <option value="">Auto</option>
            <option value="gene">Gene</option>
            <option value="variant">Variant</option>
            <option value="drug">Drug</option>
            <option value="disease">Disease</option>
          </select>
          <button className="btn btn-primary" type="submit" id="search-btn" disabled={loading}>
            {loading ? "..." : "Search"}
          </button>
        </div>
      </form>

      {/* Quick Examples */}
      {!results && !loading && (
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <span style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginRight: "0.5rem" }}>
            Try:
          </span>
          {["BRCA1", "TP53", "rs121913529", "imatinib", "breast cancer"].map((ex) => (
            <button
              key={ex}
              className="btn btn-sm"
              style={{ margin: "0.2rem" }}
              onClick={() => { setQuery(ex); }}
            >
              {ex}
            </button>
          ))}
        </div>
      )}

      {error && <WarningBanner warnings={[error]} />}

      {loading && <LoadingSpinner text="Querying biological databases..." />}

      {/* Results */}
      {results && !loading && (
        <div className="fade-in">
          <div className="section-header">
            <span className="section-title">
              <span className="icon">🔬</span>
              {results.result_count} result{results.result_count !== 1 ? "s" : ""} for "{results.query}"
            </span>
            <Badge variant={results.type === "gene" ? "cyan" : results.type === "variant" ? "orange" : results.type === "drug" ? "purple" : "green"}>
              {results.type}
            </Badge>
          </div>

          <WarningBanner warnings={results.warnings} />

          {results.result_count === 0 ? (
            <EmptyState title="No results" message="Try a different query or query type." />
          ) : (
            <table className="data-table" id="results-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Source</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {results.results.map((item, i) => (
                  <tr key={i} className="fade-in" style={{ animationDelay: `${i * 50}ms` }}>
                    <td>
                      <Link to={getLink(item)} style={{ fontWeight: 600 }}>
                        {item.name || item.id}
                      </Link>
                      <br />
                      <code style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{item.id}</code>
                    </td>
                    <td style={{ color: "var(--text-secondary)", maxWidth: "350px" }}>
                      {item.description ? item.description.substring(0, 120) : "—"}
                    </td>
                    <td>{sourceBadge(item.source)}</td>
                    <td>
                      <Link to={getLink(item)} className="btn btn-sm">
                        View →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
