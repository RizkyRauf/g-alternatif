
import logging
import sys
import os
from app.core.config import settings

def setup_logging():
    """
    Configure logging for the application.
    Works for both main process and subprocesses.
    """
    log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    # Create a root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicate logs
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)
    
    # File handler (optional but recommended for "recording" logs)
    try:
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to setup file logging: {e}", file=sys.stderr)

    return root_logger
