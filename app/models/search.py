from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class SearchResultItem(BaseModel):
    title: str
    url: str
    domain: str
    content: str
    engine: str
    page_number: int
    worker_id: int = 0
    scraped_at: str

class SingleSearchResponse(BaseModel):
    query: str
    category: str
    total_results: int
    pages_scraped: int
    results: List[SearchResultItem]

class BatchSearchRequest(BaseModel):
    keywords: List[str] = Field(..., min_length=1, max_length=50)
    max_pages: int = Field(2, ge=1, le=10)
    category: str = Field("general")
    concurrency: int = Field(3, ge=1, le=10)
    lang: str = Field("id-ID")
    skip_failed: bool = Field(True)

class KeywordResult(BaseModel):
    keyword: str
    status: Literal["success", "failed", "partial"]
    results_count: int
    results: List[SearchResultItem] = []
    error: Optional[str] = None
    duration_seconds: Optional[float] = None
    pages_scraped: Optional[int] = None

class BatchSearchResponse(BaseModel):
    request_id: str
    total_keywords: int
    successful: int
    failed: int
    partial: int
    total_results: int
    duration_seconds: float
    started_at: str
    completed_at: str
    results: List[KeywordResult]