import logging
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from app.core.config import settings
from app.models.search import SingleSearchResponse, BatchSearchRequest, BatchSearchResponse
from app.services.scraper import perform_search
from app.services.batch_scraper import batch_search

from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SearX Multi-Keyword Scraper API",
    version="2.0.0",
    description="FastAPI-based scraper dengan ProcessPoolExecutor untuk parallel scraping yang efisien"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/search", response_model=SingleSearchResponse, tags=["Single Search"])
def search(
    q: str = Query(..., min_length=1, max_length=200),
    max_pages: int = Query(settings.DEFAULT_MAX_PAGES, ge=1, le=10),
    category: str = Query(settings.DEFAULT_CATEGORY)
):
    """
    Single keyword search endpoint.
    Scrapes hasil pencarian dari SearX untuk 1 keyword.
    """
    logger.info(f"Single search request: q='{q}', pages={max_pages}, category={category}")
    try:
        results = perform_search(q, max_pages, category)
        return SingleSearchResponse(
            query=q,
            category=category,
            total_results=len(results),
            pages_scraped=max_pages,
            results=results
        )
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/batch", response_model=BatchSearchResponse, tags=["Batch Search"])
async def search_batch(request: BatchSearchRequest):
    """
    Batch keyword search endpoint.
    
    Scrapes multiple keywords secara parallel menggunakan ProcessPoolExecutor.
    Setiap keyword akan diproses di process terpisah dengan browser instance sendiri.
    
    Parameters:
    - keywords: List kata kunci (max 50)
    - max_pages: Jumlah halaman per keyword (1-10)
    - category: Kategori pencarian (general, news, images, dll)
    - concurrency: Jumlah concurrent tasks (1-10)
    
    Example:
    ```json
    {
      "keywords": ["pertamina", "telkom", "bca"],
      "max_pages": 2,
      "category": "news",
      "concurrency": 3
    }
    ```
    """
    if len(request.keywords) > settings.MAX_BATCH_KEYWORDS:
        raise HTTPException(400, f"Max {settings.MAX_BATCH_KEYWORDS} keywords allowed per batch.")
    if request.concurrency > settings.MAX_BATCH_CONCURRENCY:
        raise HTTPException(400, f"Max concurrency is {settings.MAX_BATCH_CONCURRENCY}.")

    logger.info(
        f"Batch request: {len(request.keywords)} keywords, "
        f"concurrency={request.concurrency}, max_pages={request.max_pages}"
    )
    try:
        return await batch_search(
            keywords=request.keywords,
            max_pages=request.max_pages,
            category=request.category,
            concurrency=request.concurrency
        )
    except Exception as e:
        logger.error(f"Batch error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "searx-scraper-api",
        "version": "2.0.0",
        "executor": "ProcessPoolExecutor",
        "max_workers": settings.MAX_WORKERS
    }

@app.get("/")
async def root():
    """Root endpoint dengan informasi API"""
    return {
        "message": "SearX Multi-Keyword Scraper API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "single_search": "GET /search?q=keyword&max_pages=3&category=general",
            "batch_search": "POST /search/batch"
        }
    }