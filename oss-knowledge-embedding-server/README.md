# OSS Knowledge Embedding Server

A production-ready FastAPI service for processing Excel and Markdown files with Korean language support using Azure OpenAI text-embedding-3-large embeddings, semantic analysis with LangChain, and dual storage backends (Qdrant vector database and Neo4j graph database).

> **Latest Update**: Fixed Pydantic v2 compatibility issues and added interactive markdown chunking functionality.

## Features

-   **Excel Processing**: Comprehensive Excel file analysis with semantic chunking
-   **Markdown Processing**: Structure-aware hierarchical chunking for technical documentation
-   **Interactive Chunking**: Preview and edit chunks before storage (Markdown only)
-   **Korean Language Support**: Azure OpenAI text-embedding-3-large embeddings (3072 dimensions)
-   **Azure OpenAI Integration**: High-quality text-embedding-3-large model for enhanced multilingual embeddings
-   **Semantic Analysis**: Domain detection and relationship extraction using LangChain
-   **Dual Storage**: Qdrant for vector similarity search + Neo4j for graph relationships
-   **REST API**: FastAPI endpoints for file upload and processing
-   **Production Ready**: Comprehensive error handling, logging, and status tracking
-   **Container Support**: Department-based data isolation with Qdrant collections

## Quick Start

1. Create and activate virtual environment:

    ```bash
    # Create virtual environment
    python -m venv venv

    # Activate virtual environment
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    # venv\Scripts\activate
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Start storage services:

    ```bash
    # Qdrant (Docker)
    docker run -p 6333:6333 qdrant/qdrant

    # Neo4j (local instance at neo4j://127.0.0.1:7687)
    ```

4. Start the server:

    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

5. Test API:
    ```bash
    ./test_api_curl.sh
    ```

## Configuration

### Azure OpenAI Setup

The server uses Azure OpenAI text-embedding-3-large model for generating high-quality embeddings:

```bash
# Required environment variables
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_EMBEDDING_DEPLOYMENT="oss-embedding"
export AZURE_EMBEDDING_MODEL="text-embedding-3-large"
```

### Vector Dimensions

-   **Model**: Azure OpenAI text-embedding-3-large
-   **Dimensions**: 3072 (high-quality multilingual embeddings)
-   **Distance Metric**: Cosine similarity
-   **Batch Size**: 32 (configurable)

### Container Support

The server supports department-based data isolation:

-   **Container Mapping**: Department names → Qdrant collections
-   **Data Isolation**: Each department's data stored in separate collections
-   **Fallback Support**: "general" container for default storage

## API Endpoints

### Core Processing

-   `POST /process/excel` - Process Excel files
-   `POST /process/markdown` - Process Markdown files (auto-chunking)

### Interactive Markdown Processing

-   `POST /process/markdown/preview` - Preview chunking strategy and chunks
-   `POST /process/markdown/confirm` - Process user-edited chunks and store

### Status & Management

-   `GET /process/status/{job_id}` - Get job status
-   `GET /process/jobs` - List all jobs
-   `GET /process/capabilities` - System capabilities
-   `GET /` - Health check

## Processing Results

Successfully processes files into:

### Excel Files

-   **Semantic chunks** with intelligent text splitting
-   **OpenAI text-embedding-3-large embeddings** (3072-dimensional vectors)
-   **Domain classification** (IT Service Management, etc.)
-   **Relationship extraction** between entities
-   **Dual storage** in Qdrant and Neo4j

### Markdown Files

-   **Structure-aware hierarchical chunking** preserving document hierarchy
-   **Azure OpenAI embeddings** (3072-dimensional vectors with text-embedding-3-large)
-   **Interactive workflow** with preview, edit, and confirm phases
-   **Metadata preservation** including structural and semantic information
-   **Container-based storage** for multi-tenant isolation

## Interactive Markdown Workflow

1. **Preview**: Upload markdown → system shows recommended chunks → user reviews
2. **Edit**: User can modify chunk boundaries and content as needed
3. **Confirm**: System processes final chunks → generates embeddings → stores in database

Example workflow:

```bash
# 1. Preview chunks
curl -X POST "http://localhost:8000/process/markdown/preview" \
  -F "file=@document.md" \
  -F "container=my-project"

# 2. User edits chunks in frontend

# 3. Confirm and store
curl -X POST "http://localhost:8000/process/markdown/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "document.md",
    "container": "my-project",
    "chunks": [...edited chunks...],
    "embedding_model": "text-embedding-3-large"
  }'
```

See `docs/` for comprehensive test results and executive summary.
