from typing import List, Optional, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, env_file_encoding="utf-8"
    )

    PROJECT_NAME: str = "OVM System"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ovm_db"
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], values: any) -> any:
        if isinstance(v, str):
            return v
        return f"postgresql+asyncpg://{values.data.get('POSTGRES_USER')}:{values.data.get('POSTGRES_PASSWORD')}@{values.data.get('POSTGRES_SERVER')}:{values.data.get('POSTGRES_PORT')}/{values.data.get('POSTGRES_DB')}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], values: any) -> any:
        if isinstance(v, str):
            return v
        return f"redis://{values.data.get('REDIS_HOST')}:{values.data.get('REDIS_PORT')}/0"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Environment
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # CORS
    ALLOWED_ORIGINS: List[AnyHttpUrl] = []

    # SQLAlchemy
    SQLALCHEMY_ECHO: bool = False

    # Scheduler
    # ---------------------------------------------------------------------------
    # ENABLE_SCHEDULER must be explicitly set to True only on the single
    # primary worker that owns background scan jobs.
    #
    # DEPLOYMENT RULE — THIS SCHEDULER IS SINGLE-INSTANCE ONLY:
    #   In a multi-process deployment (gunicorn, uvicorn workers > 1) this flag
    #   MUST be enabled on exactly ONE worker.  Enabling it on multiple workers
    #   causes duplicate job execution every scan interval.  It is NOT
    #   horizontally distributed — there is no leader-election or distributed
    #   locking.  Set ENABLE_SCHEDULER=true only via a dedicated scheduler
    #   process (e.g. a separate k8s Deployment with replicas: 1).
    # ---------------------------------------------------------------------------
    ENABLE_SCHEDULER: bool = False

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        return []

settings = Settings()
