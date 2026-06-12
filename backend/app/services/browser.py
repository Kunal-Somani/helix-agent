"""Browser automation service.

Fetches webpage content and extracts clean text using HTTPX and BeautifulSoup.
"""

import httpx
from bs4 import BeautifulSoup

from app.logger import log


async def get_task_from_url(url: str) -> str:
    log.info("extracting_quiz_content", url=url)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            
            log.info("quiz_content_extracted", url=url)
            return text
    except Exception as e:
        log.error("content_extraction_failed", url=url, error=str(e))
        raise
