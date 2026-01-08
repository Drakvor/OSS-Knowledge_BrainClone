"""
Metadata Sync Service

This service handles synchronization of document metadata between the embedding backend
and the Java backend after successful document processing.
"""

import logging
import httpx
from typing import Optional, Dict, Any
from app.config.settings import settings

logger = logging.getLogger(__name__)


class MetadataSyncService:
    """Service for syncing document metadata with Java backend"""
    
    def __init__(self):
        self.java_backend_url = settings.JAVA_BACKEND_URL
        self.timeout = 30.0
        
    async def sync_document_metadata(
        self,
        document_name: str,
        document_path: str,
        file_type: str,
        file_size: int,
        container: str,
        embedding_status: str = "embedded"
    ) -> Dict[str, Any]:
        """
        Sync document metadata with Java backend after successful embedding
        
        Args:
            document_name: Name of the document
            document_path: Path where document is stored
            file_type: Type of the file (e.g., 'markdown', 'excel')
            file_size: Size of the file in bytes
            container: Container/department name
            embedding_status: Status of embedding process
            
        Returns:
            Dict containing sync result
        """
        
        if not self.java_backend_url:
            logger.warning("Java backend URL not configured, skipping metadata sync")
            return {
                "success": False,
                "error": "Java backend URL not configured",
                "skipped": True
            }
        
        payload = {
            "documentName": document_name,
            "documentPath": document_path,
            "fileType": file_type,
            "fileSize": file_size,
            "container": container,
            "embeddingStatus": embedding_status
        }
        
        try:
            logger.info(f"Syncing document metadata for {document_name} in container {container}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.java_backend_url}/documents/add-after-embedding",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Successfully synced metadata for {document_name}: {result}")
                    return {
                        "success": True,
                        "data": result,
                        "message": f"Metadata synced successfully for {document_name}"
                    }
                else:
                    error_msg = f"Failed to sync metadata: HTTP {response.status_code}"
                    logger.error(f"{error_msg} - Response: {response.text}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "response": response.text
                    }
                    
        except httpx.TimeoutException:
            error_msg = f"Timeout while syncing metadata for {document_name}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "timeout": True
            }
            
        except httpx.ConnectError:
            error_msg = f"Cannot connect to Java backend at {self.java_backend_url}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "connection_error": True
            }
            
        except Exception as e:
            error_msg = f"Unexpected error while syncing metadata for {document_name}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "exception": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if Java backend is accessible
        
        Returns:
            Dict containing health check result
        """
        
        if not self.java_backend_url:
            return {
                "healthy": False,
                "error": "Java backend URL not configured"
            }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.java_backend_url}/actuator/health")
                
                if response.status_code == 200:
                    return {
                        "healthy": True,
                        "url": self.java_backend_url,
                        "status": "connected"
                    }
                else:
                    return {
                        "healthy": False,
                        "url": self.java_backend_url,
                        "status": f"HTTP {response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "healthy": False,
                "url": self.java_backend_url,
                "error": str(e)
            }


# Global instance
metadata_sync_service = MetadataSyncService()
