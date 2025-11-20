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

    # Performance optimization configuration
    enable_dask: bool = Field(False, alias="ENABLE_DASK")  # Enable Dask-Geopandas for parallel processing
    enable_tiling: bool = Field(False, alias="ENABLE_TILING")  # Enable tiling for large AOIs
    tile_size_km: float = Field(50.0, alias="TILE_SIZE_KM")  # Tile size in kilometers
    aoi_size_threshold_km2: float = Field(1000.0, alias="AOI_SIZE_THRESHOLD_KM2")  # Threshold for auto-tiling (km²)
    dask_workers: int | None = Field(None, alias="DASK_WORKERS")  # Number of Dask workers (None = auto)

    # Model Governance configuration
    enable_model_registry: bool = Field(True, alias="ENABLE_MODEL_REGISTRY")  # Enable model registry
    enable_drift_detection: bool = Field(True, alias="ENABLE_DRIFT_DETECTION")  # Enable drift detection
    drift_threshold: float = Field(0.2, alias="DRIFT_THRESHOLD")  # Default drift alert threshold
    drift_detection_method: str = Field("ks_test", alias="DRIFT_DETECTION_METHOD")  # Default drift detection method

    # Security configuration
    jwt_secret_key: str = Field("change-me-in-production", alias="JWT_SECRET_KEY")  # JWT signing secret (CHANGE IN PRODUCTION!)
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")  # JWT algorithm
    access_token_expire_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")  # Access token expiration
    refresh_token_expire_days: int = Field(7, alias="REFRESH_TOKEN_EXPIRE_DAYS")  # Refresh token expiration
    enable_authentication: bool = Field(True, alias="ENABLE_AUTHENTICATION")  # Enable authentication middleware
    enable_audit_logging: bool = Field(True, alias="ENABLE_AUDIT_LOGGING")  # Enable audit logging
    oauth_google_client_id: str | None = Field(None, alias="OAUTH_GOOGLE_CLIENT_ID")  # Google OAuth client ID
    oauth_microsoft_client_id: str | None = Field(None, alias="OAUTH_MICROSOFT_CLIENT_ID")  # Microsoft OAuth client ID
    oauth_okta_domain: str | None = Field(None, alias="OAUTH_OKTA_DOMAIN")  # Okta domain

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = AppSettings()

