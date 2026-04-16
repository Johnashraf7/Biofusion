"""
BioFusion AI — Drug API Route
Drug information with targets and mechanisms.
"""

import asyncio
import logging

from fastapi import APIRouter, Query
from typing import List, Optional

from cache_manager import cache
from fusion_engine import merge_drug_data
from services import chembl, rxnorm, clinical_trials

logger = logging.getLogger("biofusion.api.drug")

router = APIRouter()


@router.get("/{drug_id}")
async def get_drug(drug_id: str):
    """
    Get drug details with targets.
    
    Args:
        drug_id: ChEMBL ID (e.g., CHEMBL25) or drug name (e.g., imatinib)
    """
    # Check cache
    cached = cache.get("drug", drug_id)
    if cached:
        return cached

    warnings = []
    is_chembl = drug_id.upper().startswith("CHEMBL")

    # Resolve ChEMBL ID if needed
    chembl_id = drug_id if is_chembl else ""
    if not is_chembl:
        try:
            search_results = await chembl.search_drug(drug_id, limit=1)
            if search_results:
                chembl_id = search_results[0].get("chembl_id", "")
        except Exception:
            warnings.append("ChEMBL search failed")

    # Fetch data in parallel
    chembl_task = chembl.get_drug(chembl_id) if chembl_id else asyncio.sleep(0)
    targets_task = chembl.get_drug_targets(chembl_id) if chembl_id else asyncio.sleep(0)
    rxnorm_task = rxnorm.search_drug(drug_id if not is_chembl else "")

    results = await asyncio.gather(
        chembl_task, targets_task, rxnorm_task,
        return_exceptions=True,
    )

    chembl_data = results[0] if isinstance(results[0], dict) else None
    targets_data = results[1] if isinstance(results[1], list) else []
    rxnorm_results = results[2] if isinstance(results[2], list) else []

    # Get RxNorm details if we got results
    rxnorm_data = None
    if rxnorm_results:
        rxcui = rxnorm_results[0].get("rxcui", "")
        if rxcui:
            try:
                rxnorm_data = await rxnorm.get_drug_info(rxcui)
            except Exception:
                warnings.append("RxNorm detail fetch failed")

    # Handle errors in gather results
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            source = ["ChEMBL", "ChEMBL Targets", "RxNorm"][i]
            warnings.append("{} lookup failed".format(source))

    # Merge data
    merged = merge_drug_data(chembl_data, rxnorm_data, targets_data)
    merged["warnings"] = warnings

    if not merged["drug_name"]:
        merged["drug_name"] = drug_id

    # Cache
    cache.set("drug", drug_id, merged)

    return merged


@router.get("/{drug_id}/trials")
async def get_drug_trials(
    drug_id: str,
    query: Optional[str] = Query(None, description="Direct drug name for search")
):
    """
    Get clinical trials for a drug.
    Uses the provided query (name) if available, otherwise resolves drug_id.
    """
    search_term = query or drug_id
    
    # If no direct query and is ChEMBL ID, try to resolve
    if not query and drug_id.upper().startswith("CHEMBL"):
        drug_data = cache.get("drug", drug_id)
        if drug_data and drug_data.get("drug_name"):
            search_term = drug_data["drug_name"]
        else:
            try:
                details = await chembl.get_drug(drug_id)
                if details and details.get("pref_name"):
                    search_term = details["pref_name"]
            except Exception:
                pass

    logger.info("Drug Trials Request: ID=%s, Query=%s -> SearchTerm=%s", drug_id, query, search_term)
    trials = await clinical_trials.get_clinical_trials(search_term)
    return {"trials": trials}
