import { useState, useEffect } from "react";
import { api } from "../api/client";
import { Badge } from "./Shared";

export default function AISynthesis({ type, data }) {
  const [synthesis, setSynthesis] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSynthesis = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getSynthesis(type, data);
      setSynthesis(result.synthesis);
    } catch (err) {
      console.error("AISynthesis failed:", err);
      setError("Unable to generate AI synthesis at this time.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (data) fetchSynthesis();
  }, [type, data]);

  return (
    <div className="card ai-synthesis-card" style={{ 
      background: "linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)",
      border: "1px solid rgba(139, 92, 246, 0.3)", // Purple accent for AI
      position: "relative",
      overflow: "hidden"
    }}>
      <div className="card-shine"></div>
      
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <span className="section-title" style={{ margin: 0, fontSize: "0.9rem", color: "#a78bfa" }}>
          <span className="icon">✨</span>
          AI Discovery Synthesis
        </span>
        <Badge variant="glass" style={{ borderColor: "#a78bfa22", color: "#a78bfa" }}>Pollinations-14B</Badge>
      </div>

      {loading ? (
        <div style={{ padding: "1rem 0" }}>
          <div className="skeleton-line" style={{ width: "100%", height: "1rem", marginBottom: "0.8rem" }}></div>
          <div className="skeleton-line" style={{ width: "90%", height: "1rem", marginBottom: "0.8rem" }}></div>
          <div className="skeleton-line" style={{ width: "70%", height: "1rem" }}></div>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "1rem", textAlign: "center" }}>
            Synthesizing biological context...
          </p>
        </div>
      ) : error ? (
        <div style={{ color: "#ef4444", fontSize: "0.85rem", padding: "1rem", textAlign: "center" }}>
          {error}
          <button onClick={fetchSynthesis} className="btn-link" style={{ display: "block", margin: "0.5rem auto", color: "#a78bfa" }}>
            Retry Synthesis
          </button>
        </div>
      ) : (
        <div className="fade-in">
          <p style={{ 
            fontSize: "0.95rem", 
            lineHeight: "1.6", 
            color: "var(--text-primary)", 
            fontStyle: "italic",
            margin: 0 
          }}>
            "{synthesis}"
          </p>
          <div style={{ marginTop: "1rem", fontSize: "0.7rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ color: "#a78bfa" }}>●</span>
            Generated bio-insight based on fused data. Not for primary clinical use.
          </div>
        </div>
      )}

      <style dangerouslySetInnerHTML={{ __html: `
        .ai-synthesis-card:hover {
          border-color: rgba(139, 92, 246, 0.6) !important;
          box-shadow: 0 0 20px rgba(139, 92, 246, 0.1);
        }
        .skeleton-line {
          background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%);
          background-size: 200% 100%;
          border-radius: 4px;
          animation: skeleton-pulse 1.5s infinite;
        }
        @keyframes skeleton-pulse {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
        .card-shine {
          position: absolute;
          top: -50%;
          left: -50%;
          width: 200%;
          height: 200%;
          background: radial-gradient(circle, rgba(139, 92, 246, 0.05) 0%, transparent 70%);
          pointer-events: none;
        }
      `}} />
    </div>
  );
}
