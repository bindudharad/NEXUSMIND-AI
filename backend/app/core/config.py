from functools import cached_property

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "NEXUSMIND AI"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    jwt_secret_key: str = Field(default="change-this-before-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    backend_cors_origins: str = "http://localhost:3000"
    default_tenant_id: str = "tenant_nexusmind_demo"
    demo_ceo_password: str = "nexusmind-demo"
    demo_admin_password: str = "nexusmind-demo"
    postgres_dsn: str = "postgresql+psycopg://nexusmind:nexusmind@localhost:5432/nexusmind"
    mongo_uri: str = "mongodb://localhost:27017"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: AnyHttpUrl | str = "http://localhost:6333"
    neo4j_uri: str = "bolt://localhost:7687"
    kafka_bootstrap_servers: str = "localhost:9092"
    spark_master_url: str = "spark://localhost:7077"
    langchain_enabled: bool = True
    llm_provider: str = "local"
    llm_api_base_url: str = ""
    llm_api_key: str = ""
    rate_limit_per_minute: int = 600
    rate_limit_bypass_loopback: bool = True

    @cached_property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


settings = Settings()
