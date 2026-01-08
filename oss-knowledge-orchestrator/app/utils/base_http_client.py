"""
Base HTTP client class
Eliminates duplicate HTTP client patterns across services
"""

import logging
import httpx
import os
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseHTTPClient(ABC):
    """Base class for HTTP clients with common error handling"""
    
    def __init__(self, base_url: str = None, timeout: float = 30.0, env_var: str = None):
        """
        Initialize base HTTP client
        
        Args:
            base_url: Base URL for the service
            timeout: Request timeout in seconds
            env_var: Environment variable name for base URL (if base_url not provided)
        """
        if base_url:
            self.base_url = base_url.rstrip('/')
        elif env_var:
            env_value = os.getenv(env_var, "")
            if not env_value:
                # Provide sensible defaults for known services
                defaults = {
                    "INTENT_CLASSIFIER_URL": "http://localhost:8001",
                    "CONTEXT_MANAGER_URL": "http://localhost:8005",
                    "SEARCH_SERVER_URL": "http://localhost:8002",
                    "TASK_PLANNER_URL": "http://localhost:8004",
                    "BACKEND_SERVICE_URL": "http://localhost:8080"
                }
                env_value = defaults.get(env_var, "")
            self.base_url = env_value.rstrip('/')
        else:
            raise ValueError("Either base_url or env_var must be provided")
        
        self.timeout = httpx.Timeout(timeout)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"{self.__class__.__name__} initialized with base_url: {self.base_url}")
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        raise_on_error: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with common error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to base_url)
            json_data: JSON body for POST/PUT requests
            params: Query parameters
            raise_on_error: Whether to raise exceptions on error
            
        Returns:
            Response JSON as dict, or None if error and raise_on_error=False
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                method_upper = method.upper()
                
                if method_upper == "GET":
                    response = await client.get(url, params=params)
                elif method_upper == "POST":
                    response = await client.post(url, json=json_data, params=params)
                elif method_upper == "PUT":
                    response = await client.put(url, json=json_data, params=params)
                elif method_upper == "DELETE":
                    response = await client.delete(url, params=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} from {url}"
            if hasattr(e.response, 'text'):
                error_msg += f": {e.response.text}"
            self.logger.error(error_msg)
            if raise_on_error:
                raise
            return None
            
        except httpx.RequestError as e:
            error_msg = f"Request error to {url}: {str(e)}"
            self.logger.error(error_msg)
            if raise_on_error:
                raise
            return None
            
        except Exception as e:
            error_msg = f"Unexpected error in request to {url}: {str(e)}"
            self.logger.error(error_msg)
            if raise_on_error:
                raise
            return None

