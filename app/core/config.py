# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # SearX Configuration
    BASE_URL: str = "https://searx.kavin.rocks/search"
    DEFAULT_MAX_PAGES: int = 3
    BASE_DELAY: float = 2.0
    
    # Scraping Configuration
    HEADLESS: bool = True
    BLOCK_IMAGES: bool = True
    DISABLE_CSP: bool = True
    VIEWPORT_WIDTH: int = 1280
    VIEWPORT_HEIGHT: int = 800
    
    # API Configuration
    API_TIMEOUT: float = 120.0
    MAX_WORKERS: int = 2
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Instance global settings
settings = Settings()