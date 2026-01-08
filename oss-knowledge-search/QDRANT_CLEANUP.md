# Qdrant Database Cleanup Guide

This document describes how to clean up all data from Qdrant vector database to remove old test collections and start fresh with the correct container-specific collection structure.

## Background

The OSS Knowledge system previously used a single "file_chunks" collection for all data. The architecture has been updated to use readable English collection names that avoid encoding issues with Korean department names.

Examples:
- `test` for test container
- `general` for general container
- `report-management` for 보고관리팀 (report management team)
- `safety-management` for 안전관리팀 (safety management team)
- `maintenance-team` for 정비관리팀 (maintenance team)
- `wm-field-team` for WM 현장팀 (WM field team)

Collection names use English slugs for Korean departments and lowercase English names for existing English departments.

## Cleanup Methods

### Method 1: API Endpoint (Recommended)

Use the admin API endpoint to clean up Qdrant remotely:

```bash
# 1. Check container to collection name mapping
curl -X GET "http://search.4.230.158.187.nip.io/admin/containers/mapping"

# 2. Check current collections
curl -X GET "http://search.4.230.158.187.nip.io/admin/qdrant/collections"

# 3. Check Qdrant status
curl -X GET "http://search.4.230.158.187.nip.io/admin/qdrant/status"

# 4. Clean up all collections (WARNING: Deletes ALL data!)
curl -X POST "http://search.4.230.158.187.nip.io/admin/qdrant/cleanup?confirm=true"
```

### Method 2: Server-Side Script

If you have access to the server where Qdrant is running:

```bash
# 1. Copy the cleanup script to the server
scp scripts/cleanup_qdrant_server.py user@server:/tmp/

# 2. Run the script on the server
python3 /tmp/cleanup_qdrant_server.py --host localhost --port 6333

# 3. Or with auto-confirmation
python3 /tmp/cleanup_qdrant_server.py --host localhost --port 6333 --confirm
```

### Method 3: Direct Qdrant API

If you have direct access to Qdrant:

```bash
# 1. List all collections
curl -X GET "http://qdrant-host:6333/collections"

# 2. Delete each collection individually
curl -X DELETE "http://qdrant-host:6333/collections/{collection_name}"

# Example:
curl -X DELETE "http://qdrant-host:6333/collections/file_chunks"
```

## After Cleanup

After cleaning up Qdrant:

1. **Re-process files**: Use the embedding server to re-process files into the new container-specific collections
2. **Verify collections**: Check that new collections use readable English names/slugs
3. **Test search**: Verify that search works with the new collection structure

## API Endpoints Reference

### Container Mapping
```
GET /admin/containers/mapping
```
Returns mapping between container names and readable Qdrant collection names.

### List Collections
```
GET /admin/qdrant/collections
```
Returns detailed information about all Qdrant collections.

### Qdrant Status
```
GET /admin/qdrant/status
```
Returns Qdrant connection status and summary.

### Cleanup All Collections
```
POST /admin/qdrant/cleanup?confirm=true
```
**WARNING**: Deletes ALL collections and vector data from Qdrant!

## Safety Notes

⚠️ **WARNING**: Cleanup operations are **irreversible** and will delete ALL vector embeddings!

- Always backup important data before cleanup
- Verify you have the source files to re-process embeddings
- Test cleanup on development environment first
- Use `confirm=true` parameter to proceed with deletion

## Troubleshooting

### Connection Issues
If you can't connect to Qdrant:
- Check if Qdrant service is running
- Verify network connectivity and firewall rules
- Confirm Qdrant host/port configuration

### Permission Issues
If cleanup fails:
- Check Qdrant service permissions
- Verify API access rights
- Ensure Qdrant is not in read-only mode

### Partial Cleanup
If some collections remain after cleanup:
- Try deleting remaining collections individually
- Check Qdrant logs for error messages
- Restart Qdrant service if necessary

## Example Workflow

Complete cleanup and restart workflow:

```bash
# 1. Backup current state (optional)
curl -X GET "http://search.4.230.158.187.nip.io/admin/qdrant/collections" > collections_backup.json

# 2. Clean up all data
curl -X POST "http://search.4.230.158.187.nip.io/admin/qdrant/cleanup?confirm=true"

# 3. Verify cleanup
curl -X GET "http://search.4.230.158.187.nip.io/admin/qdrant/status"

# 4. Re-process files using embedding server
curl -X POST "http://embedding.4.230.158.187.nip.io/process/excel" \
  -F "file=@test_file.xlsx" \
  -F "container=test"

# 5. Verify new collections created
curl -X GET "http://search.4.230.158.187.nip.io/admin/qdrant/collections"

# 6. Test search functionality
curl -X POST "http://search.4.230.158.187.nip.io/search/similarity" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "collection": "test"}'
```