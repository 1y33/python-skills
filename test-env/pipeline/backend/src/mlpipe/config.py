from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read once from the environment."""

    model_config = SettingsConfigDict(
        env_prefix="MLPIPE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        enable_decoding=False,
    )

    service_name: str = "mlpipe"
    log_level: str = "INFO"

    kafka_bootstrap: str = "localhost:9094"
    kafka_client_id: str = "mlpipe"
    kafka_partitions: int = Field(default=6, ge=1, le=64)
    kafka_replication: int = Field(default=1, ge=1, le=3)
    kafka_poll_timeout_ms: int = Field(default=200, ge=10, le=5000)
    kafka_max_batch: int = Field(default=200, ge=1, le=5000)

    postgres_dsn: str = "postgresql://mlpipe:mlpipe@localhost:5432/mlpipe"
    postgres_pool_min: int = Field(default=1, ge=0)
    postgres_pool_max: int = Field(default=8, ge=1)

    redis_url: str = "redis://localhost:6379/0"
    events_channel: str = "mlpipe.events"

    api_key: str | None = None
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    max_attempts: int = Field(default=3, ge=1, le=10)
    retry_backoff_ms: int = Field(default=600, ge=50)
    retry_max_backoff_ms: int = Field(default=30_000, ge=100)
    artificial_delay_ms: int = Field(default=90, ge=0, le=5000)
    heartbeat_interval_ms: int = Field(default=2_000, ge=500)
    heartbeat_ttl_s: int = Field(default=12, ge=2)

    pipeline_refresh_ms: int = Field(default=2_000, ge=500)
    throughput_window_minutes: int = Field(default=30, ge=5, le=180)
    job_page_limit: int = Field(default=30, ge=5, le=100)
    job_page_max: int = Field(default=100, ge=10, le=500)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
