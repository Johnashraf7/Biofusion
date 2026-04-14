"""
BioFusion AI — Open Targets Service Client
Query Open Targets GraphQL API for disease-gene associations and drug data.
"""

import logging
from typing import Any, Dict, List, Optional

from config import API_URLS
from services.base_client import http_client

logger = logging.getLogger("biofusion.services.opentargets")

GRAPHQL_URL = API_URLS["opentargets"]

# ─── GraphQL Query Templates ──────────────────────────────────────────────────

SEARCH_TARGET_QUERY = """
query SearchTarget($queryString: String!, $size: Int!) {
  search(queryString: $queryString, entityNames: ["target"], page: {size: $size, index: 0}) {
    total
    hits {
      id
      name
      description
      entity
    }
  }
}
"""

SEARCH_DISEASE_QUERY = """
query SearchDisease($queryString: String!, $size: Int!) {
  search(queryString: $queryString, entityNames: ["disease"], page: {size: $size, index: 0}) {
    total
    hits {
      id
      name
      description
      entity
    }
  }
}
"""

SEARCH_DRUG_QUERY = """
query SearchDrug($queryString: String!, $size: Int!) {
  search(queryString: $queryString, entityNames: ["drug"], page: {size: $size, index: 0}) {
    total
    hits {
      id
      name
      description
      entity
    }
  }
}
"""

TARGET_DISEASES_QUERY = """
query TargetDiseases($ensemblId: String!, $size: Int!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    approvedName
    associatedDiseases(page: {size: $size, index: 0}) {
      count
      rows {
        disease {
          id
          name
          description
        }
        score
        datatypeScores {
          id
          score
        }
      }
    }
  }
}
"""

DISEASE_TARGETS_QUERY = """
query DiseaseTargets($efoId: String!, $size: Int!) {
  disease(efoId: $efoId) {
    id
    name
    description
    associatedTargets(page: {size: $size, index: 0}) {
      count
      rows {
        target {
          id
          approvedSymbol
          approvedName
        }
        score
        datatypeScores {
          id
          score
        }
      }
    }
  }
}
"""

DISEASE_DRUGS_QUERY = """
query DiseaseDrugs($efoId: String!) {
  disease(efoId: $efoId) {
    id
    name
    drugAndClinicalCandidates {
      count
      rows {
        maxClinicalStage
        drug {
          id
          name
          drugType
          maximumClinicalStage
        }
      }
    }
  }
}
"""


async def search_target(gene_name: str, limit: int = 5) -> List[Dict]:
    """
    Search Open Targets for a gene/target by name.
    """
    data = await http_client.fetch_graphql(
        "opentargets",
        GRAPHQL_URL,
        SEARCH_TARGET_QUERY,
        variables={"queryString": gene_name, "size": limit},
    )
    if not data or "search" not in data:
        return []

    results = []
    for hit in data["search"].get("hits", []):
        results.append({
            "id": hit.get("id", ""),
            "name": hit.get("name", ""),
            "description": hit.get("description", ""),
            "entity": hit.get("entity", ""),
        })

    logger.info("OpenTargets target search '%s': %d results", gene_name, len(results))
    return results


async def search_disease(disease_name: str, limit: int = 5) -> List[Dict]:
    """
    Search Open Targets for diseases.
    """
    data = await http_client.fetch_graphql(
        "opentargets",
        GRAPHQL_URL,
        SEARCH_DISEASE_QUERY,
        variables={"queryString": disease_name, "size": limit},
    )
    if not data or "search" not in data:
        return []

    results = []
    for hit in data["search"].get("hits", []):
        results.append({
            "id": hit.get("id", ""),
            "name": hit.get("name", ""),
            "description": hit.get("description", ""),
        })

    logger.info("OpenTargets disease search '%s': %d results", disease_name, len(results))
    return results


async def search_drug(drug_name: str, limit: int = 5) -> List[Dict]:
    """
    Search Open Targets for drugs.
    """
    data = await http_client.fetch_graphql(
        "opentargets",
        GRAPHQL_URL,
        SEARCH_DRUG_QUERY,
        variables={"queryString": drug_name, "size": limit},
    )
    if not data or "search" not in data:
        return []

    results = []
    for hit in data["search"].get("hits", []):
        results.append({
            "id": hit.get("id", ""),
            "name": hit.get("name", ""),
            "description": hit.get("description", ""),
        })

    logger.info("OpenTargets drug search '%s': %d results", drug_name, len(results))
    return results


async def get_disease_associations(ensembl_id: str, limit: int = 20) -> Optional[Dict]:
    """
    Get diseases associated with a gene (by Ensembl ID).
    Returns association scores from Open Targets.
    """
    data = await http_client.fetch_graphql(
        "opentargets",
        GRAPHQL_URL,
        TARGET_DISEASES_QUERY,
        variables={"ensemblId": ensembl_id, "size": limit},
    )
    if not data or "target" not in data:
        return None

    target = data["target"]
    associations = []
    assoc_data = target.get("associatedDiseases", {})

    for row in assoc_data.get("rows", []):
        disease = row.get("disease", {})
        associations.append({
            "disease_id": disease.get("id", ""),
            "disease_name": disease.get("name", ""),
            "disease_description": disease.get("description", ""),
            "overall_score": row.get("score", 0),
            "datatype_scores": {
                dt.get("id", ""): dt.get("score", 0)
                for dt in row.get("datatypeScores", [])
            },
        })

    result = {
        "ensembl_id": target.get("id", ""),
        "gene_symbol": target.get("approvedSymbol", ""),
        "gene_name": target.get("approvedName", ""),
        "total_associations": assoc_data.get("count", 0),
        "associations": associations,
    }

    logger.info(
        "OpenTargets associations for %s: %d diseases",
        ensembl_id, len(associations),
    )
    return result


async def get_disease_targets(efo_id: str, limit: int = 20) -> Optional[Dict]:
    """
    Get gene targets associated with a disease (by EFO ID).
    """
    data = await http_client.fetch_graphql(
        "opentargets",
        GRAPHQL_URL,
        DISEASE_TARGETS_QUERY,
        variables={"efoId": efo_id, "size": limit},
    )
    if not data or "disease" not in data:
        return None

    disease = data["disease"]
    targets = []
    assoc_data = disease.get("associatedTargets", {})

    for row in assoc_data.get("rows", []):
        tgt = row.get("target", {})
        targets.append({
            "ensembl_id": tgt.get("id", ""),
            "gene_symbol": tgt.get("approvedSymbol", ""),
            "gene_name": tgt.get("approvedName", ""),
            "overall_score": row.get("score", 0),
        })

    result = {
        "disease_id": disease.get("id", ""),
        "disease_name": disease.get("name", ""),
        "disease_description": disease.get("description", ""),
        "total_targets": assoc_data.get("count", 0),
        "targets": targets,
    }

    logger.info(
        "OpenTargets targets for %s: %d genes",
        efo_id, len(targets),
    )
    return result


async def get_disease_drugs(efo_id: str, limit: int = 10) -> List[Dict]:
    """
    Get known drugs for a disease.
    Uses drugAndClinicalCandidates (replaces deprecated knownDrugs).
    """
    data = await http_client.fetch_graphql(
        "opentargets",
        GRAPHQL_URL,
        DISEASE_DRUGS_QUERY,
        variables={"efoId": efo_id},
    )
    if not data or "disease" not in data:
        return []

    disease = data["disease"]
    if not disease:
        return []

    drugs_data = disease.get("drugAndClinicalCandidates", {})
    if not drugs_data:
        return []

    results = []
    seen_drug_ids = set()

    for row in drugs_data.get("rows", []):
        drug = row.get("drug", {})
        if not drug:
            continue

        drug_id = drug.get("id", "")
        # Deduplicate by drug ID
        if drug_id in seen_drug_ids:
            continue
        seen_drug_ids.add(drug_id)

        results.append({
            "drug_id": drug_id,
            "drug_name": drug.get("name", ""),
            "drug_type": drug.get("drugType", ""),
            "max_phase": drug.get("maximumClinicalStage", ""),
            "mechanism": "",
            "target_genes": [],
            "indication_stage": row.get("maxClinicalStage", ""),
        })

        if len(results) >= limit:
            break

    logger.info("OpenTargets drugs for %s: %d drugs", efo_id, len(results))
    return results
