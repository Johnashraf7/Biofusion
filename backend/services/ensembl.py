"""
BioFusion AI — Ensembl Service Client
Query Ensembl REST API for gene information and ID lookups.
"""

import logging
from typing import Any, Dict, List, Optional

from config import API_URLS
from services.base_client import http_client

logger = logging.getLogger("biofusion.services.ensembl")

BASE_URL = API_URLS["ensembl"]


async def lookup_gene(symbol: str, species: str = "homo_sapiens") -> Optional[Dict]:
    """
    Look up a gene by symbol (e.g., BRCA1, TP53).
    Returns gene metadata including Ensembl ID, location, and biotype.
    """
    url = "{}/lookup/symbol/{}/{}".format(BASE_URL, species, symbol)
    headers = {"Content-Type": "application/json"}

    data = await http_client.fetch_json("ensembl", url, headers=headers)
    if not data:
        return None

    result = {
        "ensembl_id": data.get("id", ""),
        "display_name": data.get("display_name", ""),
        "description": data.get("description", ""),
        "biotype": data.get("biotype", ""),
        "species": data.get("species", ""),
        "chromosome": data.get("seq_region_name", ""),
        "start": data.get("start", 0),
        "end": data.get("end", 0),
        "strand": data.get("strand", 0),
        "assembly": data.get("assembly_name", ""),
        "source": data.get("source", ""),
    }

    logger.info("Ensembl gene lookup: %s -> %s", symbol, result["ensembl_id"])
    return result


async def get_gene_by_id(ensembl_id: str) -> Optional[Dict]:
    """
    Get gene details by Ensembl stable ID (e.g., ENSG00000141510).
    """
    url = "{}/lookup/id/{}".format(BASE_URL, ensembl_id)
    headers = {"Content-Type": "application/json"}
    params = {"expand": "1"}

    data = await http_client.fetch_json("ensembl", url, params=params, headers=headers)
    if not data:
        return None

    # Extract transcript info if available
    transcripts = []
    for tr in data.get("Transcript", []):
        transcripts.append({
            "id": tr.get("id", ""),
            "display_name": tr.get("display_name", ""),
            "biotype": tr.get("biotype", ""),
            "length": tr.get("length", 0),
            "is_canonical": tr.get("is_canonical", 0) == 1,
        })

    result = {
        "ensembl_id": data.get("id", ""),
        "display_name": data.get("display_name", ""),
        "description": data.get("description", ""),
        "biotype": data.get("biotype", ""),
        "species": data.get("species", ""),
        "chromosome": data.get("seq_region_name", ""),
        "start": data.get("start", 0),
        "end": data.get("end", 0),
        "strand": data.get("strand", 0),
        "assembly": data.get("assembly_name", ""),
        "transcripts": transcripts[:10],  # Limit transcripts
    }

    logger.info("Ensembl gene by ID: %s (%s)", ensembl_id, result["display_name"])
    return result


async def search_genes(query: str, species: str = "homo_sapiens", limit: int = 10) -> List[Dict]:
    """
    Search Ensembl for genes matching a query string.
    Uses the xrefs endpoint for flexible searching.
    """
    url = "{}/xrefs/symbol/{}/{}".format(BASE_URL, species, query)
    headers = {"Content-Type": "application/json"}

    data = await http_client.fetch_json("ensembl", url, headers=headers)
    if not data or not isinstance(data, list):
        return []

    results = []
    for entry in data[:limit]:
        if entry.get("type") == "gene":
            results.append({
                "ensembl_id": entry.get("id", ""),
                "type": entry.get("type", ""),
            })

    logger.info("Ensembl search for '%s': %d gene results", query, len(results))
    return results
