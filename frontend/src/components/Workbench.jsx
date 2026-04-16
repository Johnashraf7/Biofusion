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
      const contentWidth = pageWidth - (margin * 2);
      
      // Cover Page
      doc.setFillColor(15, 23, 42);
      doc.rect(0, 0, pageWidth, 40, "F");
      
      doc.setFontSize(24);
      doc.setTextColor(255, 255, 255);
      doc.text("BioFusion Research Dossier", margin, 25);
      
      doc.setFontSize(10);
      doc.setTextColor(200, 200, 200);
      doc.text(`Generated on ${new Date().toLocaleString()}`, margin, 32);

      let y = 55;
      
      // Fetch full details for all items
      const fullDataItems = await Promise.all(pinnedItems.map(async (item) => {
        let details = null;
        let synthesis = null;
        let extra = null;

        try {
          if (item.type === "drug") {
            details = await api.getDrug(item.id);
            extra = await api.getDrugTrials(item.id, details.drug_name);
          } else if (item.type === "gene") {
            details = await api.getGene(item.id);
          } else if (item.type === "disease") {
            details = await api.getDisease(item.id);
          } else if (item.type === "variant") {
            details = await api.getVariant(item.id);
          }
          
          if (details) {
            const synthRes = await api.getSynthesis(item.type, details);
            synthesis = synthRes.synthesis;
          }
        } catch (e) {
          console.error("Error fetching detail for report:", item.id, e);
        }

        return { ...item, details, synthesis, extra };
      }));

      // Table of Contents / Summary
      doc.setFontSize(16);
      doc.setTextColor(15, 23, 42);
      doc.text("Executive Summary", margin, y);
      y += 10;
      
      fullDataItems.forEach((item, i) => {
        if (y > 270) { doc.addPage(); y = 20; }
        doc.setFontSize(11);
        doc.setTextColor(50);
        doc.text(`• [${item.type.toUpperCase()}] ${item.name || item.id}`, margin + 5, y);
        y += 7;
      });

      y += 10;

      // Detailed Pages
      for (const item of fullDataItems) {
        doc.addPage();
        y = 20;
        
        // Header
        doc.setFontSize(18);
        doc.setTextColor(59, 130, 246);
        doc.text(`${item.name || item.id}`, margin, y);
        
        doc.setFontSize(9);
        doc.setTextColor(150);
        doc.text(`${item.type.toUpperCase()} IDENTIFIER: ${item.id}`, margin, y + 5);
        y += 15;

        // AI Synthesis Section
        if (item.synthesis) {
          doc.setFillColor(248, 250, 252);
          doc.rect(margin - 5, y - 5, contentWidth + 10, 35, "F");
          
          doc.setFontSize(12);
          doc.setTextColor(15, 23, 42);
          doc.text("AI Synthesis & Insights", margin, y);
          
          y += 7;
          doc.setFontSize(10);
          doc.setTextColor(71, 85, 105);
          const splitSynth = doc.splitTextToSize(item.synthesis, contentWidth);
          doc.text(splitSynth, margin, y);
          y += (splitSynth.length * 5) + 5;
        }

        // Key Properties
        doc.setFontSize(12);
        doc.setTextColor(15, 23, 42);
        doc.text("Key Characteristics", margin, y);
        y += 7;
        
        doc.setFontSize(10);
        doc.setTextColor(50);
        
        if (item.type === "drug" && item.details) {
          doc.text(`Molecule Type: ${item.details.molecule_type || "N/A"}`, margin, y);
          y += 5;
          doc.text(`Max Phase: ${item.details.max_phase || "0"}`, margin, y);
          y += 5;
          doc.text(`RxCUI: ${item.details.rxcui || "N/A"}`, margin, y);
          y += 5;
          
          // Targets
          if (item.details.targets?.length) {
            y += 5;
            doc.text(`Primary Targets (${item.details.targets.length}):`, margin, y);
            y += 5;
            doc.setFontSize(9);
            item.details.targets.slice(0, 5).forEach(t => {
              doc.text(`- ${t.target_name || t.target_chembl_id}: ${t.action_type || "Unknown Action"}`, margin + 5, y);
              y += 5;
            });
          }
        } else if (item.type === "gene" && item.details) {
          doc.text(`Chromosome: ${item.details.chromosome || "N/A"}`, margin, y);
          y += 5;
          doc.text(`Biotype: ${item.details.biotype || "N/A"}`, margin, y);
          y += 5;
          doc.text(`Full Name: ${item.details.gene_name || "N/A"}`, margin, y);
          y += 5;
        }

        // Clinical Data Summary (for Drugs)
        if (item.extra?.trials?.length) {
            y += 5;
            doc.setFontSize(12);
            doc.setTextColor(15, 23, 42);
            doc.text("Clinical Investigations Summary", margin, y);
            y += 7;
            doc.setFontSize(9);
            doc.setTextColor(50);
            doc.text(`Top ${Math.min(3, item.extra.trials.length)} Clinical Trials:`, margin, y);
            y += 5;
            item.extra.trials.slice(0, 3).forEach(trial => {
                doc.text(`• ${trial.nct_id}: ${trial.title.substring(0, 80)}... [${trial.status}]`, margin + 5, y);
                y += 5;
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
