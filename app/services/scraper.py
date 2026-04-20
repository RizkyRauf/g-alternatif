# app/services/scraper.py
"""
Scraper service menggunakan SeleniumBase CDP Mode + Playwright
Kompatibel dengan FastAPI + uvloop via ProcessPoolExecutor
Sesuai dokumentasi: https://seleniumbase.io/examples/cdp_mode/playwright/ReadMe/
"""

from seleniumbase import SB
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import random
import logging
from typing import List

from app.core.config import settings
from app.models.search import SearchResult
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

def get_random_user_agent():
    ua = UserAgent(platforms='desktop')
    return ua.random


def build_params(query: str, page_no: int, category: str = "general") -> dict:
    """Bangun parameter pencarian SearX dengan kategori dinamis"""
    return {
        "q": query,
        "language": "id-ID",
        "time_range": "day",
        "safesearch": "0",
        "pageno": str(page_no),
        "categories": category
    }

def build_url(query: str, page_no: int, category: str = "general") -> str:
    """Bangun URL lengkap dengan query string"""
    params = build_params(query, page_no, category)
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{settings.BASE_URL}?{query_string}"


def extract_results(html: str) -> List[SearchResult]:
    """
    Ekstrak hasil pencarian dari HTML SearX menggunakan BeautifulSoup
    """
    results = []
    soup = BeautifulSoup(html, 'lxml')
    
    articles = soup.select("article.result")
    logger.debug(f"Ditemukan {len(articles)} artikel dalam HTML")
    
    for article in articles:
        try:
            title_el = article.select_one("h3 a")
            title = title_el.get_text(strip=True) if title_el else ""
            url = title_el.get("href") if title_el else ""
            
            domain_el = article.select_one("span.url_i1")
            domain = domain_el.get_text(strip=True) if domain_el else ""
            
            content_el = article.select_one("p.content")
            content = ""
            if content_el:
                for span in content_el.select("span.highlight"):
                    span.unwrap()
                content = content_el.get_text(strip=True)
            
            engine_el = article.select_one("div.engines span:first-child")
            engine = engine_el.get_text(strip=True) if engine_el else "unknown"
            
            if title or url:
                results.append(SearchResult(
                    title=title,
                    url=url,
                    domain=domain,
                    content=content,
                    engine=engine,
                ))
                
        except Exception as e:
            logger.warning(f"Parse error untuk satu artikel: {e}")
            continue
    
    return results


def perform_search(query: str, max_pages: int = None, category: str = None) -> List[SearchResult]:
    """
    Main scraping function - sekarang mendukung parameter category
    """
    if max_pages is None:
        max_pages = settings.DEFAULT_MAX_PAGES
    if category is None:
        category = settings.DEFAULT_CATEGORY

    logger.info(f"Starting scraper: query='{query}', pages={max_pages}, category='{category}'")

    all_results = []

    with SB(
        uc=True,
        agent=get_random_user_agent(),
        headless2=settings.HEADLESS,
        # headless=settings.HEADLESS,
        block_images=settings.BLOCK_IMAGES,
        disable_csp=settings.DISABLE_CSP,
        disable_js=True,
        incognito=True
    ) as sb:
        sb.activate_cdp_mode()
        endpoint_url = sb.cdp.get_endpoint_url()
        
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(endpoint_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            page.set_viewport_size({
                "width": settings.VIEWPORT_WIDTH,
                "height": settings.VIEWPORT_HEIGHT
            })

            for page_no in range(1, max_pages + 1):
                url = build_url(query, page_no, category)
                logger.info(f"Page {page_no}/{max_pages}: {url[:100]}...")

                try:
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    page.wait_for_selector("article.result", timeout=20000)
                    page.wait_for_timeout(1000)

                    html = page.content()
                    page_results = extract_results(html)
                    all_results.extend(page_results)

                    logger.info(f"Page {page_no}: {len(page_results)} results | Total: {len(all_results)}")

                except Exception as e:
                    logger.error(f"Error di page {page_no}: {e}", exc_info=True)
                    continue

                if page_no < max_pages:
                    delay = settings.BASE_DELAY + random.uniform(0.5, 2.0)
                    time.sleep(delay)

            browser.close()

    logger.info(f"Scraper completed: {len(all_results)} total results")
    return all_results