"""
Simplified Container Validation Service - Always returns 'general' as fallback
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SimpleContainerValidator:
    """Simplified container validator that always falls back to 'general'"""
    
    def __init__(self):
        logger.info("Simple container validator initialized - always uses 'general' fallback")
    
    def validate_container(self, container_name: str) -> bool:
        """
        Always validate containers as valid, falling back to 'general' behavior
        
        Args:
            container_name: The container name to validate
            
        Returns:
            bool: Always True (all containers are valid)
        """
        logger.info(f"Container validation for '{container_name}': valid (simple fallback)")
        return True
    
    def validate_container_with_suggestions(self, container_name: str) -> Dict[str, Any]:
        """
        Always validate containers as valid with fallback suggestions
        
        Args:
            container_name: The container name to validate
            
        Returns:
            Dict with validation result and suggestions
        """
        return {
            'valid': True,
            'container': container_name,
            'error': None,
            'available_containers': ['general'],
            'suggestions': ['general']
        }
    
    def get_available_containers(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Always return 'general' as the only available container
        
        Args:
            force_refresh: Ignored (always returns same result)
            
        Returns:
            List with only 'general' container
        """
        return [
            {
                'id': 1,
                'name': 'general',
                'description': 'General collection for all documents',
                'icon': '📁',
                'color': 'blue',
                'keywords': '["general", "all", "default"]',
                'monthly_queries': 0
            }
        ]
    
    def get_container_collection_name(self, container_name: str) -> str:
        """
        Return the container name directly as collection name (supports Korean names)
        
        Args:
            container_name: The container name to map
            
        Returns:
            str: The container name to use as collection name
        """
        logger.info(f"Container mapping for '{container_name}': '{container_name}' (direct mapping)")
        return container_name
    
    def get_container_collection_id(self, container_name: str) -> str:
        """
        Return the container name directly as collection ID (supports Korean names)
        
        Args:
            container_name: The container name to map
            
        Returns:
            str: The container name to use as collection ID
        """
        return container_name


# Create a simple instance
simple_container_validator = SimpleContainerValidator()
