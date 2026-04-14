"""
BioFusion AI — Variant API Route
Variant annotation with risk classification.
"""

import logging

from fastapi import APIRouter

from cache_manager import cache
from fusion_engine import score_variant_risk
from services import myvariant

logger = logging.getLogger("biofusion.api.variant")

router = APIRouter()


@router.get("/{variant_id:path}")
async def get_variant(variant_id: str):
    """
    Get variant annotation and risk assessment.
    
    Args:
        variant_id: rsID (e.g., rs121913529) or HGVS notation
    """
    # Check cache
    cached = cache.get("variant", variant_id)
    if cached:
        return cached

    warnings = []

    try:
        variant_data = await myvariant.get_variant(variant_id)
    except Exception as e:
        logger.error("Variant fetch failed: %s", e)
        return {
            "variant_id": variant_id,
            "error": "Failed to fetch variant data",
            "warnings": [str(e)],
        }

    if not variant_data:
        return {
            "variant_id": variant_id,
            "error": "Variant not found",
            "warnings": ["No data found for variant: {}".format(variant_id)],
        }

    # Score risk
    risk_assessment = score_variant_risk(variant_data)

    result = {
        "variant_id": variant_id,
        "rsid": variant_data.get("rsid", ""),
        "clinvar": variant_data.get("clinvar", {}),
        "cadd_phred": variant_data.get("cadd_phred"),
        "allele_frequency": variant_data.get("allele_frequency"),
        "risk_assessment": risk_assessment,
        "warnings": warnings,
    }

    # Cache
    cache.set("variant", variant_id, result)

    return result
