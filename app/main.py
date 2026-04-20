# app/main.py
"""
FastAPI Application Entry Point
✅ Menggunakan ProcessPoolExecutor untuk isolasi event loop (kompatibel uvloop)
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ProcessPoolExecutor
import asyncio
import logging
import time
from typing import Optional

from app.services.scraper import perform_search
from app.models.search import SearchResponse, SearchResult
from app.core.config import settings

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Inisialisasi FastAPI app
app = FastAPI(
    title="Google Alternative Search API",
    description="API untuk scraping hasil pencarian dari SearX instance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Tambahkan CORS middleware (opsional, untuk frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Untuk production, ganti dengan domain spesifik
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ProcessPoolExecutor untuk menjalankan blocking scraper
# Max workers sesuai resource server (1 worker ≈ 300-500MB RAM)
executor = ProcessPoolExecutor(max_workers=settings.MAX_WORKERS)


@app.on_event("shutdown")
def shutdown_event():
    """Cleanup executor saat aplikasi shutdown"""
    logger.info("Shutting down executor...")
    executor.shutdown(wait=True)
    logger.info("Executor shutdown complete")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - informasi API"""
    return {
        "message": "Welcome to Google Alternative Search API",
        "version": "1.0.0",
        "documentation": "/docs",
        "example_usage": "/search?q=pertamina&max_pages=2",
        "endpoints": {
            "GET /search": "Lakukan pencarian dengan query",
            "GET /health": "Cek status kesehatan API"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint untuk monitoring"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "max_workers": settings.MAX_WORKERS
    }


@app.get("/search", response_model=SearchResponse, tags=["Search"])
async def search(
    q: str = Query(
        ..., 
        min_length=1, 
        max_length=200, 
        description="Kata kunci pencarian (query)"
    ),
    max_pages: int = Query(
        settings.DEFAULT_MAX_PAGES, 
        ge=1, 
        le=10, 
        description="Jumlah halaman maksimal untuk discrape (1-10)"
    ),
    lang: str = Query(
        "id-ID",
        description="Kode bahasa untuk hasil pencarian (contoh: id-ID, en-US)"
    )
):
    """
    Endpoint pencarian utama
    
    Melakukan scraping hasil pencarian dari SearX instance menggunakan
    SeleniumBase + Playwright dalam mode stealth.
    
    Request ini bisa memakan waktu 10-60 detik tergantung jumlah halaman.
    """
    start_time = time.time()
    logger.info(f"Search request: q='{q}', pages={max_pages}, lang={lang}")
    
    try:
        loop = asyncio.get_running_loop()
        
        results = await asyncio.wait_for(
            loop.run_in_executor(
                executor, 
                perform_search,
                q, 
                max_pages
            ),
            timeout=settings.API_TIMEOUT
        )
        
        elapsed = time.time() - start_time
        logger.info(f"earch completed in {elapsed:.2f}s: {len(results)} results")
        
        return SearchResponse(
            query=q,
            total_results=len(results),
            results=results,
            pages_scraped=max_pages
        )
        
    except asyncio.TimeoutError:
        logger.error(f"Timeout after {settings.API_TIMEOUT}s for query: '{q}'")
        raise HTTPException(
            status_code=504,
            detail=f"Request timeout setelah {settings.API_TIMEOUT} detik. Coba kurangi max_pages."
        )
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/search/simple", tags=["Search"])
async def search_simple(q: str):
    """
    Endpoint pencarian sederhana (tanpa validasi ketat)
    Untuk testing cepat atau penggunaan internal
    """
    try:
        results = perform_search(q, max_pages=1)
        return {
            "query": q,
            "count": len(results),
            "results": [r.model_dump() for r in results]
        }
    except Exception as e:
        return {"error": str(e), "query": q}