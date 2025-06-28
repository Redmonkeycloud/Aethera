# utils/logging_utils.py

import logging
import os
import time
import psutil

BASE_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(BASE_LOG_DIR, exist_ok=True)

def init_logger(name: str, country_code: str = "GENERIC"):
    """Initializes a logger that outputs to both console and file."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(BASE_LOG_DIR, f"{country_code}_log_{timestamp}.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if logger is already configured
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.info(f"Logger initialized for {country_code}. Logs will be saved to: {log_filename}")
    return logger

def log_step(logger, message: str):
    """Logs a general step/info message."""
    logger.info(message)

def log_exception(logger, message: str, exception: Exception):
    """Logs an exception with traceback."""
    logger.error(f"{message}: {exception}", exc_info=True)

def log_memory_usage(logger, label: str = "Memory Check"):
    """Logs the current memory usage of the process."""
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 ** 2)  # Convert bytes to MB
    logger.info(f"[{label}] Current memory usage: {mem:.2f} MB")
