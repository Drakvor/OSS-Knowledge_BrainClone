"""
Configuration for File Processing Service with Qdrant and Neo4j
Production-ready configuration with real storage backends
"""

import os
import torch
import platform
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


def get_optimal_device():
    """Auto-detect optimal device for embeddings"""
    try:
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() and platform.system() == "Darwin":
            return "mps"
        else:
            return "cpu"
    except ImportError:
        return "cpu"


class Settings(BaseSettings):
    """Settings for file processing service with production storage"""
    
    # API Configuration
    APP_NAME: str = Field(default="File Processing Service", env="APP_NAME")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # File Processing Configuration
    MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    TEMP_DIR: str = Field(default="data/temp", env="TEMP_DIR")
    
    # Processing Limits
    DEFAULT_CHUNK_SIZE: int = Field(default=400, env="DEFAULT_CHUNK_SIZE")  # From old config
    DEFAULT_CHUNK_OVERLAP: int = Field(default=50, env="DEFAULT_CHUNK_OVERLAP")  # From old config
    MAX_CONCURRENT_JOBS: int = Field(default=5, env="MAX_CONCURRENT_JOBS")
    JOB_TIMEOUT_SECONDS: int = Field(default=600, env="JOB_TIMEOUT_SECONDS")  # 10 minutes for production
    
    # Azure OpenAI GPT Configuration
    OPENAI_API_KEY: str = Field(env="OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: str = Field(default="https://multiagent-openai-service.openai.azure.com/", env="AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION: str = Field(default="2024-12-01-preview", env="AZURE_OPENAI_API_VERSION")
    OPENAI_MODEL: str = Field(default="gpt-4.1-mini", env="OPENAI_MODEL")
    OPENAI_MAX_TOKENS: int = Field(default=4000, env="OPENAI_MAX_TOKENS")
    OPENAI_TEMPERATURE: float = Field(default=0.1, env="OPENAI_TEMPERATURE")
    
    # Azure OpenAI Embedding Configuration
    AZURE_EMBEDDING_DEPLOYMENT: str = Field(default="oss-embedding", env="AZURE_EMBEDDING_DEPLOYMENT")
    AZURE_EMBEDDING_MODEL: str = Field(default="text-embedding-3-large", env="AZURE_EMBEDDING_MODEL")
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-large", env="EMBEDDING_MODEL")  # Alias for compatibility
    
    # Azure OpenAI Embedding Configuration
    VECTOR_SIZE: int = Field(default=3072, env="VECTOR_SIZE")  # Azure text-embedding-3-large dimension
    EMBEDDING_BATCH_SIZE: int = Field(default=32, env="EMBEDDING_BATCH_SIZE")
    EMBEDDING_DEVICE: str = Field(default="cpu", env="EMBEDDING_DEVICE")  # Device for embeddings
    
    # Qdrant Configuration
    QDRANT_HOST: str = Field(default="20.249.165.27", env="QDRANT_HOST")
    QDRANT_PORT: int = Field(default=6333, env="QDRANT_PORT")
    QDRANT_API_KEY: Optional[str] = Field(default=None, env="QDRANT_API_KEY")
    QDRANT_HTTPS: bool = Field(default=False, env="QDRANT_HTTPS")
    QDRANT_COLLECTION_NAME: str = Field(default="general", env="QDRANT_COLLECTION_NAME")
    
    # Neo4j Configuration
    NEO4J_URI: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    NEO4J_USER: str = Field(default="neo4j", env="NEO4J_USER")
    NEO4J_PASSWORD: str = Field(env="NEO4J_PASSWORD")
    NEO4J_DATABASE: str = Field(default="neo4j", env="NEO4J_DATABASE")
    
    # PostgreSQL Configuration for Container Validation
    POSTGRES_HOST: str = Field(default="localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_DATABASE: str = Field(default="oss_knowledge", env="POSTGRES_DATABASE")
    POSTGRES_USER: str = Field(default="oss", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="changeme", env="POSTGRES_PASSWORD")
    
    # Java Backend Configuration for Metadata Sync
    JAVA_BACKEND_URL: Optional[str] = Field(default="http://localhost:8080", env="JAVA_BACKEND_URL")
    
    # Storage Configuration
    BATCH_SIZE: int = Field(default=100, env="BATCH_SIZE")  # For batch operations
    ENABLE_QDRANT: bool = Field(default=True, env="ENABLE_QDRANT")
    ENABLE_NEO4J: bool = Field(default=True, env="ENABLE_NEO4J")
    
    # Similarity Search Configuration
    SIMILARITY_FUNCTION: str = Field(default="cosine", env="SIMILARITY_FUNCTION")
    DEFAULT_SEARCH_LIMIT: int = Field(default=10, env="DEFAULT_SEARCH_LIMIT")
    SIMILARITY_THRESHOLD: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    
    # Azure File Share Configuration
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = Field(default=None, env="AZURE_STORAGE_CONNECTION_STRING")
    AZURE_FILE_SHARE_NAME: Optional[str] = Field(default=None, env="AZURE_FILE_SHARE_NAME")
    AZURE_SAS_TOKEN_EXPIRY_HOURS: int = Field(default=1, env="AZURE_SAS_TOKEN_EXPIRY_HOURS")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"  # Allow extra environment variables without error
    }


# Global settings instance
settings = Settings()


def ensure_directories():
    """Create required directories if they don't exist"""
    directories = [
        settings.TEMP_DIR,
        "config",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


# Initialize directories on import
ensure_directories()


# Device information for monitoring
def get_device_info():
    """Get device information for monitoring"""
    device_info = {
        "device": settings.EMBEDDING_DEVICE,
        "cuda_available": torch.cuda.is_available() if 'torch' in globals() else False,
        "mps_available": (
            hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() 
            if 'torch' in globals() else False
        ),
        "platform": platform.system(),
        "python_version": platform.python_version()
    }
    
    if torch.cuda.is_available():
        device_info.update({
            "cuda_version": torch.version.cuda,
            "gpu_count": torch.cuda.device_count(),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else None
        })
    
    return device_info