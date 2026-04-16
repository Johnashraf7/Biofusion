# BioFusion — The High-Fidelity AI Discovery Engine

**A zero-cost, professional-grade bioinformatics platform for drug discovery, genomic analysis, and clinical research.**

BioFusion integrates 10+ biological data sources into a unified, high-performance workbench, featuring AI-driven synthesis and professional research dossiers—all running on a 100% free infrastructure.

---

## 🔥 New in v2.0: The Research Evolution

- **🧬 High-Fidelity Target Resolution**: Advanced recursive fallback in the ChEMBL integration correctly resolves mechanisms for drug salts (e.g., Imatinib Mesylate) to their parent molecules.
- **📄 Professional Research Dossiers**: Direct workbench-to-PDF engine that fetches full scientific profiles, clinical summaries, and AI synthesis for pinned items.
- **🏥 Clinical Investigation Suite**: Real-time integration with ClinicalTrials.gov to fetch active studies, phases, and recruitment status for drug candidates.
- **🧪 AI-Driven Synthesis**: Hybrid AI pipelines (via Pollinations) that summarize complex multi-source data into human-readable dossiers.
- **✨ Premium Clinical Interface**: A sterile clinical aesthetic with glassmorphism components, dark-mode optimization, and enterprise-grade accessibility.

---

## 🛠 Features

| Category | Capability |
|----------|------------|
| **Unified Search** | Intelligent query detection for Gene, Variant, Drug, and Disease types. |
| **Workbench** | Session-persistent item collection for multi-entity research and reporting. |
| **Gene Explorer** | Protein architecture, disease associations, KEGG/Reactome pathways. |
| **Variant Analysis** | ClinVar significance, CADD deleterious scoring, and risk classification. |
| **Discovery Engine** | Molecular properties, recursive mechanism lookups, and primary targets. |
| **Disease Profiling** | ICD-10 mapping, associated genes, and known drug indications. |
| **PPI Network** | Interactive STRING-DB interaction networks via high-performance Canvas2D. |
| **Smart Caching** | Multi-tier file-based TTL cache to maximize speed while respecting API limits. |

---

## 🏗 Architecture

```
biofusion-ai/
├── backend/              FastAPI + Async HTTPX + SQLite + File Cache
│   ├── fusion_engine.py  Data normalization & multi-source merging
│   ├── services/         API interaction layer (10+ sources)
│   │   ├── ai_service.py     AI Synthesis pipeline (Pollinations)
│   │   ├── chembl.py         Recursive target resolver
│   │   ├── clinical_trials.py ClinicalTrials.gov client
│   │   └── ...               (UniProt, Ensembl, STRING-DB, etc.)
│   └── api/              Feature-driven routing
│
├── frontend/             Vite + React + Tailwind + Canvas2D
│   ├── src/components/   BioFusion UI System (Glassmorphism)
│   ├── src/pages/        Scientific detail views & Discovery views
│   └── src/context/      Workbench & Session management
│
└── ...
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.9+** (Backend)
- **Node.js 18+** (Frontend)

### Installation

```bash
# Clone the repository
git clone https://github.com/Johnashraf7/Biofusion.git
cd Biofusion

# 1. Start the Backend Infrastructure
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 2. Launch the High-Fidelity UI (In a new terminal)
cd frontend
npm install
npm run dev
```

Visit **http://localhost:5173** to begin your discovery.

---

## 🔌 API Service Map

| Service | Data Domain |
|---------|-------------|
| **ChEMBL** | Primary Drug Targets & Mechanisms |
| **ClinicalTrials.gov** | Real-time Clinical Investigations |
| **Open Targets** | Genetic Evidence & Disease Associations |
| **Ensembl / UniProt** | Protein Structure & Genomic Context |
| **ClinVar / MyVariant** | Clinical Variant Significance |
| **STRING-DB** | Protein-Protein Interaction Networks |
| **KEGG / Reactome** | Biological Pathway Mapping |
| **Pollinations AI** | Dossier Synthesis & Scientific Summaries |

---

## ⚖️ License
**MIT** — Free for academic, personal, and professional research.
*Note: Individual data sources remain subject to their respective licensing terms.*
