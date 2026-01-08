#!/usr/bin/env python3
"""
Server-side script to clean up all Qdrant collections
This should be run on the server where Qdrant is accessible

Usage:
    python cleanup_qdrant_server.py [--host HOST] [--port PORT] [--confirm]
"""

import argparse
import logging
import sys
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_qdrant(host="localhost", port=6333, confirm=False):
    """Delete all collections from Qdrant"""

    if not confirm:
        print("⚠️  WARNING: This will delete ALL data from Qdrant!")
        print(f"Target server: {host}:{port}")
        response = input("Are you sure you want to continue? Type 'YES' to confirm: ")
        if response != "YES":
            print("Operation cancelled.")
            return False

    try:
        logger.info(f"Connecting to Qdrant at {host}:{port}")

        # Initialize client
        client = QdrantClient(
            host=host,
            port=port,
            timeout=30
        )

        # Test connection
        try:
            client.get_collections()
            logger.info("✅ Successfully connected to Qdrant")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            return False

        # Get all collections
        collections_response = client.get_collections()
        collections = [col.name for col in collections_response.collections]

        logger.info(f"Found {len(collections)} collections:")
        for i, collection in enumerate(collections, 1):
            # Get collection info
            try:
                info = client.get_collection(collection)
                points_count = info.points_count if hasattr(info, 'points_count') else "unknown"
                logger.info(f"  {i}. {collection} ({points_count} points)")
            except:
                logger.info(f"  {i}. {collection} (info unavailable)")

        if not collections:
            logger.info("✅ No collections found. Qdrant is already clean.")
            return True

        # Delete each collection
        deleted_count = 0
        for collection_name in collections:
            try:
                logger.info(f"🗑️  Deleting collection: {collection_name}")
                client.delete_collection(collection_name)
                logger.info(f"✅ Successfully deleted: {collection_name}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to delete {collection_name}: {e}")

        # Verify cleanup
        logger.info("🔍 Verifying cleanup...")
        final_collections = client.get_collections()
        remaining = [col.name for col in final_collections.collections]

        if remaining:
            logger.warning(f"⚠️  Some collections remain: {remaining}")
            return False
        else:
            logger.info(f"✅ Cleanup complete! Deleted {deleted_count} collections. Qdrant is now clean.")
            return True

    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Clean up all Qdrant collections")
    parser.add_argument("--host", default="localhost", help="Qdrant host (default: localhost)")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port (default: 6333)")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()

    success = cleanup_qdrant(args.host, args.port, args.confirm)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()