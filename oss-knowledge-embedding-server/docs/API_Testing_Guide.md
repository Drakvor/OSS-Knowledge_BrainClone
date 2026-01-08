# API Testing Guide

This guide provides curl commands to test the Excel processing and search functionality of the OSS Knowledge Embedding Server.

## Prerequisites

1. **Start the server:**

    ```bash
    source venv/bin/activate
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

2. **Ensure storage services are running:**

    ```bash
    # Start Qdrant (Docker)
    docker run -p 6333:6333 qdrant/qdrant

    # Start Neo4j (if not already running)
    # Neo4j should be accessible at neo4j://127.0.0.1:7687
    ```

3. **Verify environment variables are set:**
    - `OPENAI_API_KEY` - For semantic analysis
    - `NEO4J_PASSWORD` - For graph database access

## 1. Excel Processing Endpoint

### Basic Excel Processing

Process an Excel file with semantic chunking and embedding generation:

```bash
curl -X POST "http://localhost:8000/process/excel" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/ITSM Data_Login.xlsx" \
  -F "chunking_strategy=semantic" \
  -F "chunk_size=400" \
  -F "chunk_overlap=50" \
  -F "detect_relationships=true" \
  -F "detect_domains=true" \
  -F "generate_embeddings=true" \
  -F "embedding_model=text-embedding-3-large"
```

### Advanced Excel Processing

Process with specific options and sheet filtering:

```bash
curl -X POST "http://localhost:8000/process/excel" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/ITSM Data_Mobile.xlsx" \
  -F "chunking_strategy=semantic" \
  -F "chunk_size=600" \
  -F "chunk_overlap=100" \
  -F "include_formulas=true" \
  -F "detect_relationships=true" \
  -F "detect_domains=true" \
  -F "generate_embeddings=true" \
  -F "embedding_model=text-embedding-3-large"
```

### Table-based Chunking (Faster Processing)

For faster processing without semantic analysis:

```bash
curl -X POST "http://localhost:8000/process/excel" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/ITSM Data_Login.xlsx" \
  -F "chunking_strategy=table_based" \
  -F "chunk_size=800" \
  -F "chunk_overlap=50" \
  -F "detect_relationships=false" \
  -F "detect_domains=false" \
  -F "generate_embeddings=true"
```

### Expected Response

Successful processing returns:

```json
{
    "job_id": "12345678-1234-5678-9012-123456789012",
    "status": "completed",
    "message": "Excel file 'ITSM Data_Login.xlsx' processed successfully"
}
```

## 2. Search Endpoints

✅ **Search endpoints are now implemented and ready for testing.**

### Similarity Search

Perform semantic similarity search using BGE-M3 embeddings:

```bash
curl -X POST "http://localhost:8000/search/similarity" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "서버 성능 모니터링 문제",
    "limit": 5,
    "threshold": 0.7
  }'
```

### Graph Traversal Search

Explore relationships between chunks using Neo4j:

```bash
curl -X POST "http://localhost:8000/search/graph" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "start_chunk_id": "ITSM Login Data_semantic_ITSM_Data_data_0",
    "relationship_types": ["contains", "RESOLVED_BY"],
    "max_depth": 2,
    "limit": 10
  }'
```

### Hybrid Search

Combine similarity and graph search for comprehensive results:

```bash
curl -X POST "http://localhost:8000/search/hybrid?query=네트워크%20문제&limit=10&similarity_weight=0.7&graph_weight=0.3" \
  -H "accept: application/json"
```

### Search Analytics

Get search and storage statistics:

```bash
curl -X GET "http://localhost:8000/search/analytics" \
  -H "accept: application/json"
```

### Expected Search Response

```json
{
    "query": "서버 성능 모니터링 문제",
    "results": [
        {
            "chunk_id": "ITSM Login Data_semantic_ITSM_Data_data_0",
            "content": "시스템 모니터링 알림: 웹 서버 CPU 사용률이 85%를 초과했습니다. 트래픽 증가로 인한 성능 저하가 예상됩니다.",
            "score": 0.95,
            "source_file": "ITSM Data_Login.xlsx",
            "chunk_type": "data_sample",
            "metadata": {}
        }
    ],
    "total_results": 1,
    "processing_time_ms": 45.2,
    "threshold_used": 0.7
}
```

## 3. Testing Workflow

### Complete Testing Sequence

1. **Check server health:**

    ```bash
    curl -X GET "http://localhost:8000/" \
      -H "accept: application/json"
    ```

2. **Check processing capabilities:**

    ```bash
    curl -X GET "http://localhost:8000/process/capabilities" \
      -H "accept: application/json"
    ```

3. **Process Excel file:**

    ```bash
    curl -X POST "http://localhost:8000/process/excel" \
      -H "accept: application/json" \
      -H "Content-Type: multipart/form-data" \
      -F "file=@data/ITSM Data_Login.xlsx" \
      -F "chunking_strategy=semantic" \
      -F "generate_embeddings=true"
    ```

4. **List processing jobs:**

    ```bash
    curl -X GET "http://localhost:8000/process/jobs" \
      -H "accept: application/json"
    ```

5. **Get job status (use job_id from step 3):**

    ```bash
    curl -X GET "http://localhost:8000/process/status/{job_id}" \
      -H "accept: application/json"
    ```

6. **Test similarity search (after processing is complete):**

    ```bash
    curl -X POST "http://localhost:8000/search/similarity" \
      -H "accept: application/json" \
      -H "Content-Type: application/json" \
      -d '{
        "query": "네트워크 문제",
        "limit": 3,
        "threshold": 0.6
      }'
    ```

7. **Check search analytics:**
    ```bash
    curl -X GET "http://localhost:8000/search/analytics" \
      -H "accept: application/json"
    ```

## 4. Verification

### Verify Processing Results

After successful processing, you can verify the results by:

1. **Checking Qdrant storage:**

    ```bash
    curl -X GET "http://localhost:6333/collections/file_chunks/points/scroll" \
      -H "Content-Type: application/json"
    ```

2. **Checking Neo4j storage:**
   Use Neo4j Browser at `http://localhost:7474` and run:
    ```cypher
    MATCH (n:Chunk) RETURN n LIMIT 10
    ```

### Expected Processing Results

For `ITSM Data_Login.xlsx`:

-   **Chunks created:** ~8 chunks
-   **Embeddings generated:** ~8 embeddings (3072-dimensional Azure OpenAI)
-   **Domain detected:** "IT 서비스 관리 (ITSM)" with high confidence
-   **Relationships found:** ~2 relationships
-   **Processing time:** ~70s (semantic) or ~15s (table-based)

For `ITSM Data_Mobile.xlsx`:

-   **Chunks created:** ~88 chunks (semantic) or ~44 chunks (table-based)
-   **Embeddings generated:** Matching number of embeddings
-   **Domain detected:** ITSM-related domain
-   **Processing time:** ~60s (semantic) or ~20s (table-based)

## 5. Troubleshooting

### Common Issues

1. **File not found error:**

    - Ensure Excel files exist in the `data/` directory
    - Use absolute paths if needed

2. **OpenAI API errors:**

    - Verify `OPENAI_API_KEY` is set correctly
    - Check API key has sufficient credits

3. **Storage connection errors:**

    - Ensure Qdrant is running on port 6333
    - Ensure Neo4j is running with correct credentials

4. **Processing timeout:**
    - Large files may take longer to process
    - Monitor job status using the status endpoint

### Debugging

Enable debug logging by setting:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

## 6. Complete Testing Example

Here's a complete end-to-end test sequence:

```bash
# 1. Start server and check health
curl -X GET "http://localhost:8000/" -H "accept: application/json"

# 2. Process an Excel file
curl -X POST "http://localhost:8000/process/excel" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/ITSM Data_Login.xlsx" \
  -F "chunking_strategy=semantic" \
  -F "generate_embeddings=true"

# 3. Wait a moment for processing, then search
sleep 5

# 4. Test similarity search
curl -X POST "http://localhost:8000/search/similarity" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "서버 연결 오류",
    "limit": 5,
    "threshold": 0.6
  }'

# 5. Check analytics
curl -X GET "http://localhost:8000/search/analytics" \
  -H "accept: application/json"
```

## 7. Next Steps

The system now provides complete functionality:

✅ **Excel processing** with semantic chunking  
✅ **Azure OpenAI embeddings** for Korean text  
✅ **Similarity search** using vector embeddings  
✅ **Graph traversal** using Neo4j relationships  
✅ **Hybrid search** combining both methods

Optional enhancements:

-   **Batch processing** for multiple files
-   **Export endpoints** for processed data
-   **Advanced filtering** by date, source, etc.
-   **Search result ranking** improvements
