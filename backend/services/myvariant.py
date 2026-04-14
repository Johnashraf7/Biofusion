"""
BioFusion AI — MyVariant.info Service Client
Query MyVariant.info for variant annotations including ClinVar and CADD.
"""

import logging
from typing import Any, Dict, List, Optional

from config import API_URLS
from services.base_client import http_client

logger = logging.getLogger("biofusion.services.myvariant")

BASE_URL = API_URLS["myvariant"]


async def get_variant(variant_id: str) -> Optional[Dict]:
    """
    Get variant annotation by HGVS ID or rsID.

    Examples:
        - HGVS: "chr17:g.41245466G>A"
        - rsID: "rs121913529"
    """
    url = "{}/variant/{}".format(BASE_URL, variant_id)
    params = {
        "fields": "clinvar,cadd,dbsnp,gnomad_genome,dbnsfp",
    }

    data = await http_client.fetch_json("myvariant", url, params=params)
    if not data or data.get("notfound", False):
        logger.warning("Variant not found: %s", variant_id)
        return None

    # Extract ClinVar info
    clinvar = data.get("clinvar", {})
    clinvar_info = {}
    if clinvar:
        rcv = clinvar.get("rcv", {})
        if isinstance(rcv, list):
            rcv = rcv[0] if rcv else {}

        clinvar_info = {
            "clinical_significance": rcv.get("clinical_significance", "Unknown"),
            "conditions": [],
            "review_status": rcv.get("review_status", ""),
            "variation_id": clinvar.get("variant_id", ""),
            "allele_id": clinvar.get("allele_id", ""),
        }

        # Extract conditions
        conditions = rcv.get("conditions", {})
        if isinstance(conditions, dict):
            name = conditions.get("name", "")
            if name:
                clinvar_info["conditions"].append(name)
        elif isinstance(conditions, list):
            for cond in conditions:
                name = cond.get("name", "")
                if name:
                    clinvar_info["conditions"].append(name)

    # Extract CADD score
    cadd = data.get("cadd", {})
    cadd_score = None
    if cadd:
        cadd_score = cadd.get("phred", None)

    # Extract population frequency from gnomAD
    gnomad = data.get("gnomad_genome", {})
    allele_freq = None
    if gnomad:
        af = gnomad.get("af", {})
        if isinstance(af, dict):
            allele_freq = af.get("af", None)
        else:
            allele_freq = af

    # Extract dbSNP info
    dbsnp = data.get("dbsnp", {})
    rsid = dbsnp.get("rsid", "") if dbsnp else ""

    # Determine risk level
    risk_level = _classify_risk(clinvar_info.get("clinical_significance", ""), cadd_score)

    result = {
        "variant_id": variant_id,
        "rsid": rsid,
        "clinvar": clinvar_info,
        "cadd_phred": cadd_score,
        "allele_frequency": allele_freq,
        "risk_level": risk_level,
        "source": "MyVariant.info",
    }

    logger.info("Variant fetched: %s (risk: %s)", variant_id, risk_level)
    return result


async def search_variants(query: str, limit: int = 10) -> List[Dict]:
    """
    Search for variants by gene name, rsID pattern, or region.
    """
    url = "{}/query".format(BASE_URL)
    params = {
        "q": query,
        "fields": "clinvar.rcv.clinical_significance,clinvar.gene.symbol,cadd.phred,dbsnp.rsid",
        "size": str(limit),
    }

    data = await http_client.fetch_json("myvariant", url, params=params)
    if not data or "hits" not in data:
        return []

    results = []
    for hit in data.get("hits", []):
        clinvar = hit.get("clinvar", {})
        rcv = clinvar.get("rcv", {})
        if isinstance(rcv, list):
            rcv = rcv[0] if rcv else {}

        gene_symbol = ""
        gene_info = clinvar.get("gene", {})
        if isinstance(gene_info, dict):
            gene_symbol = gene_info.get("symbol", "")
        elif isinstance(gene_info, list) and gene_info:
            gene_symbol = gene_info[0].get("symbol", "")

        results.append({
            "variant_id": hit.get("_id", ""),
            "rsid": hit.get("dbsnp", {}).get("rsid", ""),
            "gene": gene_symbol,
            "clinical_significance": rcv.get("clinical_significance", "Unknown"),
            "cadd_phred": hit.get("cadd", {}).get("phred", None),
        })

    logger.info("Variant search for '%s': %d results", query, len(results))
    return results


def _classify_risk(
    clinical_significance: str,
    cadd_score: Optional[float],
) -> str:
    """
    Classify variant risk level based on ClinVar significance and CADD score.

    Returns: "high", "moderate", "low", or "uncertain"
    """
    sig_lower = clinical_significance.lower() if clinical_significance else ""

    # ClinVar-based classification
    if "pathogenic" in sig_lower and "likely" not in sig_lower:
        return "high"
    if "likely pathogenic" in sig_lower:
        return "moderate"
    if "benign" in sig_lower:
        return "low"

    # CADD-based fallback
    if cadd_score is not None:
        if cadd_score >= 30:
            return "high"
        if cadd_score >= 20:
            return "moderate"
        if cadd_score < 15:
            return "low"

    return "uncertain"
