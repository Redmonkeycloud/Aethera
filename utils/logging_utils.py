import logging
import os
import psutil
from datetime import datetime

def setup_logger(country_code: str = "UNKNOWN") -> logging.Logger:
    """Initializes a file logger for the given country and returns the logger."""
    logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"run_{timestamp}_{country_code}.log"
    log_filepath = os.path.join(logs_dir, log_filename)

    logger = logging.getLogger(f"AETHERA_{country_code}_{timestamp}")
    logger.setLevel(logging.DEBUG)

    # File handler
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setLevel(logging.DEBUG)

    # Console handler (optional)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Avoid duplicated handlers
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    logger.info(f"Logger initialized for country: {country_code}")
    return logger


def log_memory_usage(logger: logging.Logger, label: str = ""):
    """Logs current memory usage using psutil."""
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 ** 3)  # GB
    logger.info(f"[{label}] Memory usage: {mem:.2f} GB")
