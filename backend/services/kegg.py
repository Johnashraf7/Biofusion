"""
BioFusion AI — KEGG Service Client
Query KEGG REST API for pathway information.
Rate limited to max 3 requests/second.
"""

import logging
from typing import Any, Dict, List, Optional

from config import API_URLS
from services.base_client import http_client

logger = logging.getLogger("biofusion.services.kegg")

BASE_URL = API_URLS["kegg"]


async def search_gene(gene_name: str) -> List[Dict]:
    """
    Search KEGG for a gene by name.
    Returns matching gene entries for human (hsa).
    """
    url = "{}/find/hsa/{}".format(BASE_URL, gene_name)

    text = await http_client.fetch_text("kegg", url)
    if not text:
        return []

    results = []
    for line in text.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            gene_id = parts[0].strip()
            description = parts[1].strip()
            results.append({
                "kegg_id": gene_id,
                "description": description,
            })

    logger.info("KEGG gene search for '%s': %d results", gene_name, len(results))
    return results[:10]


async def get_gene_pathways(gene_id: str) -> List[Dict]:
    """
    Get pathways for a KEGG gene ID (e.g., hsa:7157).
    Uses the link endpoint.
    """
    url = "{}/link/pathway/{}".format(BASE_URL, gene_id)

    text = await http_client.fetch_text("kegg", url)
    if not text:
        return []

    results = []
    for line in text.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            pathway_id = parts[1].strip()
            results.append({
                "kegg_pathway_id": pathway_id,
            })

    # Fetch pathway names in batch (limited)
    for entry in results[:10]:
        name = await _get_pathway_name(entry["kegg_pathway_id"])
        entry["name"] = name

    logger.info("KEGG pathways for %s: %d found", gene_id, len(results))
    return results[:10]


async def get_pathway(pathway_id: str) -> Optional[Dict]:
    """
    Get pathway details by KEGG pathway ID (e.g. hsa04110).
    """
    url = "{}/get/{}".format(BASE_URL, pathway_id)

    text = await http_client.fetch_text("kegg", url)
    if not text:
        return None

    # Parse the KEGG flat file format
    result = {
        "pathway_id": pathway_id,
        "name": "",
        "description": "",
        "genes": [],
        "compounds": [],
        "diseases": [],
        "url": "https://www.kegg.jp/entry/{}".format(pathway_id),
    }

    current_section = ""
    for line in text.split("\n"):
        if line.startswith("NAME"):
            result["name"] = line.replace("NAME", "").strip()
            # Remove species prefix like " - Homo sapiens (human)"
            if " - " in result["name"]:
                result["name"] = result["name"].split(" - ")[0].strip()
        elif line.startswith("DESCRIPTION"):
            result["description"] = line.replace("DESCRIPTION", "").strip()
        elif line.startswith("GENE"):
            current_section = "GENE"
        elif line.startswith("COMPOUND"):
            current_section = "COMPOUND"
        elif line.startswith("DISEASE"):
            current_section = "DISEASE"
        elif line.startswith("///"):
            break
        elif line.startswith(" ") and not line.startswith("  "):
            # New section
            current_section = ""
        elif line.startswith("            ") or line.startswith("        "):
            # Continuation of current section
            content = line.strip()
            if current_section == "GENE" and len(result["genes"]) < 20:
                result["genes"].append(content)
            elif current_section == "COMPOUND" and len(result["compounds"]) < 10:
                result["compounds"].append(content)
            elif current_section == "DISEASE" and len(result["diseases"]) < 10:
                result["diseases"].append(content)

    logger.info("KEGG pathway detail: %s (%s)", pathway_id, result["name"])
    return result


async def _get_pathway_name(pathway_id: str) -> str:
    """Get just the name of a pathway (lightweight call)."""
    url = "{}/list/{}".format(BASE_URL, pathway_id)

    text = await http_client.fetch_text("kegg", url)
    if not text:
        return ""

    # Format: "hsa04110\tCell cycle - Homo sapiens (human)"
    parts = text.strip().split("\t")
    if len(parts) >= 2:
        name = parts[1].strip()
        if " - " in name:
            name = name.split(" - ")[0].strip()
        return name

    return ""
