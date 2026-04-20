from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # SearX Configuration
    BASE_URL: str = "https://searx.kavin.rocks/search"
    DEFAULT_MAX_PAGES: int = 3
    DEFAULT_CATEGORY: str = "general"

    # Scraping Configuration
    HEADLESS: bool = True
    BLOCK_IMAGES: bool = True
    DISABLE_CSP: bool = True
    VIEWPORT_WIDTH: int = 1280
    VIEWPORT_HEIGHT: int = 800

    # API Configuration
    API_TIMEOUT: float = 120.0
    MAX_WORKERS: int = 3
    LOG_LEVEL: str = "INFO"

    # Batch Configuration
    MAX_BATCH_KEYWORDS: int = 50
    DEFAULT_BATCH_CONCURRENCY: int = 3
    MAX_BATCH_CONCURRENCY: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()