"""
BioFusion AI — STRING-DB Service Client
Query STRING-DB for protein-protein interaction networks.
Results capped at 20 interactions as per requirements.
"""

import logging
from typing import Any, Dict, List, Optional

from config import API_URLS, STRING_SPECIES, STRING_NETWORK_LIMIT, STRING_SCORE_THRESHOLD
from services.base_client import http_client

logger = logging.getLogger("biofusion.services.string_db")

BASE_URL = API_URLS["string_db"]


async def get_interactions(
    gene_name: str,
    limit: int = STRING_NETWORK_LIMIT,
    score_threshold: int = STRING_SCORE_THRESHOLD,
) -> List[Dict]:
    """
    Get protein-protein interactions for a gene from STRING-DB.
    
    Args:
        gene_name: Gene symbol (e.g., "TP53")
        limit: Max number of interactions (default: 20)
        score_threshold: Minimum combined score 0-1000 (default: 400)
    
    Returns:
        List of interaction dicts with partner info and scores.
    """
    url = "{}/json/network".format(BASE_URL)
    params = {
        "identifiers": gene_name,
        "species": str(STRING_SPECIES),
        "limit": str(limit),
        "required_score": str(score_threshold),
        "caller_identity": "BioFusionAI",
    }

    data = await http_client.fetch_json("string_db", url, params=params)
    if not data or not isinstance(data, list):
        return []

    results = []
    seen_pairs = set()

    for interaction in data:
        # Avoid duplicate pairs (A-B == B-A)
        pair = tuple(sorted([
            interaction.get("preferredName_A", ""),
            interaction.get("preferredName_B", ""),
        ]))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        results.append({
            "protein_a": interaction.get("preferredName_A", ""),
            "protein_b": interaction.get("preferredName_B", ""),
            "string_id_a": interaction.get("stringId_A", ""),
            "string_id_b": interaction.get("stringId_B", ""),
            "score": interaction.get("score", 0),
            "nscore": interaction.get("nscore", 0),        # Neighborhood score
            "fscore": interaction.get("fscore", 0),        # Fusion score
            "pscore": interaction.get("pscore", 0),        # Phylogenetic profile score
            "ascore": interaction.get("ascore", 0),        # Coexpression score
            "escore": interaction.get("escore", 0),        # Experimental score
            "dscore": interaction.get("dscore", 0),        # Database score
            "tscore": interaction.get("tscore", 0),        # Text-mining score
        })

    # Sort by combined score descending
    results.sort(key=lambda x: x.get("score", 0), reverse=True)

    logger.info(
        "STRING-DB interactions for '%s': %d found (limit: %d)",
        gene_name, len(results), limit,
    )
    return results[:limit]


async def get_interaction_partners(
    gene_name: str,
    limit: int = STRING_NETWORK_LIMIT,
) -> List[Dict]:
    """
    Get interaction partners for a gene (simplified format).
    """
    url = "{}/json/interaction_partners".format(BASE_URL)
    params = {
        "identifiers": gene_name,
        "species": str(STRING_SPECIES),
        "limit": str(limit),
        "caller_identity": "BioFusionAI",
    }

    data = await http_client.fetch_json("string_db", url, params=params)
    if not data or not isinstance(data, list):
        return []

    results = []
    for partner in data:
        results.append({
            "query_gene": partner.get("preferredName_A", ""),
            "partner_gene": partner.get("preferredName_B", ""),
            "score": partner.get("score", 0),
        })

    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    logger.info("STRING-DB partners for '%s': %d found", gene_name, len(results))
    return results[:limit]


async def get_network_image_url(
    gene_name: str,
    limit: int = STRING_NETWORK_LIMIT,
) -> Optional[str]:
    """
    Get the URL for a STRING-DB network visualization image.
    """
    url = (
        "{}/image/network"
        "?identifiers={}"
        "&species={}"
        "&limit={}"
        "&caller_identity=BioFusionAI"
    ).format(BASE_URL, gene_name, STRING_SPECIES, limit)

    return url


def build_graph_data(interactions: List[Dict], center_gene: str) -> Dict:
    """
    Transform STRING-DB interactions into a graph-compatible format.
    
    Returns:
        Dict with "nodes" and "edges" suitable for frontend rendering.
    """
    nodes = {}
    edges = []

    # Add center node
    nodes[center_gene] = {
        "id": center_gene,
        "label": center_gene,
        "type": "center",
    }

    for interaction in interactions:
        prot_a = interaction.get("protein_a", "")
        prot_b = interaction.get("protein_b", "")
        score = interaction.get("score", 0)

        # Add nodes
        if prot_a and prot_a not in nodes:
            nodes[prot_a] = {
                "id": prot_a,
                "label": prot_a,
                "type": "partner",
            }
        if prot_b and prot_b not in nodes:
            nodes[prot_b] = {
                "id": prot_b,
                "label": prot_b,
                "type": "partner",
            }

        # Add edge
        if prot_a and prot_b:
            edges.append({
                "source": prot_a,
                "target": prot_b,
                "weight": score,
            })

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "center": center_gene,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }
