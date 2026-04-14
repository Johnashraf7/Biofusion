"""
BioFusion AI — RxNorm Service Client
Query NLM RxNorm API for drug normalization and information.
"""

import logging
from typing import Any, Dict, List, Optional

from config import API_URLS
from services.base_client import http_client

logger = logging.getLogger("biofusion.services.rxnorm")

BASE_URL = API_URLS["rxnorm"]


async def search_drug(name: str) -> List[Dict]:
    """
    Search RxNorm for drugs by name.
    Returns matching drug concepts.
    """
    url = "{}/drugs.json".format(BASE_URL)
    params = {"name": name}

    data = await http_client.fetch_json("rxnorm", url, params=params)
    if not data:
        return []

    concepts = data.get("drugGroup", {}).get("conceptGroup", [])
    results = []

    for group in concepts:
        for prop in group.get("conceptProperties", []):
            results.append({
                "rxcui": prop.get("rxcui", ""),
                "name": prop.get("name", ""),
                "synonym": prop.get("synonym", ""),
                "tty": prop.get("tty", ""),  # Term type
            })

    logger.info("RxNorm search for '%s': %d results", name, len(results))
    return results[:10]


async def get_drug_info(rxcui: str) -> Optional[Dict]:
    """
    Get drug properties by RxCUI.
    """
    url = "{}/rxcui/{}/properties.json".format(BASE_URL, rxcui)

    data = await http_client.fetch_json("rxnorm", url)
    if not data:
        return None

    props = data.get("properties", {})
    if not props:
        return None

    result = {
        "rxcui": props.get("rxcui", ""),
        "name": props.get("name", ""),
        "synonym": props.get("synonym", ""),
        "tty": props.get("tty", ""),
        "language": props.get("language", ""),
    }

    logger.info("RxNorm drug info: %s (%s)", rxcui, result["name"])
    return result


async def get_related_drugs(rxcui: str) -> List[Dict]:
    """
    Get related drug concepts (brand names, ingredients, etc.).
    """
    url = "{}/rxcui/{}/related.json".format(BASE_URL, rxcui)
    params = {"tty": "BN+IN+SBD"}  # Brand Name, Ingredient, Semantic Branded Drug

    data = await http_client.fetch_json("rxnorm", url, params=params)
    if not data:
        return []

    results = []
    for group in data.get("relatedGroup", {}).get("conceptGroup", []):
        for prop in group.get("conceptProperties", []):
            results.append({
                "rxcui": prop.get("rxcui", ""),
                "name": prop.get("name", ""),
                "tty": prop.get("tty", ""),
            })

    logger.info("RxNorm related drugs for %s: %d results", rxcui, len(results))
    return results[:10]
