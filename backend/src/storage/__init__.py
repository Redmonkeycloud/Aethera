"""Storage abstraction layer for AETHERA."""

from .base import StorageBackend, StorageConfig
from .factory import create_storage_backend
from .local import LocalStorageBackend
from .s3 import S3StorageBackend

__all__ = [
    "StorageBackend",
    "StorageConfig",
    "LocalStorageBackend",
    "S3StorageBackend",
    "create_storage_backend",
]
