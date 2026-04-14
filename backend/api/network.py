"""
BioFusion AI — Network API Route
Protein-protein interaction network from STRING-DB.
"""

import logging

from fastapi import APIRouter, Query
from typing import Optional

from cache_manager import cache
from services import string_db

logger = logging.getLogger("biofusion.api.network")

router = APIRouter()


@router.get("/{gene}")
async def get_network(
    gene: str,
    limit: Optional[int] = Query(20, le=20, description="Max interactions (max 20)"),
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

    try:
        interactions = await string_db.get_interactions(gene, limit=limit or 20)
    except Exception as e:
        logger.error("STRING-DB error: %s", e)
        return {
            "gene": gene,
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
