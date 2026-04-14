"""
BioFusion AI — Reactome Service Client
Query Reactome Content Service for pathway information.
"""

import logging
from typing import Any, Dict, List, Optional

from config import API_URLS
from services.base_client import http_client

logger = logging.getLogger("biofusion.services.reactome")

BASE_URL = API_URLS["reactome"]


async def get_pathways(gene_name: str) -> List[Dict]:
    """
    Get pathways associated with a gene/protein.
    Uses the Reactome search endpoint.
    """
    # First, search for the entity
    url = "{}/search/query".format(BASE_URL)
    params = {
        "query": gene_name,
        "types": "Pathway",
        "species": "Homo sapiens",
        "cluster": "true",
    }

    data = await http_client.fetch_json("reactome", url, params=params)
    if not data or "results" not in data:
        return []

    results = []
    for group in data.get("results", []):
        for entry in group.get("entries", []):
            results.append({
                "pathway_id": entry.get("stId", ""),
                "name": entry.get("name", ""),
                "species": entry.get("species", [""])[0] if entry.get("species") else "",
                "summary": entry.get("summation", [""])[0] if entry.get("summation") else "",
                "is_disease": entry.get("isDisease", False),
            })

    logger.info("Reactome pathways for '%s': %d found", gene_name, len(results))
    return results[:15]  # Limit results


async def get_pathway_detail(pathway_id: str) -> Optional[Dict]:
    """
    Get detailed pathway information by Reactome stable ID (e.g. R-HSA-109582).
    """
    url = "{}/data/pathway/{}/containedEvents".format(BASE_URL, pathway_id)

    events = await http_client.fetch_json("reactome", url)

    # Also get the pathway summary
    summary_url = "{}/data/query/{}".format(BASE_URL, pathway_id)
    summary_data = await http_client.fetch_json("reactome", summary_url)

    if not summary_data:
        return None

    # Extract contained events/reactions
    contained = []
    if events and isinstance(events, list):
        for ev in events[:20]:
            contained.append({
                "id": ev.get("stId", ""),
                "name": ev.get("displayName", ""),
                "type": ev.get("schemaClass", ""),
            })

    result = {
        "pathway_id": summary_data.get("stId", ""),
        "name": summary_data.get("displayName", ""),
        "species": summary_data.get("speciesName", ""),
        "is_disease": summary_data.get("isInDisease", False),
        "diagram_available": summary_data.get("hasDiagram", False),
        "contained_events": contained,
        "diagram_url": "https://reactome.org/PathwayBrowser/#/{}".format(pathway_id),
    }

    logger.info("Reactome pathway detail: %s (%s)", pathway_id, result["name"])
    return result


async def get_pathways_for_entity(identifier: str) -> List[Dict]:
    """
    Get pathways involving a specific entity (gene/protein/molecule).
    Uses the pathways endpoint with a direct identifier lookup.
    """
    url = "{}/data/pathways/low/entity/{}".format(BASE_URL, identifier)
    params = {"species": "9606"}  # Homo sapiens

    data = await http_client.fetch_json("reactome", url)
    if not data or not isinstance(data, list):
        return []

    results = []
    for pathway in data:
        results.append({
            "pathway_id": pathway.get("stId", ""),
            "name": pathway.get("displayName", ""),
            "species": pathway.get("speciesName", ""),
            "is_disease": pathway.get("isInDisease", False),
        })

    logger.info("Reactome entity pathways for '%s': %d found", identifier, len(results))
    return results[:15]
