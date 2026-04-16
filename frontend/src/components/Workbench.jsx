import React, { useState } from "react";
import { useWorkbench } from "../context/WorkbenchContext";
import { Badge } from "./Shared";
import { Link } from "react-router-dom";
import api from "../api/client";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

export default function Workbench() {
  const { pinnedItems, togglePin, clearWorkbench } = useWorkbench();
  const [isOpen, setIsOpen] = useState(false);
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    if (pinnedItems.length === 0) return;
    setExporting(true);
    
      try {
      const doc = new jsPDF("p", "mm", "a4");
      const pageWidth = doc.internal.pageSize.getWidth();
      const margin = 20;
      const contentWidth = pageWidth - (margin * 2) - 5; // Extra padding
      let y = 55;

      // --- Centralized PDF Engine v3 (Indestructible) ---
      const addWrappedText = (text, options = {}) => {
        const { 
          fontSize = 10, 
          isBold = false, 
          color = [51, 65, 85], 
          indent = 0, 
          afterGap = 3
        } = options;

        // SANITIZE: Aggressive ASCII cleaning + normalize unbreakable strings
        let cleanText = text.toString()
            .replace(/[\u2018\u2019]/g, "'").replace(/[\u201C\u201D]/g, '"')
            .replace(/[\u2013\u2014]/g, "-").replace(/[^\x00-\x7F]/g, "")
            .replace(/\*\*/g, "").replace(/\*/g, "").replace(/#/g, "")
            .replace(/[ \t]+/g, " ").trim();

        if (!cleanText) return;

        // Hard character wrapping guard (detect long unbreakable strings like RSIDs/Sequences)
        const words = cleanText.split(" ");
        const processedWords = words.map(word => {
            if (word.length > 35) return word.match(/.{1,35}/g).join(" "); // break massive strings
            return word;
        });
        cleanText = processedWords.join(" ");

        doc.setFont("helvetica", isBold ? "bold" : "normal");
        doc.setFontSize(fontSize);
        doc.setTextColor(color[0], color[1], color[2]);

        const lines = doc.splitTextToSize(cleanText, contentWidth - indent);
        lines.forEach(line => {
          if (y > 270) {
            doc.addPage();
            y = 25;
            // Immediate re-bind
            doc.setFont("helvetica", isBold ? "bold" : "normal");
            doc.setFontSize(fontSize);
            doc.setTextColor(color[0], color[1], color[2]);
          }
          doc.text(line, margin + indent, y);
          y += (fontSize * 0.45); // Tighter but safe line height
        });
        y += afterGap;
      };

      // Cover Page
      doc.setFillColor(15, 23, 42);
      doc.rect(0, 0, pageWidth, 40, "F");
      doc.setFont("times", "bold");
      doc.setFontSize(24);
      doc.setTextColor(255, 255, 255);
      doc.text("BioFusion Research Dossier", margin, 25);
      doc.setFont("times", "normal");
      doc.setFontSize(10);
      doc.setTextColor(200, 200, 200);
      doc.text(`Generated on ${new Date().toLocaleString()}`, margin, 32);

      // Fetch full details
      const fullDataItems = await Promise.all(pinnedItems.map(async (item) => {
        let details = null, synthesis = null, extra = null;
        try {
          if (item.type === "drug") {
            details = await api.getDrug(item.id);
            extra = await api.getDrugTrials(item.id, details.drug_name);
          } else if (item.type === "gene") details = await api.getGene(item.id);
          else if (item.type === "disease") details = await api.getDisease(item.id);
          else if (item.type === "variant") details = await api.getVariant(item.id);
          
          if (details) {
            const synthRes = await api.getSynthesis(item.type, details);
            synthesis = synthRes.synthesis;
          }
        } catch (e) { console.error("Fetch Error:", item.id, e); }
        return { ...item, details, synthesis, extra };
      }));

      // Executive Summary
      addWrappedText("Executive Summary", { fontSize: 16, isBold: true, color: [15, 23, 42], afterGap: 5 });
      fullDataItems.forEach(item => {
        addWrappedText(`• [${item.type.toUpperCase()}] ${item.name || item.id}`, { indent: 5 });
      });
      y += 10;

      // Detailed Pages
      for (const item of fullDataItems) {
        doc.addPage();
        y = 25;
        
        // Item Header
        addWrappedText(item.name || item.id, { fontSize: 20, isBold: true, color: [59, 130, 246] });
        addWrappedText(`${item.type.toUpperCase()} IDENTIFIER: ${item.id}`, { fontSize: 10, color: [100, 116, 139], afterGap: 8 });

        // AI Synthesis
        if (item.synthesis) {
          addWrappedText("AI Synthesis & Insights", { fontSize: 14, isBold: true, color: [15, 23, 42], afterGap: 2 });
          item.synthesis.split("\n\n").forEach(para => {
            addWrappedText(para, { fontSize: 11, afterGap: 4 });
          });
          y += 5;
        }

        // Key Characteristics
        addWrappedText("Key Characteristics", { fontSize: 14, isBold: true, color: [15, 23, 42], afterGap: 2 });
        if (item.type === "drug" && item.details) {
          addWrappedText(`Molecule Type: ${item.details.molecule_type || "N/A"}`);
          addWrappedText(`Max Phase: ${item.details.max_phase || "0"}`);
          addWrappedText(`RxCUI: ${item.details.rxcui || "N/A"}`);
          
          if (item.details.targets?.length) {
            y += 4;
            addWrappedText(`Primary Targets (${item.details.targets.length}):`, { isBold: true });
            item.details.targets.slice(0, 5).forEach(t => {
              addWrappedText(`- ${t.target_name || t.target_chembl_id}: ${t.action_type || "Unknown"}`, { indent: 5, fontSize: 10 });
            });
          }
        } else if (item.type === "gene" && item.details) {
          addWrappedText(`Chromosome: ${item.details.chromosome || "N/A"}`);
          addWrappedText(`Biotype: ${item.details.biotype || "N/A"}`);
          addWrappedText(`Full Name: ${item.details.gene_name || "N/A"}`);
        } else if (item.type === "disease" && item.details) {
            addWrappedText(`Categories: ${item.details.categories?.join(", ") || "N/A"}`);
        }

        // Clinical Data
        if (item.extra?.trials?.length) {
          y += 5;
          addWrappedText("Clinical Investigations Summary", { fontSize: 13, isBold: true, color: [15, 23, 42], afterGap: 2 });
          addWrappedText(`Top ${Math.min(3, item.extra.trials.length)} Clinical Trials:`, { fontSize: 9.5, afterGap: 1 });
          item.extra.trials.slice(0, 3).forEach(trial => {
            addWrappedText(`• ${trial.nct_id}: ${trial.title} [${trial.status}]`, { indent: 5, fontSize: 9.5 });
          });
        }
      }

      doc.save(`BioFusion_Research_Dossier_${new Date().toISOString().split('T')[0]}.pdf`);
    } catch (err) {
      console.error("Dossier Generation Failed:", err);
      confirm("Failed to generate dossier. Please check console for errors.");
    } finally {
      setExporting(false);
    }
  };

  if (!isOpen) {
    return (
      <button 
        onClick={() => setIsOpen(true)}
        className="workbench-trigger"
        style={{
          position: "fixed",
          bottom: "2rem",
          right: "2rem",
          width: "60px",
          height: "60px",
          borderRadius: "50%",
          background: "var(--accent-blue)",
          border: "none",
          boxShadow: "0 10px 25px rgba(59, 130, 246, 0.4)",
          color: "white",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000,
          transition: "transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)"
        }}
        onMouseEnter={(e) => e.target.style.transform = "scale(1.1)"}
        onMouseLeave={(e) => e.target.style.transform = "scale(1)"}
      >
        <span style={{ fontSize: "1.5rem" }}>📁</span>
        {pinnedItems.length > 0 && (
          <span style={{
            position: "absolute",
            top: 0,
            right: 0,
            background: "#ef4444",
            color: "white",
            fontSize: "0.75rem",
            width: "20px",
            height: "20px",
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: "bold",
            border: "2px solid white"
          }}>
            {pinnedItems.length}
          </span>
        )}
      </button>
    );
  }

  return (
    <div className="workbench-panel fade-in" style={{
      position: "fixed",
      bottom: "2rem",
      right: "2rem",
      width: "350px",
      maxHeight: "500px",
      background: "rgba(15, 23, 42, 0.95)",
      backdropFilter: "blur(12px)",
      border: "1px solid var(--accent-blue-alpha)",
      borderRadius: "16px",
      boxShadow: "0 20px 50px rgba(0,0,0,0.5)",
      zIndex: 1001,
      display: "flex",
      flexDirection: "column",
      overflow: "hidden"
    }}>
      <div className="workbench-header" style={{
        padding: "1rem",
        borderBottom: "1px solid var(--border-color)",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        background: "rgba(59, 130, 246, 0.1)"
      }}>
        <h3 style={{ margin: 0, fontSize: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span>🧪</span> Discovery Workbench
        </h3>
        <button 
          onClick={() => setIsOpen(false)}
          style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "1.2rem" }}
        >
          &times;
        </button>
      </div>

      <div className="workbench-content" style={{ padding: "1rem", overflowY: "auto", flex: 1 }}>
        {pinnedItems.length === 0 ? (
          <div style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)" }}>
            <p style={{ fontSize: "2rem", marginBottom: "1rem" }}>📥</p>
            <p>Your workbench is empty. Pin items to collect them for reporting.</p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {pinnedItems.map((item) => (
              <div key={`${item.type}-${item.id}`} className="workbench-item card" style={{ padding: "0.75rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <Badge variant="blue" style={{ fontSize: "0.6rem" }}>{item.type.toUpperCase()}</Badge>
                    <Link to={`/${item.type}/${item.id}`} style={{ fontWeight: 600, fontSize: "0.9rem", color: "var(--text-primary)" }}>
                      {item.id}
                    </Link>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
                    {item.name}
                  </div>
                </div>
                <button 
                  onClick={() => togglePin(item)}
                  style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer", fontSize: "0.9rem" }}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="workbench-footer" style={{ padding: "1rem", borderTop: "1px solid var(--border-color)", display: "flex", gap: "0.5rem" }}>
        <button 
          className="btn btn-primary" 
          style={{ flex: 1 }} 
          disabled={pinnedItems.length === 0 || exporting}
          onClick={handleExport}
        >
          {exporting ? "Generating..." : "Export Report (PDF)"}
        </button>
        <button 
          className="btn-glass" 
          onClick={clearWorkbench} 
          disabled={pinnedItems.length === 0}
          style={{ color: "#ef4444" }}
        >
          Clear
        </button>
      </div>
    </div>
  );
}
