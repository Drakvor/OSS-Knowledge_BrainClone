#!/usr/bin/env python3
"""
Script to clean up all Qdrant collections
"""

import asyncio
import logging
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def cleanup_qdrant():
    """Delete all collections from Qdrant"""

    # Qdrant configuration (matching the app config)
    QDRANT_HOST = "localhost"
    QDRANT_PORT = 6333

    try:
        # Initialize client
        client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
            timeout=30
        )

        logger.info(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")

        # Get all collections
        collections_response = client.get_collections()
        collections = [col.name for col in collections_response.collections]

        logger.info(f"Found {len(collections)} collections: {collections}")

        if not collections:
            logger.info("No collections found. Qdrant is already clean.")
            return

        # Delete each collection
        for collection_name in collections:
            try:
                logger.info(f"Deleting collection: {collection_name}")
                client.delete_collection(collection_name)
                logger.info(f"Successfully deleted collection: {collection_name}")
            except Exception as e:
                logger.error(f"Failed to delete collection {collection_name}: {e}")

        # Verify cleanup
        final_collections = client.get_collections()
        remaining = [col.name for col in final_collections.collections]

        if remaining:
            logger.warning(f"Some collections remain: {remaining}")
        else:
            logger.info("✅ All collections successfully deleted. Qdrant is now clean.")

    except Exception as e:
        logger.error(f"Failed to connect to Qdrant or cleanup failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(cleanup_qdrant())