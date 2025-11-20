"""Unit tests for storage backends."""

from __future__ import annotations

import pytest

from src.storage.base import StorageConfig
from src.storage.factory import create_storage_backend
from src.storage.local import LocalStorageBackend


@pytest.mark.unit
class TestStorageBackends:
    """Test storage backend implementations."""

    def test_local_storage_creation(self, temp_dir: Path) -> None:
        """Test local storage backend creation."""
        config = StorageConfig(backend_type="local", base_path=temp_dir)
        storage = create_storage_backend(config)
        assert isinstance(storage, LocalStorageBackend)

    def test_local_storage_save_read(self, temp_dir: Path) -> None:
        """Test local storage save and read operations."""
        config = StorageConfig(backend_type="local", base_path=temp_dir)
        storage = create_storage_backend(config)
        
        test_content = b"test content"
        file_path = storage.save_file("test.txt", test_content)
        assert file_path is not None
        
        read_content = storage.read_file("test.txt")
        assert read_content == test_content

    def test_local_storage_file_exists(self, temp_dir: Path) -> None:
        """Test file existence checking."""
        config = StorageConfig(backend_type="local", base_path=temp_dir)
        storage = create_storage_backend(config)
        
        assert not storage.file_exists("nonexistent.txt")
        
        storage.save_file("test.txt", b"content")
        assert storage.file_exists("test.txt")

