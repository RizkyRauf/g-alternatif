import asyncio
import time
import logging
import uuid
from datetime import datetime
from typing import List
from concurrent.futures import ProcessPoolExecutor

from app.services.scraper import perform_search
from app.core.config import settings
from app.models.search import KeywordResult, BatchSearchResponse

logger = logging.getLogger(__name__)

executor = ProcessPoolExecutor(max_workers=settings.MAX_WORKERS)

async def _search_single_keyword(
    keyword: str,
    semaphore: asyncio.Semaphore,
    max_pages: int,
    category: str,
    worker_id: int
) -> KeywordResult:
    """
    Mencari 1 keyword menggunakan ProcessPoolExecutor.
    Semaphore membatasi jumlah concurrent tasks, bukan jumlah browser.
    
    Args:
        keyword: Kata kunci untuk dicari
        semaphore: Asyncio semaphore untuk rate limiting
        max_pages: Jumlah halaman yang akan di-scrape
        category: Kategori pencarian
        worker_id: ID worker untuk tracking
    """
    start_time = time.time()

    async with semaphore:
        try:
            logger.info(f"[Worker {worker_id}] Starting search for: '{keyword}' [category={category}]")
            loop = asyncio.get_running_loop()
            results = await asyncio.wait_for(
                loop.run_in_executor(
                    executor, 
                    perform_search, 
                    keyword, 
                    max_pages, 
                    category,
                    worker_id
                ),
                timeout=settings.API_TIMEOUT
            )

            duration = time.time() - start_time
            status = "success" if results else "partial"

            logger.info(f"[Worker {worker_id}] Completed '{keyword}': {len(results)} results in {duration:.2f}s")
            return KeywordResult(
                keyword=keyword,
                status=status,
                results_count=len(results),
                results=results,
                duration_seconds=round(duration, 2),
                pages_scraped=max_pages
            )

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            logger.error(f"[Worker {worker_id}] Timeout for '{keyword}' after {duration:.2f}s")
            return KeywordResult(
                keyword=keyword,
                status="failed",
                results_count=0,
                results=[],
                error=f"Timeout after {duration:.2f}s",
                duration_seconds=round(duration, 2)
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[Worker {worker_id}] Error searching '{keyword}': {str(e)}", exc_info=True)
            return KeywordResult(
                keyword=keyword,
                status="failed",
                results_count=0,
                results=[],
                error=str(e),
                duration_seconds=round(duration, 2)
            )

async def batch_search(
    keywords: List[str],
    max_pages: int = 2,
    category: str = "general",
    concurrency: int = 3
) -> BatchSearchResponse:
    """
    Melakukan batch search untuk multiple keywords secara parallel.
    
    Cara kerja:
    1. Setiap keyword akan diproses di process terpisah (via ProcessPoolExecutor)
    2. Semaphore membatasi berapa banyak concurrent tasks yang berjalan
    3. Setiap process memiliki browser instance sendiri (tidak ada konflik)
    
    Args:
        keywords: List kata kunci yang akan dicari
        max_pages: Jumlah halaman per keyword
        category: Kategori pencarian
        concurrency: Jumlah maksimal concurrent tasks (dibatasi oleh semaphore)
    
    Returns:
        BatchSearchResponse dengan hasil semua keyword
    """
    request_id = str(uuid.uuid4())
    started_at = datetime.now().isoformat()
    start_time = time.time()

    logger.info(
        f"Batch search started: {len(keywords)} keywords, "
        f"concurrency={concurrency}, max_workers={settings.MAX_WORKERS}"
    )

    semaphore = asyncio.Semaphore(concurrency)

    tasks = [
        _search_single_keyword(kw, semaphore, max_pages, category, idx)
        for idx, kw in enumerate(keywords)
    ]

    # Jalankan semua tasks secara parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    keyword_results = []
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            logger.error(f"Unhandled exception for '{keywords[i]}': {res}", exc_info=True)
            keyword_results.append(KeywordResult(
                keyword=keywords[i],
                status="failed",
                results_count=0,
                results=[],
                error=f"Unhandled exception: {str(res)}"
            ))
        else:
            keyword_results.append(res)

    # Hitung statistik
    successful = sum(1 for r in keyword_results if r.status == "success")
    failed = sum(1 for r in keyword_results if r.status == "failed")
    partial = sum(1 for r in keyword_results if r.status == "partial")
    total_results = sum(r.results_count for r in keyword_results)
    duration = time.time() - start_time

    logger.info(
        f"Batch completed in {duration:.2f}s: "
        f"{successful} success, {failed} failed, {partial} partial, "
        f"{total_results} total results"
    )

    return BatchSearchResponse(
        request_id=request_id,
        total_keywords=len(keywords),
        successful=successful,
        failed=failed,
        partial=partial,
        total_results=total_results,
        duration_seconds=round(duration, 2),
        started_at=started_at,
        completed_at=datetime.now().isoformat(),
        results=keyword_results
    )