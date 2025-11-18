"""Local filesystem storage backend."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import BinaryIO

from ..logging_utils import get_logger
from .base import StorageBackend, StorageConfig

logger = get_logger(__name__)


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, config: StorageConfig) -> None:
        """
        Initialize local storage backend.

        Args:
            config: Storage configuration with base_path set
        """
        if not config.base_path:
            raise ValueError("base_path is required for LocalStorageBackend")
        self.base_path = Path(config.base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info("Initialized local storage at %s", self.base_path)

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve a relative file path to an absolute path."""
        # Normalize path to prevent directory traversal
        normalized = Path(file_path).as_posix()
        if normalized.startswith("/") or ".." in normalized:
            raise ValueError(f"Invalid file path: {file_path}")
        return self.base_path / normalized

    def save_file(self, file_path: str, content: bytes | BinaryIO) -> str:
        """Save a file to local storage."""
        target_path = self._resolve_path(file_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            target_path.write_bytes(content)
        else:
            with open(target_path, "wb") as f:
                shutil.copyfileobj(content, f)

        logger.debug("Saved file to %s", target_path)
        return str(target_path.relative_to(self.base_path))

    def read_file(self, file_path: str) -> bytes:
        """Read a file from local storage."""
        target_path = self._resolve_path(file_path)
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return target_path.read_bytes()

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in local storage."""
        target_path = self._resolve_path(file_path)
        return target_path.exists() and target_path.is_file()

    def delete_file(self, file_path: str) -> None:
        """Delete a file from local storage."""
        target_path = self._resolve_path(file_path)
        if target_path.exists():
            target_path.unlink()
            logger.debug("Deleted file %s", target_path)

    def list_files(self, prefix: str = "") -> list[str]:
        """List files in local storage with a given prefix."""
        prefix_path = self._resolve_path(prefix) if prefix else self.base_path
        if not prefix_path.exists():
            return []

        files: list[str] = []
        for path in prefix_path.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(self.base_path)
                files.append(str(rel_path.as_posix()))
        return sorted(files)

    def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Get a local file path (URL for local storage is just the path)."""
        rel_path = self._resolve_path(file_path).relative_to(self.base_path)
        return f"/storage/{rel_path.as_posix()}"

