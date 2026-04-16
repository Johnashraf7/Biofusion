"""
BioFusion AI — Network API Route
Protein-protein interaction network from STRING-DB.
"""

import logging

from fastapi import APIRouter, Query
from typing import Optional

from cache_manager import cache
from services import string_db, chembl

logger = logging.getLogger("biofusion.api.network")

router = APIRouter()


@router.get("/{gene}")
async def get_network(
    gene: str,
    symbol: Optional[str] = Query(None, description="Direct gene symbol for search"),
    limit: Optional[int] = Query(40, le=100, description="Max interactions (max 100)"),
):
    """
    Get PPI network for a gene.
    
    Args:
        gene: Gene symbol (e.g., TP53)
        limit: Number of interactions (max 20)
    """
    # Check cache
    cache_key = "{}:{}".format(gene, limit)
    cached = cache.get("network", cache_key)
    if cached:
        return cached

    warnings = []

    # Resolving ID to Symbol if needed
    symbol = gene
    if gene.upper().startswith("CHEMBL"):
        # ChEMBL Target ID -> Symbol
        try:
            target_info = await chembl.search_target(gene, limit=1)
            if target_info and target_info[0].get("gene_symbols"):
                symbol = target_info[0]["gene_symbols"][0]
                logger.info("Resolved target %s to symbol %s", gene, symbol)
        except Exception:
            logger.warning("Failed to resolve target ID %s", gene)
    elif gene.upper().startswith("ENSG"):
        # Ensembl ID -> Symbol
        try:
            gene_data = cache.get("gene", gene)
            if gene_data and gene_data.get("gene_symbol"):
                symbol = gene_data["gene_symbol"]
                logger.info("Resolved ensembl %s to symbol %s from cache", gene, symbol)
        except Exception:
            pass

    try:
        interactions = await string_db.get_interactions(symbol, limit=limit or 20)
    except Exception as e:
        logger.error("STRING-DB error: %s", e)
        return {
            "gene": symbol,
            "interactions": [],
            "graph": {"nodes": [], "edges": [], "node_count": 0},
            "warnings": ["STRING-DB lookup failed: {}".format(str(e))],
        }

    # Build graph data
    graph = string_db.build_graph_data(interactions, gene)

    # Network image URL
    image_url = await string_db.get_network_image_url(gene, limit=limit or 20)

    result = {
        "gene": gene,
        "interaction_count": len(interactions),
        "interactions": interactions,
        "graph": graph,
        "image_url": image_url,
        "warnings": warnings,
    }

    # Cache
    cache.set("network", cache_key, result)

    return result
