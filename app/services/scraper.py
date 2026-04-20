import time
import random
import logging
import os
from typing import List
from bs4 import BeautifulSoup
from seleniumbase import SB
from app.core.config import settings

from app.core.logging_config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

def build_params(query: str, page_no: int, category: str = "general") -> dict:
    return {
        "q": query,
        "language": "id-ID",
        "time_range": "day",
        "safesearch": "0",
        "pageno": str(page_no),
        "categories": category
    }

def build_url(query: str, page_no: int, category: str = "general") -> str:
    params = build_params(query, page_no, category)
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{settings.BASE_URL}?{query_string}"

def extract_results(html: str, page_number: int, worker_id: int = 0) -> List[dict]:
    results = []
    soup = BeautifulSoup(html, 'lxml')

    for article in soup.select("article.result"):
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
                results.append({
                    "title": title,
                    "url": url,
                    "domain": domain,
                    "content": content,
                    "engine": engine,
                    "page_number": page_number,
                    "worker_id": worker_id,
                    "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S")
                })
        except Exception as e:
            logger.warning(f"Parse error on page {page_number}: {e}")
            continue
    return results

def perform_search(query: str, max_pages: int = None, category: str = None, worker_id: int = 0) -> List[dict]:
    """
    Fungsi scraping yang akan dipanggil oleh ProcessPoolExecutor.
    PENTING: Setiap process akan memiliki browser instance sendiri yang terisolasi.
    
    Args:
        query: Kata kunci pencarian
        max_pages: Jumlah halaman yang akan di-scrape
        category: Kategori pencarian (general, news, images, dll)
        worker_id: ID worker untuk tracking
    
    Returns:
        List hasil scraping dalam bentuk dictionary
    """
    max_pages = max_pages or settings.DEFAULT_MAX_PAGES
    category = category or settings.DEFAULT_CATEGORY

    pid = os.getpid()
    logger.info(f"[PID {pid}] Starting scraper: query='{query}', pages={max_pages}, category='{category}'")
    
    all_results = []

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    try:
        with SB(
            uc=True,
            headless2=settings.HEADLESS,
            block_images=settings.BLOCK_IMAGES,
            disable_csp=settings.DISABLE_CSP,
            disable_js=False,
            incognito=True,
            chromium_arg=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                f"--user-agent={random.choice(user_agents)}"
            ]
        ) as sb:
            for page_no in range(1, max_pages + 1):
                url = build_url(query, page_no, category)
                logger.info(f"[PID {pid}] Page {page_no}/{max_pages}: {url[:80]}...")

                try:
                    sb.open(url)
                    sb.wait_for_element("article.result", timeout=25000)
                    time.sleep(random.uniform(1.0, 2.0))

                    html = sb.get_page_source()
                    page_results = extract_results(html, page_no, worker_id)
                    all_results.extend(page_results)
                    logger.info(f"[PID {pid}] Page {page_no}: {len(page_results)} results | Total: {len(all_results)}")

                except Exception as e:
                    logger.error(f"[PID {pid}] Error di page {page_no}: {e}", exc_info=True)
                    continue

                if page_no < max_pages:
                    delay = 2.0 + random.uniform(0.5, 1.5)
                    time.sleep(delay)

    except Exception as e:
        logger.error(f"[PID {pid}] Fatal error in scraper: {e}", exc_info=True)
        raise

    logger.info(f"[PID {pid}] Scraper completed: {len(all_results)} total results for '{query}'")
    return all_results