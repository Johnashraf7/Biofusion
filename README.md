# BioFusion AI — Free Edition

**Zero-cost bioinformatics data fusion platform.**

Search genes, variants, drugs, and diseases across 9 free biological APIs — UniProt, Ensembl, ClinVar (via MyVariant.info), ChEMBL, RxNorm, Open Targets, Reactome, KEGG, and STRING-DB.

---

## Features

| Feature | Description |
|---------|-------------|
| **Unified Search** | Auto-detects query type (gene / variant / drug / disease) |
| **Gene Explorer** | Protein info, disease associations, pathways (lazy loaded) |
| **Variant Analysis** | ClinVar significance + CADD scoring + risk classification |
| **Drug Lookup** | Molecular properties, mechanisms, gene targets |
| **Disease Profiling** | Associated genes, known drugs, ICD-10 code mapping |
| **PPI Network** | STRING-DB interactions ≤20 nodes with Canvas2D visualization |
| **File-Based Cache** | 7-day TTL, per-category JSON cache — zero paid infrastructure |
| **Rate Limiting** | Per-service async rate limiter to prevent API bans |
| **Retry Logic** | 2 retries with exponential backoff on all external calls |
| **Partial Responses** | Returns available data + warnings if any API fails |

---

## Architecture

```
biofusion-ai/
├── backend/              FastAPI + httpx + SQLite + file cache
│   ├── main.py           App entry point + lifespan
│   ├── config.py         All settings & API URLs
│   ├── database.py       SQLite search history
│   ├── cache_manager.py  File-based TTL cache
│   ├── fusion_engine.py  Data merge, normalize, score
│   ├── services/         9 API client modules
│   │   ├── base_client.py    Shared httpx + retry + rate limit
│   │   ├── uniprot.py        Gene → Protein
│   │   ├── ensembl.py        Gene lookup + IDs
│   │   ├── myvariant.py      Variant annotation (ClinVar/CADD)
│   │   ├── chembl.py         Drug search + targets
│   │   ├── rxnorm.py         Drug normalization
│   │   ├── opentargets.py    Disease associations (GraphQL)
│   │   ├── reactome.py       Pathways
│   │   ├── kegg.py           Pathways (text API)
│   │   └── string_db.py      PPI network
│   ├── api/              6 route modules
│   │   ├── search.py     /search?q=
│   │   ├── gene.py       /gene/{id}
│   │   ├── variant.py    /variant/{id}
│   │   ├── drug.py       /drug/{id}
│   │   ├── disease.py    /disease/{id}
│   │   └── network.py    /network/{gene}
│   └── data/
│       └── icd10_codes.json  182 curated ICD-10 codes
│
├── frontend/             React + Vite
│   └── src/
│       ├── App.jsx       Routing + navbar
│       ├── index.css     Dark bioinformatics design system
│       ├── api/client.js Backend API wrapper
│       ├── components/   Shared UI components
│       └── pages/        Explorer, Gene, Variant, Drug, Disease, Network
│
├── Dockerfile            Backend container
├── render.yaml           Render free-tier blueprint
└── .gitignore
```

---

## Quick Start

### Prerequisites
- Python 3.7+ (backend)
- Node.js 18+ (frontend)

### Run Locally

```bash
# 1. Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/search?q={query}&type={gene\|variant\|drug\|disease}` | Unified search |
| GET | `/gene/{id}?include=pathways,kegg` | Gene report |
| GET | `/variant/{id}` | Variant annotation |
| GET | `/drug/{id}` | Drug details + targets |
| GET | `/disease/{id}` | Disease profile + ICD-10 |
| GET | `/network/{gene}?limit=20` | PPI network |
| GET | `/health` | Health check |
| GET | `/stats` | System statistics |
| GET | `/docs` | Swagger UI |

---

## Deploy (Free Tier)

### Backend → Render
1. Push to GitHub
2. Connect repo on [render.com](https://render.com)
3. Use the included `render.yaml` blueprint
4. Set root directory to `backend`

### Frontend → Vercel
1. Connect repo on [vercel.com](https://vercel.com)
2. Set root directory to `frontend`
3. Add env var: `VITE_API_URL=https://your-render-url.onrender.com`
4. Deploy

---

## Constraints Honored

- ✅ NO paid APIs
- ✅ NO paid databases (SQLite only)
- ✅ NO Redis
- ✅ NO PostgreSQL
- ✅ NO OMIM
- ✅ File-based caching with TTL
- ✅ Rate limit protection on all APIs
- ✅ Network graph ≤20 nodes
- ✅ Lazy loading for pathways
- ✅ Partial data + warnings on API failure

---

## License

MIT — Free for academic and personal use. Individual API data sources have their own terms.
