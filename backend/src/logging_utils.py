"""Centralized logging utilities."""

from __future__ import annotations

import logging
from pathlib import Path

from rich.logging import RichHandler


LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging(log_dir: Path | None = None, log_level: int = logging.INFO) -> None:
    handlers: list[logging.Handler] = [RichHandler(markup=False, show_time=False)]

    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "aethera.log", mode="a", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handlers.append(file_handler)

    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

