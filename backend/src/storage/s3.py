"""S3-compatible storage backend."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

try:
    import boto3  # type: ignore[import-untyped]
    from botocore.exceptions import ClientError  # type: ignore[import-untyped]
except ImportError:
    boto3 = None  # type: ignore[assignment]
    ClientError = Exception  # type: ignore[assignment]

from ..logging_utils import get_logger
from .base import StorageBackend, StorageConfig

logger = get_logger(__name__)


class S3StorageBackend(StorageBackend):
    """S3-compatible storage backend."""

    def __init__(self, config: StorageConfig) -> None:
        """
        Initialize S3 storage backend.

        Args:
            config: Storage configuration with S3 settings
        """
        if boto3 is None:
            raise ImportError("boto3 is required for S3StorageBackend. Install with: pip install boto3")

        if not config.s3_bucket:
            raise ValueError("s3_bucket is required for S3StorageBackend")

        self.bucket = config.s3_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=config.s3_endpoint_url,
            aws_access_key_id=config.s3_access_key_id,
            aws_secret_access_key=config.s3_secret_access_key,
            region_name=config.s3_region,
            use_ssl=config.s3_use_ssl,
        )
        logger.info("Initialized S3 storage for bucket %s", self.bucket)

    def _normalize_path(self, file_path: str) -> str:
        """Normalize file path for S3 (use forward slashes)."""
        return str(Path(file_path).as_posix())

    def save_file(self, file_path: str, content: bytes | BinaryIO) -> str:
        """Save a file to S3."""
        key = self._normalize_path(file_path)

        if isinstance(content, bytes):
            self.client.put_object(Bucket=self.bucket, Key=key, Body=content)
        else:
            self.client.upload_fileobj(content, self.bucket, key)

        logger.debug("Saved file to s3://%s/%s", self.bucket, key)
        return key

    def read_file(self, file_path: str) -> bytes:
        """Read a file from S3."""
        key = self._normalize_path(file_path)
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"File not found: {file_path}") from exc
            raise

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in S3."""
        key = self._normalize_path(file_path)
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def delete_file(self, file_path: str) -> None:
        """Delete a file from S3."""
        key = self._normalize_path(file_path)
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.debug("Deleted file s3://%s/%s", self.bucket, key)
        except ClientError as exc:
            logger.warning("Error deleting file %s: %s", file_path, exc)

    def list_files(self, prefix: str = "") -> list[str]:
        """List files in S3 with a given prefix."""
        prefix_norm = self._normalize_path(prefix) if prefix else ""
        files: list[str] = []
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix_norm):
            if "Contents" in page:
                for obj in page["Contents"]:
                    files.append(obj["Key"])
        return sorted(files)

    def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Get a presigned URL for accessing a file in S3."""
        key = self._normalize_path(file_path)
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as exc:
            logger.error("Error generating presigned URL for %s: %s", file_path, exc)
            raise

