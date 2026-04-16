import httpx
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("biofusion.clinical_trials")

# CT.gov API v2
CT_BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

async def get_clinical_trials(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch clinical trials from ClinicalTrials.gov for a given term (drug or disease).
    """
    logger.info("Fetching clinical trials for query: %s", query)
    params = {
        "query.term": query,
        "pageSize": limit
    }

    headers = {
        "User-Agent": "BioFusion-AI/1.0 (bioinformatics-platform)",
        "Accept": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(CT_BASE_URL, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            studies = data.get("studies", [])
            results = []
            
            for study in studies:
                protocol = study.get("protocolSection", {})
                ident = protocol.get("identificationModule", {})
                status = protocol.get("statusModule", {})
                design = protocol.get("designModule", {})
                sponsor = protocol.get("sponsorCollaboratorsModule", {})
                
                results.append({
                    "nct_id": ident.get("nctId"),
                    "title": ident.get("briefTitle"),
                    "status": status.get("overallStatus", "Unknown"),
                    "phase": design.get("phase", []),
                    "sponsor": sponsor.get("leadSponsor", {}).get("name"),
                })
                
            return results
    except Exception as e:
        logger.error("Failed to fetch ClinicalTrials.gov data: %s", e)
        return []
