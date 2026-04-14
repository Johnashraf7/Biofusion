export function LoadingSpinner({ text = "Loading..." }) {
  return (
    <div className="spinner-container">
      <div className="spinner"></div>
      <span className="spinner-text">{text}</span>
    </div>
  );
}

export function WarningBanner({ warnings }) {
  if (!warnings || warnings.length === 0) return null;
  return (
    <div className="warning-banner">
      <span>⚠</span>
      <div>
        {warnings.map((w, i) => (
          <div key={i}>{w}</div>
        ))}
      </div>
    </div>
  );
}

export function Badge({ children, variant = "blue" }) {
  return <span className={`badge badge-${variant}`}>{children}</span>;
}

export function RiskBadge({ level }) {
  const labels = {
    high: "High Risk",
    moderate: "Moderate Risk",
    low: "Low Risk",
    uncertain: "Uncertain",
  };
  return <span className={`badge risk-${level}`}>{labels[level] || level}</span>;
}

export function ScoreBar({ score, label }) {
  const pct = Math.round(score * 100);
  const level = score >= 0.7 ? "high" : score >= 0.3 ? "moderate" : "low";
  return (
    <span title={label || `Score: ${pct}%`}>
      <span className={`score-bar score-${level}`}>
        <span className="score-bar-fill" style={{ width: `${pct}%` }}></span>
      </span>
      <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{pct}%</span>
    </span>
  );
}

export function DetailRow({ label, value }) {
  if (!value && value !== 0) return null;
  return (
    <div className="detail-row">
      <span className="detail-label">{label}</span>
      <span className="detail-value">{value}</span>
    </div>
  );
}

export function EmptyState({ title, message }) {
  return (
    <div className="empty-state">
      <h3>{title || "No Data"}</h3>
      <p>{message || "No results found."}</p>
    </div>
  );
}
