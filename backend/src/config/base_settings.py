"""Base application settings and constants."""

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

    postgres_dsn: str = Field("postgresql://aethera:aethera@localhost:55432/aethera", alias="POSTGRES_DSN")
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # Storage configuration
    storage_backend: str = Field("local", alias="STORAGE_BACKEND")
    storage_base_path: Path | None = Field(None, alias="STORAGE_BASE_PATH")
    s3_endpoint_url: str | None = Field(None, alias="S3_ENDPOINT_URL")
    s3_bucket: str | None = Field(None, alias="S3_BUCKET")
    s3_access_key_id: str | None = Field(None, alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str | None = Field(None, alias="S3_SECRET_ACCESS_KEY")
    s3_region: str | None = Field(None, alias="S3_REGION")

    # Embedding configuration
    embedding_provider: str = Field("sentence-transformers", alias="EMBEDDING_PROVIDER")  # "openai" or "sentence-transformers"
    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    embedding_model: str = Field("all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")  # Default: sentence-transformers model

    # Observability configuration
    enable_tracing: bool = Field(True, alias="ENABLE_TRACING")
    otlp_endpoint: str | None = Field(None, alias="OTLP_ENDPOINT")  # OTLP collector endpoint
    service_name: str = Field("aethera-backend", alias="SERVICE_NAME")
    service_version: str = Field("0.1.0", alias="SERVICE_VERSION")
    enable_metrics: bool = Field(True, alias="ENABLE_METRICS")
    metrics_port: int = Field(9090, alias="METRICS_PORT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = AppSettings()

