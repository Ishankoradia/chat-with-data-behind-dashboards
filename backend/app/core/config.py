"""
Configuration settings for Dashboard Chat Server
"""
from typing import List
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    PROJECT_NAME: str = "Dashboard Chat Server"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # LLM Configuration
    OPENAI_API_KEY: str = ""
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.1
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://user:password@localhost/dashboard_db"
    
    # Connection Pool Configuration
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_PRE_PING: bool = True
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False
    
    # DBT Configuration
    DBT_SEMANTIC_LAYER_URL: str = ""
    DBT_API_KEY: str = ""
    DBT_ENVIRONMENT_ID: str = ""
    
    # Dashboard Context
    DASHBOARD_CONTEXT_LIMIT: int = 10  # Number of dashboard elements to include
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # Development vs Production flags
    DEVELOPMENT: bool = False  # Set to True for development logging
    
    class Config:
        env_file = ".env"


settings = Settings()