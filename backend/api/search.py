"""
BioFusion AI — Search API Route
Unified search endpoint with auto-detection and multi-source querying.
"""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Query

from cache_manager import cache
from database import db
from fusion_engine import detect_query_type
from services import ensembl, uniprot, opentargets, chembl, myvariant, rxnorm

logger = logging.getLogger("biofusion.api.search")

router = APIRouter()


@router.get("")
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    type: Optional[str] = Query(None, description="Query type: gene, variant, drug, disease"),
):
    """
    Unified search endpoint.
    Auto-detects query type if not specified.
    """
    query = q.strip()
    query_type = type if type else detect_query_type(query)

    # Check cache
    cache_key = "{}:{}".format(query_type, query)
    cached = cache.get("search", cache_key)
    if cached:
        await db.log_search(query, query_type, len(cached.get("results", [])), cached=True)
        return cached

    results = []
    warnings = []

    try:
        if query_type == "gene":
            results, warnings = await _search_gene(query)
        elif query_type == "variant":
            results, warnings = await _search_variant(query)
        elif query_type == "drug":
            results, warnings = await _search_drug(query)
        elif query_type == "disease":
            results, warnings = await _search_disease(query)
        else:
            results, warnings = await _search_gene(query)

        # ─── Fallback Logic ──────────────────────────────────────────────────
        # If no results found for auto-detected type, try other logical types
        if not results and not type:
            logger.info("No results for detected type '%s', trying fallback...", query_type)
            
            fallback_types = ["disease", "drug", "gene"]
            if query_type in fallback_types:
                fallback_types.remove(query_type)

            for fb_type in fallback_types:
                logger.debug("Trying fallback: %s", fb_type)
                fb_results = []
                fb_warnings = []
                
                if fb_type == "disease":
                    fb_results, fb_warnings = await _search_disease(query)
                elif fb_type == "drug":
                    fb_results, fb_warnings = await _search_drug(query)
                elif fb_type == "gene":
                    fb_results, fb_warnings = await _search_gene(query)
                
                if fb_results:
                    results = fb_results
                    warnings.extend(fb_warnings)
                    query_type = fb_type
                    logger.info("Fallback found results for type: %s", fb_type)
                    break

    except Exception as e:
        logger.error("Search error: %s", e)
        warnings.append("Search encountered an error: {}".format(str(e)))

    response = {
        "query": query,
        "type": query_type,
        "result_count": len(results),
        "results": results,
        "warnings": warnings,
    }

    # Cache the results
    cache.set("search", cache_key, response)
    await db.log_search(query, query_type, len(results), cached=False)

    return response


async def _search_gene(query):
    """Search for genes across Ensembl, UniProt, and Open Targets."""
    warnings = []
    tasks = [
        ensembl.lookup_gene(query),
        uniprot.search_gene(query, limit=3),
        opentargets.search_target(query, limit=3),
    ]

    ensembl_result, uniprot_results, ot_results = await asyncio.gather(
        *tasks, return_exceptions=True
    )

    results = []

    # Ensembl result
    if isinstance(ensembl_result, dict) and ensembl_result:
        results.append({
            "id": ensembl_result.get("ensembl_id", query),
            "name": ensembl_result.get("display_name", query),
            "description": ensembl_result.get("description", ""),
            "type": "gene",
            "source": "Ensembl",
            "chromosome": ensembl_result.get("chromosome", ""),
        })
    elif isinstance(ensembl_result, Exception):
        warnings.append("Ensembl search failed")

    # UniProt results
    if isinstance(uniprot_results, list):
        for up in uniprot_results:
            results.append({
                "id": up.get("accession", ""),
                "name": up.get("gene_names", [query])[0] if up.get("gene_names") else query,
                "description": up.get("protein_name", ""),
                "type": "gene",
                "source": "UniProt",
            })
    elif isinstance(uniprot_results, Exception):
        warnings.append("UniProt search failed")

    # Open Targets results
    if isinstance(ot_results, list):
        for ot in ot_results:
            # Avoid duplicates
            existing_ids = {r["id"] for r in results}
            if ot.get("id") not in existing_ids:
                results.append({
                    "id": ot.get("id", ""),
                    "name": ot.get("name", ""),
                    "description": ot.get("description", ""),
                    "type": "gene",
                    "source": "OpenTargets",
                })
    elif isinstance(ot_results, Exception):
        warnings.append("Open Targets search failed")

    return results, warnings


async def _search_variant(query):
    """Search for variants."""
    warnings = []
    results = []

    try:
        variant_results = await myvariant.search_variants(query, limit=10)
        for v in variant_results:
            results.append({
                "id": v.get("variant_id", ""),
                "name": v.get("rsid", v.get("variant_id", "")),
                "description": v.get("clinical_significance", ""),
                "type": "variant",
                "source": "MyVariant.info",
                "gene": v.get("gene", ""),
            })
    except Exception as e:
        warnings.append("Variant search failed: {}".format(str(e)))

    return results, warnings


async def _search_drug(query):
    """Search for drugs across ChEMBL, RxNorm, and Open Targets."""
    warnings = []
    
    tasks = [
        chembl.search_drug(query, limit=5),
        rxnorm.search_drug(query),
        opentargets.search_drug(query, limit=5),
    ]

    chembl_results, rxnorm_results, ot_results = await asyncio.gather(
        *tasks, return_exceptions=True
    )

    results = []
    seen_ids = set()

    # ChEMBL
    if isinstance(chembl_results, list):
        for drug in chembl_results:
            cid = drug.get("chembl_id", "")
            if cid and cid not in seen_ids:
                results.append({
                    "id": cid,
                    "name": drug.get("pref_name", query),
                    "description": "Phase {} | {}".format(
                        drug.get("max_phase", "?"),
                        drug.get("molecule_type", ""),
                    ),
                    "type": "drug",
                    "source": "ChEMBL",
                })
                seen_ids.add(cid)
    elif isinstance(chembl_results, Exception):
        warnings.append("ChEMBL drug search failed")

    # RxNorm
    if isinstance(rxnorm_results, list):
        for drug in rxnorm_results:
            rid = drug.get("rxcui", "")
            if rid and rid not in seen_ids:
                results.append({
                    "id": rid,
                    "name": drug.get("name", query),
                    "description": "RxNorm Concept ({})".format(drug.get("tty", "")),
                    "type": "drug",
                    "source": "RxNorm",
                })
                seen_ids.add(rid)
    elif isinstance(rxnorm_results, Exception):
        warnings.append("RxNorm drug search failed")

    # Open Targets
    if isinstance(ot_results, list):
        for drug in ot_results:
            otid = drug.get("id", "")
            # OT IDs are often ChEMBL IDs, so deduplicate
            if otid and otid not in seen_ids:
                results.append({
                    "id": otid,
                    "name": drug.get("name", query),
                    "description": drug.get("description", "Clinical Candidate"),
                    "type": "drug",
                    "source": "OpenTargets",
                })
                seen_ids.add(otid)
    elif isinstance(ot_results, Exception):
        warnings.append("Open Targets drug search failed")

    return results, warnings


async def _search_disease(query):
    """Search for diseases in Open Targets."""
    warnings = []
    results = []

    try:
        ot_results = await opentargets.search_disease(query, limit=10)
        for disease in ot_results:
            results.append({
                "id": disease.get("id", ""),
                "name": disease.get("name", ""),
                "description": disease.get("description", ""),
                "type": "disease",
                "source": "OpenTargets",
            })
    except Exception as e:
        warnings.append("Disease search failed: {}".format(str(e)))

    return results, warnings
