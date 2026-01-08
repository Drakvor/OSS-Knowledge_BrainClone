"""
Admin API routes for database management
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, List
import logging

from app.core.qdrant_client import QdrantService
from app.services.container_validation_service import container_validator

logger = logging.getLogger(__name__)

router = APIRouter()


def get_qdrant_service(request: Request) -> QdrantService:
    """Dependency to get Qdrant service from app state"""
    return request.app.state.qdrant_service


@router.post("/admin/qdrant/cleanup")
async def cleanup_all_qdrant_collections(
    confirm: bool = False,
    qdrant_service: QdrantService = Depends(get_qdrant_service)
) -> Dict[str, Any]:
    """
    Delete all collections from Qdrant
    WARNING: This will delete ALL vector data!
    """

    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to proceed with cleanup. This will delete ALL vector data!"
        )

    logger.warning("🚨 ADMIN: Qdrant cleanup requested - this will delete ALL collections!")

    try:
        if not qdrant_service.client:
            await qdrant_service.initialize()

        # Get current collections
        collections_response = qdrant_service.client.get_collections()
        collection_names = [col.name for col in collections_response.collections]

        logger.info(f"Found {len(collection_names)} collections to delete: {collection_names}")

        if not collection_names:
            return {
                "status": "success",
                "message": "No collections found. Qdrant is already clean.",
                "collections_deleted": [],
                "total_deleted": 0
            }

        # Delete each collection
        deleted_collections = []
        failed_collections = []

        for collection_name in collection_names:
            try:
                logger.info(f"Deleting collection: {collection_name}")
                qdrant_service.client.delete_collection(collection_name)
                deleted_collections.append(collection_name)
                logger.info(f"Successfully deleted: {collection_name}")
            except Exception as e:
                logger.error(f"Failed to delete {collection_name}: {e}")
                failed_collections.append({"name": collection_name, "error": str(e)})

        # Verify cleanup
        final_collections = qdrant_service.client.get_collections()
        remaining = [col.name for col in final_collections.collections]

        result = {
            "status": "success" if not failed_collections and not remaining else "partial",
            "message": f"Deleted {len(deleted_collections)} collections",
            "collections_deleted": deleted_collections,
            "total_deleted": len(deleted_collections),
            "failed_deletions": failed_collections,
            "remaining_collections": remaining
        }

        if remaining:
            logger.warning(f"Some collections remain after cleanup: {remaining}")
            result["message"] += f", {len(remaining)} collections remain"

        logger.info(f"Cleanup complete: {result}")
        return result

    except Exception as e:
        logger.error(f"Qdrant cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.get("/admin/qdrant/collections")
async def list_all_qdrant_collections(
    qdrant_service: QdrantService = Depends(get_qdrant_service)
) -> Dict[str, Any]:
    """List all Qdrant collections with details"""

    try:
        if not qdrant_service.client:
            await qdrant_service.initialize()

        collections_response = qdrant_service.client.get_collections()
        collections_info = []

        for col in collections_response.collections:
            try:
                # Get detailed collection info
                info = qdrant_service.client.get_collection(col.name)
                collection_detail = {
                    "name": col.name,
                    "points_count": getattr(info, 'points_count', 0),
                    "vectors_count": getattr(info, 'vectors_count', 0),
                    "status": getattr(info, 'status', {}).value if hasattr(getattr(info, 'status', {}), 'value') else 'unknown'
                }

                # Try to get vector size
                try:
                    if hasattr(info, 'config') and hasattr(info.config, 'params'):
                        vectors_config = info.config.params.vectors
                        if hasattr(vectors_config, 'size'):
                            collection_detail["vector_size"] = vectors_config.size
                        if hasattr(vectors_config, 'distance'):
                            collection_detail["distance"] = vectors_config.distance.value
                except:
                    pass

                # Try to map collection name back to container info
                try:
                    # Find container by matching collection name
                    containers = container_validator.get_available_containers()
                    for container in containers:
                        expected_collection = container_validator.get_container_collection_name(container['name'])
                        if expected_collection == col.name:
                            collection_detail["container_name"] = container["name"]
                            collection_detail["container_description"] = container["description"]
                            break
                except:
                    pass

                collections_info.append(collection_detail)

            except Exception as e:
                logger.warning(f"Could not get details for collection {col.name}: {e}")
                collections_info.append({
                    "name": col.name,
                    "error": str(e)
                })

        return {
            "total_collections": len(collections_info),
            "collections": collections_info
        }

    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@router.get("/admin/qdrant/status")
async def get_qdrant_status(
    qdrant_service: QdrantService = Depends(get_qdrant_service)
) -> Dict[str, Any]:
    """Get Qdrant connection status and summary"""

    try:
        if not qdrant_service.client:
            await qdrant_service.initialize()

        # Test connection and get basic info
        collections_response = qdrant_service.client.get_collections()
        total_collections = len(collections_response.collections)

        total_points = 0
        for col in collections_response.collections:
            try:
                info = qdrant_service.client.get_collection(col.name)
                total_points += getattr(info, 'points_count', 0)
            except:
                pass

        return {
            "status": "connected",
            "host": qdrant_service.host,
            "port": qdrant_service.port,
            "total_collections": total_collections,
            "total_points": total_points,
            "base_collection_name": qdrant_service.collection_name
        }

    except Exception as e:
        logger.error(f"Qdrant status check failed: {e}")
        return {
            "status": "disconnected",
            "error": str(e),
            "host": getattr(qdrant_service, 'host', 'unknown'),
            "port": getattr(qdrant_service, 'port', 'unknown')
        }


@router.get("/admin/containers/mapping")
async def get_container_collection_mapping() -> Dict[str, Any]:
    """Get mapping between container names and Qdrant collection IDs"""

    try:
        containers = container_validator.get_available_containers()

        mapping_info = []
        for container in containers:
            container_name = container['name']
            collection_name = container_validator.get_container_collection_name(container_name)

            mapping_info.append({
                "container_name": container_name,
                "collection_name": collection_name,
                "description": container['description'],
                "icon": container['icon'],
                "keywords": container['keywords'],
                "monthly_queries": container['monthly_queries']
            })

        return {
            "total_containers": len(mapping_info),
            "mapping": mapping_info,
            "note": "Qdrant collections use readable English names/slugs"
        }

    except Exception as e:
        logger.error(f"Failed to get container mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get container mapping: {str(e)}")