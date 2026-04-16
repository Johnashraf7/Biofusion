import httpx
import logging
import urllib.parse
from typing import Optional

logger = logging.getLogger("biofusion.ai")

POLLINATIONS_URL = "https://text.pollinations.ai/"

async def get_synthesis(prompt: str, system_prompt: str = "You are a professional bioinformatics assistant.") -> Optional[str]:
    """
    Fetch a synthesis/insight from Pollinations AI using the robust GET endpoint.
    """
    params = {
        "system": system_prompt,
        "seed": 42,
        "model": "openai"
    }
    
    # Properly encode the prompt for URL inclusion
    safe_prompt = urllib.parse.quote(prompt)
    url = f"{POLLINATIONS_URL}{safe_prompt}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            content = response.text.strip()
            if not content:
                return None
                
            return content
    except Exception as e:
        logger.error("AI Synthesis failed: %s", e)
        return None
