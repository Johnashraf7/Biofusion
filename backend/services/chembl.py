"""
BioFusion AI — ChEMBL Service Client
Query ChEMBL for drug information, mechanisms, and gene targets.
"""

import logging
from typing import Any, Dict, List, Optional

from config import API_URLS
from services.base_client import http_client

logger = logging.getLogger("biofusion.services.chembl")

BASE_URL = API_URLS["chembl"]


async def search_drug(name: str, limit: int = 5) -> List[Dict]:
    """
    Search ChEMBL for drugs by name.
    """
    url = "{}/molecule/search".format(BASE_URL)
    params = {
        "q": name,
        "limit": str(limit),
        "format": "json",
    }

    data = await http_client.fetch_json("chembl", url, params=params)
    if not data or "molecules" not in data:
        return []

    results = []
    for mol in data.get("molecules", []):
        results.append({
            "chembl_id": mol.get("molecule_chembl_id", ""),
            "pref_name": mol.get("pref_name", "") or "",
            "molecule_type": mol.get("molecule_type", ""),
            "max_phase": mol.get("max_phase", 0),
            "indication_class": mol.get("indication_class", ""),
            "first_approval": mol.get("first_approval", None),
            "oral": mol.get("oral", False),
            "natural_product": mol.get("natural_product", -1),
        })

    logger.info("ChEMBL drug search for '%s': %d results", name, len(results))
    return results


async def get_drug(chembl_id: str) -> Optional[Dict]:
    """
    Get detailed drug information by ChEMBL ID (e.g., CHEMBL25).
    """
    url = "{}/molecule/{}.json".format(BASE_URL, chembl_id)

    data = await http_client.fetch_json("chembl", url)
    if not data:
        return None

    # Extract molecular properties
    mol_props = data.get("molecule_properties", {}) or {}

    result = {
        "chembl_id": data.get("molecule_chembl_id", ""),
        "pref_name": data.get("pref_name", "") or "",
        "molecule_type": data.get("molecule_type", ""),
        "max_phase": data.get("max_phase", 0),
        "indication_class": data.get("indication_class", ""),
        "first_approval": data.get("first_approval", None),
        "oral": data.get("oral", False),
        "molecule_properties": {
            "molecular_weight": mol_props.get("full_mwt", ""),
            "alogp": mol_props.get("alogp", ""),
            "hba": mol_props.get("hba", ""),
            "hbd": mol_props.get("hbd", ""),
            "psa": mol_props.get("psa", ""),
            "num_ro5_violations": mol_props.get("num_ro5_violations", ""),
            "molecular_formula": mol_props.get("full_molformula", ""),
        },
        "synonyms": [],
    }

    # Extract synonyms
    synonyms = data.get("molecule_synonyms", []) or []
    for syn in synonyms[:10]:
        result["synonyms"].append(syn.get("molecule_synonym", ""))

    logger.info("ChEMBL drug fetched: %s (%s)", chembl_id, result["pref_name"])
    return result


async def get_drug_targets(chembl_id: str, limit: int = 10) -> List[Dict]:
    """
    Get gene targets for a drug by ChEMBL ID.
    Uses the mechanism endpoint.
    """
    url = "{}/mechanism.json".format(BASE_URL)
    params = {
        "molecule_chembl_id": chembl_id,
        "limit": str(limit),
        "format": "json",
    }

    data = await http_client.fetch_json("chembl", url, params=params)
    if not data or "mechanisms" not in data:
        return []

    results = []
    for mech in data.get("mechanisms", []):
        results.append({
            "mechanism_of_action": mech.get("mechanism_of_action", ""),
            "action_type": mech.get("action_type", ""),
            "target_chembl_id": mech.get("target_chembl_id", ""),
            "target_name": mech.get("target_name", ""),
            "target_type": mech.get("target_type", ""),
        })

    logger.info("ChEMBL targets for %s: %d mechanisms found", chembl_id, len(results))
    return results


async def search_target(gene_name: str, limit: int = 5) -> List[Dict]:
    """
    Search ChEMBL for targets (genes/proteins) by name.
    """
    url = "{}/target/search".format(BASE_URL)
    params = {
        "q": gene_name,
        "limit": str(limit),
        "format": "json",
    }

    data = await http_client.fetch_json("chembl", url, params=params)
    if not data or "targets" not in data:
        return []

    results = []
    for tgt in data.get("targets", []):
        components = tgt.get("target_components", []) or []
        gene_symbols = []
        for comp in components:
            for syn in comp.get("target_component_synonyms", []):
                if syn.get("syn_type") == "GENE_SYMBOL":
                    gene_symbols.append(syn.get("component_synonym", ""))

        results.append({
            "target_chembl_id": tgt.get("target_chembl_id", ""),
            "pref_name": tgt.get("pref_name", ""),
            "target_type": tgt.get("target_type", ""),
            "organism": tgt.get("organism", ""),
            "gene_symbols": gene_symbols,
        })

    logger.info("ChEMBL target search for '%s': %d results", gene_name, len(results))
    return results
