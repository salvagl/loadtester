"""
LoadTester Application Settings
Configuration management using Pydantic Settings
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = Field(default="LoadTester", env="APP_NAME")
    app_version: str = Field(default="0.0.1", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database
    database_url: str = Field(
        default="sqlite:///data/loadtester.db", 
        env="DATABASE_URL"
    )
    
    # Load Testing Configuration
    degradation_response_time_multiplier: float = Field(
        default=5.0, 
        env="DEGRADATION_RESPONSE_TIME_MULTIPLIER"
    )
    degradation_error_rate_threshold: float = Field(
        default=0.5, 
        env="DEGRADATION_ERROR_RATE_THRESHOLD"
    )
    default_test_duration: int = Field(
        default=60, 
        env="DEFAULT_TEST_DURATION"
    )
    max_concurrent_jobs: int = Field(
        default=1, 
        env="MAX_CONCURRENT_JOBS"
    )
    initial_user_percentage: float = Field(
        default=0.1, 
        env="INITIAL_USER_PERCENTAGE"
    )
    user_increment_percentage: float = Field(
        default=0.5, 
        env="USER_INCREMENT_PERCENTAGE"
    )
    stop_error_threshold: float = Field(
        default=0.6, 
        env="STOP_ERROR_THRESHOLD"
    )
    
    # File Configuration
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        env="MAX_FILE_SIZE"
    )
    allowed_file_extensions: str = Field(
        default=".csv,.json,.xlsx", 
        env="ALLOWED_FILE_EXTENSIONS"
    )
    
    # Paths
    k6_scripts_path: str = Field(
        default="/app/k6_scripts", 
        env="K6_SCRIPTS_PATH"
    )
    k6_results_path: str = Field(
        default="/app/k6_results", 
        env="K6_RESULTS_PATH"
    )
    upload_path: str = Field(
        default="/app/shared/data/uploads", 
        env="UPLOAD_PATH"
    )
    reports_path: str = Field(
        default="/app/shared/reports/generated", 
        env="REPORTS_PATH"
    )
    mocked_data_path: str = Field(
        default="/app/shared/data/mocked", 
        env="MOCKED_DATA_PATH"
    )
    
    # AI Services API Keys
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production", 
        env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, 
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # External Services
    callback_timeout: int = Field(default=30, env="CALLBACK_TIMEOUT")
    callback_retry_attempts: int = Field(
        default=3, 
        env="CALLBACK_RETRY_ATTEMPTS"
    )
    
    # Performance
    worker_processes: int = Field(default=1, env="WORKER_PROCESSES")
    worker_connections: int = Field(default=1000, env="WORKER_CONNECTIONS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of: {allowed_levels}")
        return v.upper()
    
    @validator("degradation_response_time_multiplier")
    def validate_response_time_multiplier(cls, v: float) -> float:
        """Validate response time multiplier."""
        if v <= 1.0:
            raise ValueError("Response time multiplier must be greater than 1.0")
        return v
    
    @validator("degradation_error_rate_threshold")
    def validate_error_rate_threshold(cls, v: float) -> float:
        """Validate error rate threshold."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Error rate threshold must be between 0.0 and 1.0")
        return v
    
    @validator("initial_user_percentage")
    def validate_initial_user_percentage(cls, v: float) -> float:
        """Validate initial user percentage."""
        if not 0.0 < v <= 1.0:
            raise ValueError("Initial user percentage must be between 0.0 and 1.0")
        return v
    
    @validator("user_increment_percentage")
    def validate_user_increment_percentage(cls, v: float) -> float:
        """Validate user increment percentage."""
        if v <= 0.0:
            raise ValueError("User increment percentage must be greater than 0.0")
        return v
    
    @validator("stop_error_threshold")
    def validate_stop_error_threshold(cls, v: float) -> float:
        """Validate stop error threshold."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Stop error threshold must be between 0.0 and 1.0")
        return v
    
    @property
    def allowed_file_extensions_list(self) -> list[str]:
        """Get allowed file extensions as a list."""
        return [ext.strip() for ext in self.allowed_file_extensions.split(",")]
    
    @property
    def has_ai_service(self) -> bool:
        """Check if at least one AI service is configured."""
        return any([
            self.google_api_key,
            self.anthropic_api_key,
            self.openai_api_key,
        ])
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.k6_scripts_path,
            self.k6_results_path,
            self.upload_path,
            self.reports_path,
            self.mocked_data_path,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()