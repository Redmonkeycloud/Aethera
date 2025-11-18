"""Factory for creating storage backends."""

from __future__ import annotations

from .base import StorageBackend, StorageConfig
from .local import LocalStorageBackend
from .s3 import S3StorageBackend


def create_storage_backend(config: StorageConfig) -> StorageBackend:
    """
    Create a storage backend based on configuration.

    Args:
        config: Storage configuration

    Returns:
        Storage backend instance
    """
    if config.backend_type == "local":
        return LocalStorageBackend(config)
    elif config.backend_type == "s3":
        return S3StorageBackend(config)
    else:
        raise ValueError(f"Unknown storage backend type: {config.backend_type}")

