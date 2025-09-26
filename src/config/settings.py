from pydantic_settings import BaseSettings
from typing import Optional
import os


class RedisSettings(BaseSettings):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30


class APISettings(BaseSettings):
    title: str = "LangGraph Agent Orchestrator"
    version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    cors_origins: list[str] = ["*"]
    api_key_header: str = "X-API-Key"


class WorkflowSettings(BaseSettings):
    max_concurrent_workflows: int = 100
    default_timeout_hours: int = 2
    retry_attempts: int = 3
    retry_delay_seconds: int = 30
    checkpoint_interval_seconds: int = 60
    state_persistence_ttl_days: int = 30


class AgentSettings(BaseSettings):
    health_check_interval_seconds: int = 30
    health_check_timeout_seconds: int = 10
    max_concurrent_tasks_per_agent: int = 5
    agent_timeout_seconds: int = 300
    agent_retry_attempts: int = 2


class ExternalServiceSettings(BaseSettings):
    auto_movie_base_url: str = "https://auto-movie.ft.tc"
    brain_service_base_url: str = "https://brain.ft.tc"
    task_service_base_url: str = "https://tasks.ft.tc"
    service_timeout_seconds: int = 30
    service_retry_attempts: int = 3


class LoggingSettings(BaseSettings):
    level: str = "INFO"
    format: str = "json"
    enable_structured_logging: bool = True
    enable_request_logging: bool = True
    enable_performance_logging: bool = True


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    @property
    def redis_url(self) -> str:
        """Build Redis URL from configuration."""
        if self.redis.password:
            return f"redis://:{self.redis.password}@{self.redis.host}:{self.redis.port}/{self.redis.db}"
        return f"redis://{self.redis.host}:{self.redis.port}/{self.redis.db}"
    
    # Redis Configuration
    redis: RedisSettings = RedisSettings()
    
    # API Configuration
    api: APISettings = APISettings()
    
    # Workflow Configuration
    workflow: WorkflowSettings = WorkflowSettings()
    
    # Agent Configuration
    agent: AgentSettings = AgentSettings()
    
    # External Services
    external_services: ExternalServiceSettings = ExternalServiceSettings()
    
    # Logging Configuration
    logging: LoggingSettings = LoggingSettings()
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Allow nested configuration via environment variables
        env_nested_delimiter = "__"


# Global settings instance
settings = Settings()

# Environment-specific overrides
def get_environment_settings():
    """Get environment-specific settings."""
    if settings.environment == "production":
        settings.debug = False
        settings.api.reload = False
        settings.logging.level = "WARNING"
        settings.redis.host = os.getenv("REDIS_HOST", "redis")
        settings.api.host = "0.0.0.0"
    elif settings.environment == "testing":
        settings.debug = False
        settings.redis.db = 15  # Use separate DB for testing
        settings.workflow.max_concurrent_workflows = 10
    
    return settings

# Initialize environment settings
settings = get_environment_settings()