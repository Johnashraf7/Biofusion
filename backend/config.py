"""
BioFusion AI — Configuration
All settings, API base URLs, cache paths, and rate limit constants.
"""

import os
from pathlib import Path
from typing import Dict, List

# ─── Base Paths ───────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = Path(os.getenv("CACHE_DIR", str(BASE_DIR / "cache")))
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "biofusion.db"

# ─── Cache Settings ───────────────────────────────────────────────────────────

CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days
CACHE_CATEGORIES = ["gene", "variant", "drug", "disease", "pathway", "network", "search"]

# ─── HTTP Client Settings ─────────────────────────────────────────────────────

HTTP_TIMEOUT = 30.0          # seconds
HTTP_MAX_CONNECTIONS = 10
HTTP_MAX_RETRIES = 2
HTTP_RETRY_BASE_DELAY = 1.0  # seconds (exponential backoff)

# ─── Rate Limits (minimum delay between calls in seconds) ─────────────────────

RATE_LIMITS: Dict[str, float] = {
    "kegg": 0.334,          # KEGG: max 3 req/sec
    "ensembl": 0.067,       # Ensembl: max 15 req/sec
    "uniprot": 0.1,
    "chembl": 0.1,
    "string_db": 0.2,
    "reactome": 0.1,
    "myvariant": 0.1,
    "opentargets": 0.1,
    "rxnorm": 0.1,
    "default": 0.1,
}

# ─── API Base URLs ─────────────────────────────────────────────────────────────

API_URLS: Dict[str, str] = {
    # Gene → Protein
    "uniprot": "https://rest.uniprot.org",
    "ensembl": "https://rest.ensembl.org",

    # Variant
    "myvariant": "https://myvariant.info/v1",

    # Drug
    "chembl": "https://www.ebi.ac.uk/chembl/api/data",
    "rxnorm": "https://rxnav.nlm.nih.gov/REST",

    # Disease
    "opentargets": "https://api.platform.opentargets.org/api/v4/graphql",

    # Pathways
    "reactome": "https://reactome.org/ContentService",
    "kegg": "https://rest.kegg.jp",

    # Network
    "string_db": "https://string-db.org/api",
}

# ─── STRING-DB Settings ───────────────────────────────────────────────────────

STRING_SPECIES = 9606             # Homo sapiens
STRING_NETWORK_LIMIT = 20        # Max interactions to return
STRING_SCORE_THRESHOLD = 400     # Minimum combined score (0-1000)

# ─── CORS Settings ─────────────────────────────────────────────────────────────

CORS_ORIGINS: List[str] = [
    "http://localhost:5173",      # Vite dev server
    "http://localhost:3000",      # Alternate dev
    "*",                          # Allow all in dev mode
]

# ─── Logging ───────────────────────────────────────────────────────────────────

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
