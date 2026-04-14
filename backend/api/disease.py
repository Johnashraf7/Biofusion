"""
BioFusion AI — Disease API Route
Disease information with gene associations, drugs, and ICD-10 mapping.
"""

import asyncio
import logging

from fastapi import APIRouter

from cache_manager import cache
from fusion_engine import merge_disease_data, search_icd10
from services import opentargets

logger = logging.getLogger("biofusion.api.disease")

router = APIRouter()


@router.get("/{disease_id}")
async def get_disease(disease_id: str):
    """
    Get disease profile with gene targets, drugs, and ICD-10 codes.
    
    Args:
        disease_id: EFO ID (e.g., EFO_0000311) or disease name
    """
    # Check cache
    cached = cache.get("disease", disease_id)
    if cached:
        return cached

    warnings = []
    is_efo = disease_id.upper().startswith("EFO_") or disease_id.upper().startswith("MONDO_")

    # Resolve disease ID if needed
    efo_id = disease_id if is_efo else ""
    disease_name = disease_id if not is_efo else ""

    if not is_efo:
        try:
            search_results = await opentargets.search_disease(disease_id, limit=1)
            if search_results:
                efo_id = search_results[0].get("id", "")
                disease_name = search_results[0].get("name", disease_id)
        except Exception:
            warnings.append("Disease search failed")

    # Fetch data in parallel
    targets_task = opentargets.get_disease_targets(efo_id, limit=20) if efo_id else asyncio.sleep(0)
    drugs_task = opentargets.get_disease_drugs(efo_id, limit=10) if efo_id else asyncio.sleep(0)

    results = await asyncio.gather(
        targets_task, drugs_task,
        return_exceptions=True,
    )

    targets_data = results[0] if isinstance(results[0], dict) else None
    drugs_data = results[1] if isinstance(results[1], list) else []

    for i, r in enumerate(results):
        if isinstance(r, Exception):
            source = ["Disease Targets", "Disease Drugs"][i]
            warnings.append("{} lookup failed".format(source))

    # Resolve human-readable disease name from OT response if available
    if not disease_name and targets_data:
        disease_name = targets_data.get("disease_name", "")

    # ICD-10 mapping (local, instant) — uses human-readable name, NOT EFO IDs
    search_term = disease_name if disease_name else disease_id
    icd10_matches = search_icd10(search_term, limit=5)

    # Merge
    merged = merge_disease_data(targets_data, icd10_matches, drugs_data)
    merged["warnings"] = warnings

    if efo_id:
        merged["disease_id"] = efo_id
    if not merged["disease_name"]:
        merged["disease_name"] = disease_name or disease_id

    # Cache
    cache.set("disease", disease_id, merged)

    return merged
