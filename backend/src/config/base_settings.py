"""Base application settings and constants."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    environment: str = Field("development", alias="ENVIRONMENT")
    data_dir: Path = Field(Path("../data"), alias="DATA_DIR")
    data_sources_dir: Path = Field(Path("../data2"), alias="DATA_SOURCES_DIR")
    projects_store: Path = Field(Path("../data/projects.json"), alias="PROJECTS_STORE")
    processed_dir_name: str = "processed"
    raw_dir_name: str = "raw"
    default_crs: str = "EPSG:3035"
    buffer_km: float = 5.0

    postgres_dsn: str = Field(
        "postgresql://aethera:aethera@localhost:55432/aethera", alias="POSTGRES_DSN"
    )
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # Dataset cache settings
    dataset_cache_enabled: bool = Field(True, alias="DATASET_CACHE_ENABLED")
    dataset_cache_dir: Path = Field(Path("../data/cache"), alias="DATASET_CACHE_DIR")
    dataset_cache_max_mb: int = Field(500, alias="DATASET_CACHE_MAX_MB")
    dataset_cache_ttl_hours: int = Field(24, alias="DATASET_CACHE_TTL_HOURS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = AppSettings()

