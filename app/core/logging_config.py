# app/core/logging_config.py
"""
Structured Logging Configuration - Process-Safe & JSON Format
"""
import logging
import sys
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
import structlog
from pythonjsonlogger import jsonlogger

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logging(log_level: str = "INFO", log_to_file: bool = True):
    """
    Setup logging untuk aplikasi + subprocess (ProcessPoolExecutor compatible)
    """
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    handlers = [console_handler]
    
    # File handlers
    if log_to_file:
        file_handler = RotatingFileHandler(
            LOG_DIR / "scraper.log",
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(json_formatter)
        file_handler.setLevel(logging.DEBUG)
        handlers.append(file_handler)
        
        error_handler = RotatingFileHandler(
            LOG_DIR / "error.log",
            maxBytes=10*1024*1024,
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setFormatter(json_formatter)
        error_handler.setLevel(logging.ERROR)
        handlers.append(error_handler)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()
    
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # Structlog configuration
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Scraper logger (process-safe)
    scraper_logger = logging.getLogger("scraper")
    scraper_logger.propagate = False
    for handler in handlers:
        scraper_logger.addHandler(handler)
    
    return logging.getLogger(__name__), structlog.get_logger("scraper")