#!/usr/bin/env python3
"""
Logging configuration for SpotifyTUI
Sets up file logging to write debug logs to a file in the project folder
"""

import os
import logging
import logging.handlers
from pathlib import Path


class _UsefulLogFilter(logging.Filter):
    """Allow only our application's loggers into the file handler.

    This keeps the debug log focused and excludes noisy third‑party libraries.
    """

    def __init__(self) -> None:
        super().__init__()
        # Module logger names we consider part of our app
        self.allowed_prefixes = (
            "simple_tui",
            "spotify_client",
            "lyrics_service",
            "vibechain_client",
            "src.logging_config",
            "vibechain.file",
        )

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        name = record.name
        return name.startswith(self.allowed_prefixes)

def setup_logging():
    """Set up logging configuration with file output"""
    
    # Get the project root directory (where this file is located)
    project_root = Path(__file__).parent.parent
    log_file = project_root / "spotifytui_debug.log"
    
    # Create logs directory if it doesn't exist
    log_file.parent.mkdir(exist_ok=True)
    
    # Start each run with a fresh log file
    try:
        with open(log_file, 'w', encoding='utf-8'):
            pass
    except Exception:
        # If truncation fails, proceed; handler will still write
        pass
    
    # Configure the root logger (INFO by default)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler for detailed logging
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8',
        mode='w'  # ensure truncation on each startup
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    file_handler.addFilter(_UsefulLogFilter())
    
    # Console handler for important messages only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # App logger levels (allow DEBUG)
    logging.getLogger('simple_tui').setLevel(logging.DEBUG)
    logging.getLogger('spotify_client').setLevel(logging.DEBUG)
    logging.getLogger('lyrics_service').setLevel(logging.DEBUG)
    logging.getLogger('vibechain_client').setLevel(logging.DEBUG)
    logging.getLogger('vibechain.file').setLevel(logging.DEBUG)

    # Quiet down noisy third‑party libraries in both console and root
    for noisy in (
        "urllib3",
        "requests",
        "PIL",
        "spotipy",
        "textual",
        "asyncio",
        "httpx",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    
    # Log the setup
    logger = logging.getLogger(__name__)
    
    return log_file

def get_log_file_path():
    """Get the path to the current log file"""
    project_root = Path(__file__).parent.parent
    return project_root / "spotifytui_debug.log"

