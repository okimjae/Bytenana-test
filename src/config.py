import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database Configuration
    DB_HOST: str = Field(default="localhost", alias="DB_HOST")
    DB_PORT: int = Field(default=5432, alias="DB_PORT")
    DB_NAME: str = Field(default="spatial_db", alias="DB_NAME")
    DB_USER: str = Field(default="postgres", alias="DB_USER")
    DB_PASSWORD: str = Field(default="postgrespassword", alias="DB_PASSWORD")

    # Storage Engine: "postgis" or "duckdb"
    STORAGE_BACKEND: str = Field(default="duckdb", alias="STORAGE_BACKEND")
    DUCKDB_PATH: str = Field(default="spatial_data.duckdb", alias="DUCKDB_PATH")

    # Observability & Monitoring
    SENTRY_DSN: str = Field(default="", alias="SENTRY_DSN")
    ENVIRONMENT: str = Field(default="development", alias="ENVIRONMENT")
    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")

    # Geospatial Constants
    SOURCE_CRS: str = "EPSG:4326"
    TARGET_CRS: str = "EPSG:2277"  # NAD83 / Texas South Central (ftUS)
    SQFT_PER_ACRE: float = 43560.0

    # ArcGIS Endpoints
    BUDA_ZONING_URL: str = (
        "https://services6.arcgis.com/vXZW4vAaPRr14z2s/ArcGIS/rest/services/Zoning/FeatureServer/0/query"
    )
    HAYS_PARCELS_URL: str = (
        "https://gis.hayscountytx.com/server/rest/services/OpenData/Parcels/FeatureServer/0/query"
    )

    # Security Guardrails
    MAX_GEOM_VERTICES: int = 50000
    TEXAS_BOUNDS: dict = {
        "min_lon": -107.0,
        "max_lon": -93.0,
        "min_lat": 25.0,
        "max_lat": 37.0,
    }

    @property
    def postgres_uri(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
