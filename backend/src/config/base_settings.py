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
    
    # LLM configuration
    llm_provider: str = Field("groq", alias="LLM_PROVIDER")  # "groq", "openai", "ollama"
    groq_api_key: str | None = Field(None, alias="GROQ_API_KEY")
    groq_model: str = Field("llama-3.1-8b-instant", alias="GROQ_MODEL")
    llm_temperature: float = Field(0.3, alias="LLM_TEMPERATURE")
    use_llm: bool = Field(True, alias="USE_LLM")
    
    # ERA5/CDS API configuration
    # Note: Recommended setup is to use ~/.cdsapirc file (see https://cds.climate.copernicus.eu/how-to-api)
    # These environment variables are fallback options
    cds_api_key: str | None = Field(None, alias="CDS_API_KEY")
    cds_api_url: str = Field("https://cds.climate.copernicus.eu/api", alias="CDS_API_URL")

    def model_post_init(self, __context) -> None:
        """Resolve relative paths to absolute paths relative to project root."""
        # This file is at: backend/src/config/base_settings.py
        # Project root is 4 levels up: backend/src/config -> backend/src -> backend -> project_root
        config_file = Path(__file__).resolve()
        project_root = config_file.parent.parent.parent.parent
        
        # Resolve relative paths (handle both Unix and Windows path separators)
        if isinstance(self.data_dir, Path):
            path_str = str(self.data_dir).replace("..\\", "").replace("../", "")
            if not self.data_dir.is_absolute() and (str(self.data_dir).startswith("../") or str(self.data_dir).startswith("..\\")):
                self.data_dir = (project_root / path_str).resolve()
            elif not self.data_dir.is_absolute():
                self.data_dir = (project_root / self.data_dir).resolve()
            
        if isinstance(self.data_sources_dir, Path):
            path_str = str(self.data_sources_dir).replace("..\\", "").replace("../", "")
            if not self.data_sources_dir.is_absolute() and (str(self.data_sources_dir).startswith("../") or str(self.data_sources_dir).startswith("..\\")):
                self.data_sources_dir = (project_root / path_str).resolve()
            elif not self.data_sources_dir.is_absolute():
                self.data_sources_dir = (project_root / self.data_sources_dir).resolve()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = AppSettings()
