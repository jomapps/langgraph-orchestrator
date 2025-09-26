from pydantic_settings import BaseSettings
from typing import Optional
import os


class RedisSettings(BaseSettings):
    url: Optional[str] = None  # Full Redis URL
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    
    class Config:
        env_prefix = "REDIS_"


class APISettings(BaseSettings):
    title: str = "LangGraph Agent Orchestrator"
    version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    cors_origins: list[str] = ["*"]
    api_key_header: str = "X-API-Key"
    
    class Config:
        env_prefix = "API_"


class WorkflowSettings(BaseSettings):
    max_concurrent_workflows: int = 100
    default_timeout_hours: int = 2
    retry_attempts: int = 3
    retry_delay_seconds: int = 30
    checkpoint_interval_seconds: int = 60
    state_persistence_ttl_days: int = 30
    
    def __init__(self, **kwargs):
        # Map MAX_WORKFLOWS to max_concurrent_workflows
        if 'MAX_WORKFLOWS' in os.environ:
            kwargs['max_concurrent_workflows'] = int(os.environ['MAX_WORKFLOWS'])
        super().__init__(**kwargs)


class AgentSettings(BaseSettings):
    health_check_interval_seconds: int = 30
    health_check_timeout_seconds: int = 10
    max_concurrent_tasks_per_agent: int = 5
    agent_timeout_seconds: int = 300
    agent_retry_attempts: int = 2
    
    def __init__(self, **kwargs):
        # Map MAX_AGENTS to max_concurrent_tasks_per_agent
        if 'MAX_AGENTS' in os.environ:
            kwargs['max_concurrent_tasks_per_agent'] = int(os.environ['MAX_AGENTS'])
        super().__init__(**kwargs)


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
    
    def __init__(self, **kwargs):
        # Map environment variables
        if 'LOG_LEVEL' in os.environ:
            kwargs['level'] = os.environ['LOG_LEVEL']
        if 'LOG_FORMAT' in os.environ:
            kwargs['format'] = os.environ['LOG_FORMAT']
        if 'ENABLE_STRUCTURED_LOGGING' in os.environ:
            kwargs['enable_structured_logging'] = os.environ['ENABLE_STRUCTURED_LOGGING'].lower() == 'true'
        if 'ENABLE_PERFORMANCE_LOGGING' in os.environ:
            kwargs['enable_performance_logging'] = os.environ['ENABLE_PERFORMANCE_LOGGING'].lower() == 'true'
        super().__init__(**kwargs)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    @property
    def redis_url(self) -> str:
        """Build Redis URL from configuration."""
        # If URL is provided directly, use it
        if self.redis.url:
            return self.redis.url
        
        # Check if REDIS_HOST contains a full URL (starts with redis://)
        if self.redis.host.startswith("redis://"):
            return self.redis.host
        
        # Otherwise build from individual components
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
    
    def __init__(self, **kwargs):
        # Map environment variables that don't have direct matches
        if 'SECRET_KEY' in os.environ:
            kwargs['secret_key'] = os.environ['SECRET_KEY']
        if 'API_KEY' in os.environ:
            kwargs['api_key'] = os.environ['API_KEY']
        if 'WORKER_PROCESSES' in os.environ:
            # This would typically go to API settings workers field
            pass
        super().__init__(**kwargs)
    
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