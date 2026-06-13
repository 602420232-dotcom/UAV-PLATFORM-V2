"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Global application settings.

    Values are read from environment variables with the prefix ALGORITHM_ENGINE_.
    Falls back to sensible defaults for local development.
    """

    # --- Application ---
    app_name: str = "algorithm-engine"
    app_version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 9090
    debug: bool = False

    # --- Kafka ---
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_tasks_topic: str = "uav.algorithm.tasks"
    kafka_results_topic: str = "uav.algorithm.results"
    kafka_consumer_group: str = "algorithm-engine-group"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"
    redis_task_ttl: int = 3600  # 1 hour

    # --- Nacos ---
    nacos_host: str = "localhost"
    nacos_port: int = 8848
    nacos_namespace: str = "public"
    nacos_username: str = ""
    nacos_password: str = ""

    # --- Scheduler ---
    max_concurrent_tasks: int = 10
    task_timeout: int = 300  # seconds

    model_config = {"env_prefix": "ALGORITHM_ENGINE_"}


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()
