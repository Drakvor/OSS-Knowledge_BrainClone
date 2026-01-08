"""
Container Validation Service
Validates container names against the PostgreSQL database
"""

import logging
import psycopg2
from typing import List, Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class ContainerValidationError(Exception):
    """Raised when container validation fails"""
    pass


class ContainerValidationService:
    """Service for validating container names against the database"""

    def __init__(self):
        self.connection_params = {
            'host': settings.POSTGRES_HOST,
            'port': settings.POSTGRES_PORT,
            'database': settings.POSTGRES_DATABASE,
            'user': settings.POSTGRES_USER,
            'password': settings.POSTGRES_PASSWORD,
            'connect_timeout': 3  # 3 second timeout for connection attempts
        }
        self._connection = None
        self._available_containers_cache = None

    def _get_connection(self):
        """Get or create database connection"""
        try:
            if self._connection is None or self._connection.closed:
                self._connection = psycopg2.connect(**self.connection_params)
                logger.info("Connected to PostgreSQL for container validation")
            return self._connection
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise ContainerValidationError(f"Database connection failed: {e}")

    def _execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """Execute a database query and return results"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise ContainerValidationError(f"Database query failed: {e}")

    def validate_container(self, container_name: str) -> bool:
        """
        Validate if a container name exists in the rag_departments table

        Args:
            container_name: The container name to validate

        Returns:
            bool: True if container exists and is active, False otherwise

        Raises:
            ContainerValidationError: If database connection or query fails
        """
        try:
            # Always allow 'general' as a fallback collection
            if container_name == "general":
                logger.info(f"Container validation for '{container_name}': valid (always allowed as fallback)")
                return True
                
            query = """
                SELECT COUNT(*) FROM rag_departments
                WHERE name = %s AND status = 'active'
            """
            results = self._execute_query(query, (container_name,))

            is_valid = results[0][0] > 0 if results else False
            logger.info(f"Container validation for '{container_name}': {'valid' if is_valid else 'invalid'}")
            return is_valid

        except Exception as e:
            logger.warning(f"Database unavailable, using fallback validation: {e}")
            # Fallback: only allow 'general' collection when database is not accessible
            if container_name == "general":
                logger.info(f"Fallback validation for '{container_name}': valid (database unavailable)")
                return True
            else:
                logger.warning(f"Fallback validation for '{container_name}': invalid (only 'general' allowed when database unavailable)")
                return False

    def get_available_containers(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of all available containers from the database

        Args:
            force_refresh: Force refresh of cached data

        Returns:
            List of container dictionaries with name, description, and metadata
        """
        if self._available_containers_cache is None or force_refresh:
            try:
                query = """
                    SELECT id, name, description, icon, color, keywords, monthly_queries
                    FROM rag_departments
                    WHERE status = 'active'
                    ORDER BY name
                """
                results = self._execute_query(query)

                containers = []
                for row in results:
                    containers.append({
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'icon': row[3],
                        'color': row[4],
                        'keywords': row[5],
                        'monthly_queries': row[6]
                    })

                # Always add 'general' as a fallback container
                containers.append({
                    'id': 0,
                    'name': 'general',
                    'description': 'General knowledge collection (fallback)',
                    'icon': '📁',
                    'color': 'blue',
                    'keywords': '["general", "all", "default"]',
                    'monthly_queries': 0
                })

                self._available_containers_cache = containers
                logger.info(f"Retrieved {len(containers)} available containers from database (including 'general' fallback)")

            except Exception as e:
                logger.warning(f"Database unavailable for container list, using fallback: {e}")
                # Fallback: return only 'general' collection when database is not accessible
                self._available_containers_cache = [
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
                logger.info("Using fallback container list with 'general' only")

        return self._available_containers_cache


    def get_container_collection_name(self, container_name: str) -> str:
        """
        Get collection name for a container (now uses department names directly)

        Args:
            container_name: The container/department name

        Returns:
            Department name to use as collection name (can include Korean names)

        Raises:
            ContainerValidationError: If container is not found
        """
        try:
            containers = self.get_available_containers()

            for container in containers:
                if container['name'] == container_name:
                    # Return the department name directly as collection name
                    return container['name']

            available_names = [c['name'] for c in containers]
            raise ContainerValidationError(
                f"Container '{container_name}' not found. Available containers: {available_names}"
            )
            
        except Exception as e:
            logger.warning(f"Database unavailable for container mapping, using fallback: {e}")
            # Fallback when database is not accessible - use simple name mapping
            if container_name == "general":
                return "general"
            else:
                # For any other container, return 'general' as fallback
                logger.warning(f"Container '{container_name}' not available, falling back to 'general'")
                return "general"

    def get_container_collection_id(self, container_name: str) -> str:
        """
        Get the collection name for a container (now uses department names directly)

        Args:
            container_name: The container/department name

        Returns:
            Department name to use as collection name (can include Korean names)

        Raises:
            ContainerValidationError: If container is not found
        """
        containers = self.get_available_containers()

        for container in containers:
            if container['name'] == container_name:
                # Return the department name directly as collection name
                return container['name']

        available_names = [c['name'] for c in containers]
        raise ContainerValidationError(
            f"Container '{container_name}' not found. Available containers: {available_names}"
        )

    def get_container_by_collection_name(self, collection_name: str) -> Dict[str, Any]:
        """
        Get container info by collection name (department name)

        Args:
            collection_name: The collection name (department name)

        Returns:
            Container dictionary with full information

        Raises:
            ContainerValidationError: If collection name is not found
        """
        containers = self.get_available_containers()

        for container in containers:
            if container['name'] == collection_name:
                return container

        available_names = [c['name'] for c in containers]
        raise ContainerValidationError(
            f"Collection name '{collection_name}' not found. Available names: {available_names}"
        )

    def get_container_names(self) -> List[str]:
        """Get just the list of available container names"""
        containers = self.get_available_containers()
        return [container['name'] for container in containers]

    def validate_container_with_suggestions(self, container_name: str) -> Dict[str, Any]:
        """
        Validate container and provide suggestions if invalid

        Args:
            container_name: The container name to validate

        Returns:
            Dict with validation result and suggestions
        """
        is_valid = self.validate_container(container_name)

        result = {
            'valid': is_valid,
            'container': container_name
        }

        if not is_valid:
            available_containers = self.get_available_containers()
            result.update({
                'error': f"Container '{container_name}' does not exist or is inactive",
                'available_containers': [c['name'] for c in available_containers],
                'suggestions': self._get_similar_containers(container_name, available_containers)
            })

        return result

    def _get_similar_containers(self, container_name: str, available_containers: List[Dict[str, Any]]) -> List[str]:
        """Get suggestions for similar container names"""
        suggestions = []
        container_lower = container_name.lower()

        for container in available_containers:
            name = container['name'].lower()
            keywords = container.get('keywords', '[]')

            # Simple similarity matching
            if container_lower in name or name in container_lower:
                suggestions.append(container['name'])
            elif keywords and container_lower in keywords.lower():
                suggestions.append(container['name'])

        return suggestions[:3]  # Return top 3 suggestions

    def close(self):
        """Close database connection"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Closed PostgreSQL connection")


# Global instance
container_validator = ContainerValidationService()