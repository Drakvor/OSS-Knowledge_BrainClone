"""
Configuration settings for OSS Knowledge Search Server
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }
    
    # API Configuration
    APP_NAME: str = Field(default="OSS Knowledge Search Server", env="APP_NAME")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8002, env="PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Vector Database (Qdrant) Configuration
    QDRANT_HOST: str = Field(default="20.249.165.27", env="QDRANT_HOST")
    QDRANT_PORT: int = Field(default=6333, env="QDRANT_PORT")
    QDRANT_COLLECTION: str = Field(default="general", env="QDRANT_COLLECTION")
    QDRANT_TIMEOUT: int = Field(default=30, env="QDRANT_TIMEOUT")
    
    # Graph Database (Neo4j) Configuration
    NEO4J_URI: str = Field(default="neo4j://localhost:7687", env="NEO4J_URI")
    NEO4J_USERNAME: str = Field(default="neo4j", env="NEO4J_USERNAME")
    NEO4J_PASSWORD: str = Field(default="password", env="NEO4J_PASSWORD")
    NEO4J_DATABASE: str = Field(default="neo4j", env="NEO4J_DATABASE")
    NEO4J_TIMEOUT: int = Field(default=30, env="NEO4J_TIMEOUT")

    # PostgreSQL Configuration (for container validation)
    POSTGRES_HOST: str = Field(default="localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_DATABASE: str = Field(default="oss_knowledge", env="POSTGRES_DATABASE")
    POSTGRES_USER: str = Field(default="oss", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="changeme", env="POSTGRES_PASSWORD")
    
    # Azure OpenAI Configuration
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: str = Field(
        default="https://multiagent-openai-service.openai.azure.com/",
        env="AZURE_OPENAI_ENDPOINT"
    )
    AZURE_OPENAI_API_VERSION: str = Field(
        default="2024-12-01-preview",
        env="AZURE_OPENAI_API_VERSION"
    )
    AZURE_EMBEDDING_DEPLOYMENT: str = Field(
        default="oss-embedding",
        env="AZURE_EMBEDDING_DEPLOYMENT"
    )
    AZURE_EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-large",
        env="AZURE_EMBEDDING_MODEL"
    )
    AZURE_EMBEDDING_SMALL_MODEL: str = Field(
        default="oss-embedding-small",
        env="AZURE_EMBEDDING_SMALL_MODEL"
    )
    
    # Search Configuration
    VECTOR_SIZE: int = Field(default=3072, env="VECTOR_SIZE")  # text-embedding-3-large dimension (for general search)
    DEFAULT_SEARCH_LIMIT: int = Field(default=10, env="DEFAULT_SEARCH_LIMIT")
    MAX_SEARCH_LIMIT: int = Field(default=100, env="MAX_SEARCH_LIMIT")
    DEFAULT_SIMILARITY_THRESHOLD: float = Field(default=0.55, env="DEFAULT_SIMILARITY_THRESHOLD")
    
    # Performance Configuration
    MAX_CONCURRENT_SEARCHES: int = Field(default=10, env="MAX_CONCURRENT_SEARCHES")
    SEARCH_TIMEOUT_SECONDS: int = Field(default=30, env="SEARCH_TIMEOUT_SECONDS")
    CACHE_TTL_SECONDS: int = Field(default=300, env="CACHE_TTL_SECONDS")  # 5 minutes
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    # Mem0 Memory Service Configuration
    MEM0_BASE_URL: str = Field(default="http://localhost:8005", env="MEM0_BASE_URL")
    MEM0_ENABLED: bool = Field(default=True, env="MEM0_ENABLED")
    MEM0_TIMEOUT: int = Field(default=30, env="MEM0_TIMEOUT")
    
    # Memory Configuration
    MEM0_USER_MEMORY_LIMIT: int = Field(default=5, env="MEM0_USER_MEMORY_LIMIT")
    MEM0_SESSION_MEMORY_LIMIT: int = Field(default=10, env="MEM0_SESSION_MEMORY_LIMIT")
    MEM0_AUTO_SAVE_IMPORTANT: bool = Field(default=True, env="MEM0_AUTO_SAVE_IMPORTANT")
    
    # Azure File Share Configuration
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = Field(default=None, env="AZURE_STORAGE_CONNECTION_STRING")
    AZURE_FILE_SHARE_NAME: Optional[str] = Field(default=None, env="AZURE_FILE_SHARE_NAME")
    AZURE_SAS_TOKEN_EXPIRY_HOURS: int = Field(default=1, env="AZURE_SAS_TOKEN_EXPIRY_HOURS")


# Global settings instance
settings = Settings()