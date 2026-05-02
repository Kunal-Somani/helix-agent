"""Browser automation service using Playwright.

Handles:
- Browser launch and page management
- Webpage content extraction
- HTML parsing and text cleaning
"""

import asyncio

from playwright.async_api import async_playwright

from app.config import settings
from app.logger import log


class BrowserService:
    """Handle browser interactions and web scraping."""

    def __init__(self):
        self.browser = None
        self.playwright = None

    async def initialize(self):
        """Initialize browser instance.
        
        Launches a Chromium browser for page automation.
        """
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch()
        log.info("browser_initialized")

    async def close(self):
        """Close browser instance and cleanup resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        log.info("browser_closed")

    async def extract_quiz_content(self, url: str) -> dict:
        """Extract quiz content from URL.
        
        Scrapes the page at the given URL and extracts quiz metadata
        and questions using Playwright browser automation.
        
        Args:
            url: Full URL of the quiz page to scrape.
            
        Returns:
            Dictionary containing quiz metadata and questions.
            
        Raises:
            ValueError: If URL is invalid or unreachable.
            TimeoutError: If page load exceeds timeout.
        """
        log.info("extracting_quiz_content", url=url)
        
        if not self.browser:
            await self.initialize()

        try:
            page = await self.browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Extract page content
            content = await page.content()
            text = await page.evaluate("() => document.documentElement.innerText")
            
            await page.close()
            
            log.info("quiz_content_extracted", url=url)
            
            return {
                "url": url,
                "html": content[:10000],  # First 10KB
                "text": text,
            }
        except Exception as e:
            log.error("content_extraction_failed", url=url, error=str(e))
            raise


async def get_task_from_url(url: str) -> str:
    """Fetch and extract task content from a URL.
    
    This is the main async interface for retrieving task information.
    Uses the BrowserService to load the page and extract raw text.
    
    Args:
        url: The quiz task URL
        
    Returns:
        Raw text content of the task page
        
    Raises:
        ValueError: If URL is invalid
        TimeoutError: If page load times out
    """
    browser_service = BrowserService()
    try:
        result = await browser_service.extract_quiz_content(url)
        return result["text"]
    finally:
        await browser_service.close()


# Global instance for synchronous access
browser_service = BrowserService()
