"""Base storage interface and configuration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, BinaryIO

from pydantic import BaseModel, Field


class StorageConfig(BaseModel):
    """Configuration for storage backends."""

    backend_type: str = Field("local", description="Storage backend type: 'local' or 's3'")
    base_path: Path | None = Field(None, description="Base path for local storage")
    # S3 configuration
    s3_endpoint_url: str | None = Field(None, description="S3 endpoint URL")
    s3_bucket: str | None = Field(None, description="S3 bucket name")
    s3_access_key_id: str | None = Field(None, description="S3 access key ID")
    s3_secret_access_key: str | None = Field(None, description="S3 secret access key")
    s3_region: str | None = Field(None, description="S3 region")
    s3_use_ssl: bool = Field(True, description="Use SSL for S3 connections")


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save_file(self, file_path: str, content: bytes | BinaryIO) -> str:
        """
        Save a file to storage.

        Args:
            file_path: Relative path where the file should be stored
            content: File content as bytes or file-like object

        Returns:
            URL or path to the saved file
        """
        pass

    @abstractmethod
    def read_file(self, file_path: str) -> bytes:
        """
        Read a file from storage.

        Args:
            file_path: Relative path to the file

        Returns:
            File content as bytes
        """
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            file_path: Relative path to the file

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> None:
        """
        Delete a file from storage.

        Args:
            file_path: Relative path to the file
        """
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> list[str]:
        """
        List files in storage with a given prefix.

        Args:
            prefix: Path prefix to filter files

        Returns:
            List of file paths
        """
        pass

    @abstractmethod
    def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        Get a URL to access a file (may be temporary for S3).

        Args:
            file_path: Relative path to the file
            expires_in: URL expiration time in seconds (for S3 presigned URLs)

        Returns:
            URL to access the file
        """
        pass

