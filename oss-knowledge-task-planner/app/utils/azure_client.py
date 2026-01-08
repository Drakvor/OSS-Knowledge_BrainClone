"""
Shared Azure OpenAI client factory
Eliminates duplicate initialization code across services
"""

import logging
import os
import warnings
from typing import Optional
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

# Global client instance (singleton pattern)
_azure_client: Optional[AzureOpenAI] = None
_client_initialized = False


def create_azure_openai_client(
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    azure_endpoint: Optional[str] = None,
    deployment: Optional[str] = None,
    force_new: bool = False
) -> AzureOpenAI:
    """
    Create or return existing Azure OpenAI client (singleton pattern)
    
    Args:
        api_key: Azure OpenAI API key (defaults to OPENAI_API_KEY env var)
        api_version: API version (defaults to AZURE_OPENAI_API_VERSION env var)
        azure_endpoint: Azure endpoint URL (defaults to AZURE_OPENAI_ENDPOINT env var)
        deployment: Deployment name (optional, for testing connection)
        force_new: Force creation of new client instance
        
    Returns:
        AzureOpenAI client instance
    """
    global _azure_client, _client_initialized
    
    # Return existing client if already initialized and not forcing new
    if _client_initialized and _azure_client and not force_new:
        return _azure_client
    
    try:
        # Suppress Pydantic warnings
        warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
        
        # Set Pydantic compatibility mode
        os.environ.setdefault('PYDANTIC_V1_COMPAT', '1')
        os.environ.setdefault('PYDANTIC_V1', '1')
        
        # Get configuration from parameters or environment
        api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", "https://multiagent-openai-service.openai.azure.com/")
        
        if not api_key:
            raise ValueError("Azure OpenAI API key not provided and OPENAI_API_KEY not set")
        
        # Create client
        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint
        )
        
        # Test connection if deployment provided
        if deployment:
            try:
                test_response = client.chat.completions.create(
                    model=deployment,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                if not test_response.choices or len(test_response.choices) == 0:
                    raise Exception("No completion data returned from test")
            except Exception as e:
                logger.warning(f"Connection test failed (may be expected): {e}")
        
        # Store as singleton
        _azure_client = client
        _client_initialized = True
        logger.info("Azure OpenAI client initialized successfully")
        
        return client
        
    except Exception as e:
        logger.error(f"Failed to initialize Azure OpenAI client: {e}")
        raise


def get_azure_openai_client() -> Optional[AzureOpenAI]:
    """Get existing Azure OpenAI client or None if not initialized"""
    return _azure_client if _client_initialized else None


def reset_azure_client():
    """Reset the global client (useful for testing)"""
    global _azure_client, _client_initialized
    _azure_client = None
    _client_initialized = False

