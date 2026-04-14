"""
BioFusion — FastAPI Application Entry Point
Free Edition Bioinformatics Data Fusion Platform
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, LOG_LEVEL
from database import db
from cache_manager import cache
from services.base_client import http_client
from fusion_engine import load_icd10

# ─── Logging Setup ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(name)-24s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("biofusion")


# ─── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle manager."""
    # ── Startup ──
    logger.info("=" * 60)
    logger.info("  BioFusion - Free Edition v1.0.0")
    logger.info("  Starting up...")
    logger.info("=" * 60)

    await db.connect()
    await http_client.start()
    load_icd10()

    # Clean expired cache on startup
    expired = cache.clear_expired()
    if expired:
        logger.info("Cleaned %d expired cache entries", expired)

    cache_stats = cache.get_stats()
    logger.info("Cache stats: %s", cache_stats)
    logger.info("BioFusion is ready!")

    yield

    # ── Shutdown ──
    logger.info("Shutting down BioFusion...")
    await http_client.stop()
    await db.disconnect()
    logger.info("Shutdown complete.")


# ─── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="BioFusion",
    description=(
        "Free-tier bioinformatics data fusion platform. "
        "Integrates UniProt, Ensembl, ClinVar, ChEMBL, Open Targets, "
        "Reactome, KEGG, STRING-DB and more."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS Middleware ───────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ──────────────────────────────────────────────────────────────

@app.get("/", tags=["system"])
async def root():
    """Root endpoint - service info."""
    return {
        "service": "BioFusion",
        "version": "1.0.0",
        "edition": "Free",
        "status": "running",
        "endpoints": {
            "search": "/search?q={query}",
            "gene": "/gene/{id}",
            "variant": "/variant/{id}",
            "drug": "/drug/{id}",
            "disease": "/disease/{id}",
            "network": "/network/{gene}",
        },
    }


@app.get("/health", tags=["system"])
async def health_check():
    """Health check with cache and DB status."""
    return {
        "status": "healthy",
        "cache": cache.get_stats(),
        "database": "connected",
    }


@app.get("/stats", tags=["system"])
async def system_stats():
    """System statistics."""
    search_stats = await db.get_search_stats()
    return {
        "cache": cache.get_stats(),
        "searches": search_stats,
    }


# ─── Register API Routers ─────────────────────────────────────────────────────

from api.search import router as search_router
from api.gene import router as gene_router
from api.variant import router as variant_router
from api.drug import router as drug_router
from api.disease import router as disease_router
from api.network import router as network_router

app.include_router(search_router, prefix="/search", tags=["search"])
app.include_router(gene_router, prefix="/gene", tags=["gene"])
app.include_router(variant_router, prefix="/variant", tags=["variant"])
app.include_router(drug_router, prefix="/drug", tags=["drug"])
app.include_router(disease_router, prefix="/disease", tags=["disease"])
app.include_router(network_router, prefix="/network", tags=["network"])
