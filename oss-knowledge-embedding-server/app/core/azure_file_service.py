"""
Azure File Share Service
Handles file uploads to Azure File Share and generates SAS token URLs for downloads
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import io

try:
    from azure.storage.fileshare import ShareFileClient, ShareClient
    from azure.storage.fileshare import generate_account_sas, AccountSasPermissions, ResourceTypes
    from azure.core.exceptions import AzureError
    from azure.storage.fileshare import generate_file_sas, FileSasPermissions
    from azure.storage.fileshare import ShareServiceClient
    AZURE_STORAGE_AVAILABLE = True
except ImportError:
    AZURE_STORAGE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Azure Storage SDK not available. Install with: pip install azure-storage-file-share")

from app.config import settings

logger = logging.getLogger(__name__)


class AzureFileService:
    """Azure File Share service for uploading files and generating download links"""
    
    def __init__(self):
        self.connection_string: Optional[str] = None
        self.share_name: Optional[str] = None
        self.sas_token_expiry_hours: int = 1
        self.share_client = None
        self.service_client = None
        self.account_name = None
        self.account_key = None
        self.initialized = False
        self._init_attempted = False
    
    def _ensure_initialized(self):
        """Lazy initialization - only initialize when first needed"""
        if self._init_attempted:
            return
        
        self._init_attempted = True
        
        if not AZURE_STORAGE_AVAILABLE:
            logger.warning("Azure Storage SDK not available. File uploads will be disabled.")
            return
        
        # Get settings (may not be loaded at module import time)
        try:
            self.connection_string = getattr(settings, 'AZURE_STORAGE_CONNECTION_STRING', None)
            self.share_name = getattr(settings, 'AZURE_FILE_SHARE_NAME', None)
            self.sas_token_expiry_hours = getattr(settings, 'AZURE_SAS_TOKEN_EXPIRY_HOURS', 1)
        except Exception as e:
            logger.warning(f"Could not read Azure settings: {e}")
            return
            
        if not self.connection_string or not self.share_name:
            logger.warning("Azure File Share not configured. Set AZURE_STORAGE_CONNECTION_STRING and AZURE_FILE_SHARE_NAME")
            return
        
        try:
            self.share_client = ShareClient.from_connection_string(
                conn_str=self.connection_string,
                share_name=self.share_name
            )
            # Also create service client for SAS token generation
            self.service_client = ShareServiceClient.from_connection_string(
                conn_str=self.connection_string
            )
            # Extract account name and key from connection string
            self._parse_connection_string()
            self.initialized = True
            logger.info(f"Azure File Service initialized - Share: {self.share_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Azure File Service: {e}")
            self.initialized = False
    
    def _parse_connection_string(self):
        """Parse connection string to extract account name and key"""
        self.account_name = None
        self.account_key = None
        
        if not self.connection_string:
            return
        
        try:
            parts = dict(part.split('=', 1) for part in self.connection_string.split(';') if '=' in part)
            self.account_name = parts.get('AccountName')
            self.account_key = parts.get('AccountKey')
        except Exception as e:
            logger.warning(f"Failed to parse connection string: {e}")
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        container: str = "general"
    ) -> Dict[str, Any]:
        """
        Upload file to Azure File Share
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            container: Container/department name for organization
            
        Returns:
            Dict with upload_status ("completed" or "failed"), azure_file_path, and error_message if failed
        """
        # Lazy initialization on first use
        self._ensure_initialized()
        
        if not self.initialized:
            logger.warning("Azure File Service not initialized. Skipping upload.")
            return {
                "upload_status": "failed",
                "azure_file_path": None,
                "error_message": "Azure File Service not configured"
            }
        
        try:
            # Sanitize filename to prevent path injection
            import os
            safe_filename = os.path.basename(filename).replace('..', '').replace('/', '').replace('\\', '')
            if not safe_filename:
                safe_filename = "unnamed_file"
            
            # Organize files by container: {container}/{filename}
            file_path = f"{container}/{safe_filename}"
            
            # Create directory if it doesn't exist
            directory_path = f"{container}"
            try:
                self.share_client.create_directory(directory_path)
            except Exception as e:
                # Directory might already exist, which is fine
                # Check if it's a specific "already exists" error (Azure returns 409 or specific message)
                error_str = str(e).lower()
                if "already exists" in error_str or "409" in error_str or "resourcealreadyexists" in error_str:
                    # Directory exists, which is fine
                    pass
                else:
                    # For other errors, log but continue - Azure might create it automatically
                    logger.warning(f"Error creating directory {directory_path}: {e}")
                    # Don't fail upload if directory creation fails
            
            # Upload file
            file_client = self.share_client.get_file_client(file_path)
            # upload_file takes data and length parameters
            file_client.upload_file(data=file_content, length=len(file_content))
            
            logger.info(f"Successfully uploaded file to Azure File Share: {file_path}")
            
            return {
                "upload_status": "completed",
                "azure_file_path": file_path,
                "error_message": None
            }
            
        except Exception as e:
            error_msg = f"Failed to upload file to Azure File Share: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "upload_status": "failed",
                "azure_file_path": None,
                "error_message": str(e)
            }
    
    def download_file(self, file_path: str) -> Optional[bytes]:
        """
        Download file content from Azure File Share
        
        Args:
            file_path: Path to file in Azure File Share (e.g., "container/filename.md")
            
        Returns:
            File content as bytes or None if download fails
        """
        # Lazy initialization on first use
        self._ensure_initialized()
        
        if not self.initialized or not file_path:
            if not self.initialized:
                logger.warning("Azure File Service not initialized. Cannot download file.")
            return None
        
        try:
            file_client = self.share_client.get_file_client(file_path)
            file_content = file_client.download_file().readall()
            logger.info(f"Successfully downloaded file from Azure File Share: {file_path}")
            return file_content
        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {e}", exc_info=True)
            return None
    
    def generate_download_url(self, file_path: str, base_url: Optional[str] = None) -> Optional[str]:
        """
        Generate proxy endpoint URL for file download (no SAS tokens needed)
        
        Args:
            file_path: Path to file in Azure File Share (e.g., "container/filename.md")
            base_url: Optional base URL for the embedding server (defaults to settings or localhost)
            
        Returns:
            Proxy endpoint URL or None if generation fails
        """
        # Lazy initialization on first use
        self._ensure_initialized()
        
        if not self.initialized or not file_path:
            if not self.initialized:
                logger.warning("Azure File Service not initialized. Cannot generate download URL.")
            return None
        
        try:
            # Use backend proxy endpoint instead of SAS tokens
            # This avoids all SAS token signature issues
            from urllib.parse import quote
            from app.config import settings
            
            encoded_path = quote(file_path, safe='')
            # Get the base URL from parameter, settings, or use default
            if not base_url:
                base_url = getattr(settings, 'EMBEDDING_SERVER_URL', None)
            if not base_url:
                # Try to get from HOST and PORT settings
                host = getattr(settings, 'HOST', 'localhost')
                port = getattr(settings, 'PORT', 8000)
                # Use http for localhost/0.0.0.0, https for others (can be overridden via env var)
                # 0.0.0.0 means "all interfaces" but we should use localhost for the URL
                if host == '0.0.0.0':
                    host = 'localhost'
                protocol = 'https' if host != 'localhost' and host != '127.0.0.1' else 'http'
                base_url = f"{protocol}://{host}:{port}"
            
            download_url = f"{base_url}/qdrant/collections/files/download?path={encoded_path}"
            
            logger.info(f"Generated proxy download URL for {file_path}: {download_url}")
            return download_url
            
        except Exception as e:
            logger.error(f"Failed to generate download URL for {file_path}: {e}", exc_info=True)
            return None


# Global instance
azure_file_service = AzureFileService()

