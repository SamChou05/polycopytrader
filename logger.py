"""
Centralized logging configuration for the Polymarket Copy Trader.
Provides structured logging with file rotation and console output.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


# Log directory
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def setup_logger(
    name: str = "copy_trader",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """
    Create and configure a logger instance.
    
    Args:
        name: Logger name (typically module name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to rotating file
        log_to_console: Whether to log to console
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Formatter with timestamp, level, module, and message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Rotating file handler (10MB max, keep 5 backups)
    if log_to_file:
        log_file = LOG_DIR / f"{name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Pre-configured loggers for each module
def get_main_logger():
    return setup_logger("main")


def get_monitor_logger():
    return setup_logger("monitor")


def get_executor_logger():
    return setup_logger("executor")


def get_database_logger():
    return setup_logger("database")


def get_api_logger():
    return setup_logger("api")


# Default application logger
logger = setup_logger("copy_trader")
