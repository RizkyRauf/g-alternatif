# app/models/search.py
from pydantic import BaseModel, Field
from typing import List, Optional

class SearchResult(BaseModel):
    """Model untuk satu hasil pencarian"""
    title: str = Field(..., description="Judul hasil pencarian")
    url: str = Field(..., description="URL lengkap ke artikel")
    domain: str = Field("", description="Nama domain sumber")
    content: str = Field("", description="Snippet/deskripsi konten")
    engine: str = Field("unknown", description="Search engine sumber")
    published_date: Optional[str] = Field(None, description="Tanggal publikasi (jika ada)")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Contoh Judul Berita",
                "url": "https://example.com/artikel",
                "domain": "example.com",
                "content": "Ini adalah cuplikan konten dari artikel...",
                "engine": "google",
                "published_date": "2024-01-15"
            }
        }

class SearchResponse(BaseModel):
    """Model response API pencarian"""
    query: str = Field(..., description="Query pencarian yang digunakan")
    total_results: int = Field(..., description="Jumlah total hasil yang ditemukan")
    results: List[SearchResult] = Field(default_factory=list, description="Daftar hasil pencarian")
    
    # Optional fields untuk metadata
    pages_scraped: Optional[int] = Field(None, description="Jumlah halaman yang discrape")
    error: Optional[str] = Field(None, description="Pesan error jika ada")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "pertamina",
                "total_results": 15,
                "results": [],
                "pages_scraped": 3
            }
        }