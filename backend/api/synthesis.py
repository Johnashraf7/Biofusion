import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

logger = logging.getLogger("biofusion.api.synthesis")
from services.ai_service import get_synthesis
from fusion_engine import (
    generate_gene_synthesis_prompt,
    generate_drug_synthesis_prompt,
    generate_disease_synthesis_prompt
)

router = APIRouter()

class SynthesisRequest(BaseModel):
    type: str # 'gene', 'drug', 'disease'
    data: Dict[str, Any]

@router.post("")
async def synthesize(request: SynthesisRequest):
    """
    Generate an AI synthesis for a biological entity.
    """
    logger.info("Generating AI synthesis for %s", request.type)
    
    prompt = ""
    if request.type == "gene":
        prompt = generate_gene_synthesis_prompt(request.data)
    elif request.type == "drug":
        prompt = generate_drug_synthesis_prompt(request.data)
    elif request.type == "disease":
        prompt = generate_disease_synthesis_prompt(request.data)
    else:
        raise HTTPException(status_code=400, detail="Invalid entity type for synthesis")

    result = await get_synthesis(prompt)
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to generate AI synthesis")
        
    return {"synthesis": result}
