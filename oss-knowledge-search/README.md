# OSS Knowledge Search Server

A dedicated search service for the OSS Knowledge platform that provides comprehensive search capabilities across vector and graph databases.

## Features

-   **Vector Search**: Semantic similarity search using Qdrant vector database
-   **Graph Search**: Relationship-based search using Neo4j graph database
-   **Hybrid Search**: Combined vector and graph search for enhanced results
-   **Multi-modal Search**: Support for various content types (text, documents, etc.)
-   **Real-time Search**: Fast, scalable search API
-   **Azure OpenAI Integration**: High-quality text-embedding-3-large embeddings (3072 dimensions)
-   **Container Support**: Department-based search with data isolation
-   **Response Generation**: LLM-powered answer generation with search context

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │  Search Server  │    │   Databases     │
│                 │────│                 │────│                 │
│ • Web UI        │    │ • Vector Search │    │ • Qdrant (Vec)  │
│ • Mobile App    │    │ • Graph Search  │    │ • Neo4j (Graph) │
│ • API Clients   │    │ • Hybrid Search │    │ • Azure OpenAI  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## API Endpoints

### Vector Search

-   `POST /search/similarity` - Semantic similarity search
-   `POST /search/similarity/batch` - Batch similarity search

### Graph Search

-   `POST /search/graph` - Graph traversal search
-   `POST /search/relationships` - Relationship discovery

### Hybrid Search

-   `POST /search/hybrid` - Combined vector + graph search
-   `POST /search/comprehensive` - Advanced multi-modal search

### Analytics

-   `GET /search/analytics` - Search usage analytics
-   `GET /search/suggestions` - Search suggestions

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
export NEO4J_URI=neo4j://localhost:7687
export AZURE_OPENAI_ENDPOINT=your-endpoint
export AZURE_OPENAI_API_KEY=your-key
export AZURE_EMBEDDING_DEPLOYMENT=oss-embedding
export AZURE_EMBEDDING_MODEL=text-embedding-3-large

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

## Configuration

### Azure OpenAI Setup

The search server uses Azure OpenAI for embedding generation and response synthesis:

```bash
# Required for embedding generation
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_EMBEDDING_DEPLOYMENT="oss-embedding"
export AZURE_EMBEDDING_MODEL="text-embedding-3-large"

# Optional for response generation
export AZURE_OPENAI_CHAT_DEPLOYMENT="oss-chat"
export AZURE_OPENAI_CHAT_MODEL="gpt-4"
```

### Vector Configuration

-   **Model**: Azure OpenAI text-embedding-3-large
-   **Dimensions**: 3072 (high-quality multilingual embeddings)
-   **Distance Metric**: Cosine similarity
-   **Collection Support**: Department-based collections for data isolation

## Environment Variables

| Variable                       | Description                     | Default                  |
| ------------------------------ | ------------------------------- | ------------------------ |
| `QDRANT_HOST`                  | Qdrant vector database host     | `localhost`              |
| `QDRANT_PORT`                  | Qdrant vector database port     | `6333`                   |
| `NEO4J_URI`                    | Neo4j graph database URI        | `neo4j://localhost:7687` |
| `NEO4J_USERNAME`               | Neo4j username                  | `neo4j`                  |
| `NEO4J_PASSWORD`               | Neo4j password                  | `password`               |
| `AZURE_OPENAI_ENDPOINT`        | Azure OpenAI service endpoint   | -                        |
| `AZURE_OPENAI_API_KEY`         | Azure OpenAI API key            | -                        |
| `AZURE_EMBEDDING_DEPLOYMENT`   | Azure embedding deployment name | `oss-embedding`          |
| `AZURE_EMBEDDING_MODEL`        | Azure embedding model           | `text-embedding-3-large` |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Azure chat deployment name      | `oss-chat`               |
| `AZURE_OPENAI_CHAT_MODEL`      | Azure chat model                | `gpt-4`                  |
| `VECTOR_SIZE`                  | Embedding vector dimensions     | `3072`                   |
| `LOG_LEVEL`                    | Logging level                   | `INFO`                   |
| `DEBUG`                        | Debug mode                      | `false`                  |

## Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run with hot reload
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

## Debugging & Monitoring

### 유사도 측정 (Similarity Score Logging)

검색 결과의 유사도 점수를 확인하려면 다음 파일들에서 주석을 해제하세요:

**파일: `app/services/search_service.py` (라인 ~188-195)**
```python
# 유사도 측정 주석
# Log similarity scores for each result
if results:
    scores = [result.score for result in results]
    print(f"[SEARCH] Similarity scores - min={min(scores):.4f}, max={max(scores):.4f}, avg={sum(scores)/len(scores):.4f}")
    for i, result in enumerate(results[:5], 1):
        print(f"[SEARCH]   Result {i}: score={result.score:.4f}, source={result.source_file[:50]}")
```

**파일: `app/api/routes/search.py` (라인 ~498-504, ~406-412)**
```python
# 유사도 측정 주석
# Log similarity scores for search results
if search_results:
    scores = [result.score for result in search_results]
    print(f"[API] Search similarity scores - min={min(scores):.4f}, max={max(scores):.4f}, avg={sum(scores)/len(scores):.4f}")
    for i, result in enumerate(search_results[:3], 1):
        print(f"[API]   Top {i}: score={result.score:.4f}, source={result.source_file[:50]}...")
```

**유사도 점수 해석:**
- 0.9 이상: 매우 강한 관련성
- 0.7~0.9: 강한 관련성
- 0.5~0.7: 보통 수준의 관련성
- 0.3~0.5: 낮은 관련성
- 0.3 미만: 매우 낮은 관련성

**참고:** 검색 라벨은 `[SEARCH]`, `[API]`, `[STREAM]`으로 구분되어 있어 각 검색 경로의 유사도를 추적할 수 있습니다.

## Deployment

The service is designed to be deployed alongside the OSS Knowledge ecosystem:

-   **Port**: 8004 (to avoid conflicts with embedding server on 8000 and backend on 8080)
-   **Health Checks**: `/health`, `/ready`, `/live` endpoints
-   **Monitoring**: Prometheus metrics on `/metrics`
-   **Documentation**: OpenAPI docs on `/docs`

## Integration

This search server is designed to replace search functionality in the embedding server:

1. **Migration Path**: Gradually move search endpoints from embedding server
2. **Service Separation**: Embedding server focuses on processing, search server handles queries
3. **Shared Storage**: Both services use same Qdrant and Neo4j instances
4. **API Compatibility**: Maintains backward compatibility during transition
