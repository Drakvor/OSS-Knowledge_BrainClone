# OSS Knowledge Context Manager Service

Handles chat context building, mem0 integration, and memory management for the agentic RAG system.

## Architecture

The Context Manager service provides context building and memory management:

```
Orchestrator
  ↓
Context Manager (Port 8005)
  ├─ Backend Client (Port 8080) - Chat history retrieval
  ├─ Mem0 Client (Port 8005) - Memory search and storage
  └─ Attachment text extraction
```

## Responsibilities

- **Context Building**: Builds enriched chat context with:
  - Sliding window chat history (last 6 messages = 3 turns)
  - User memories from mem0 (long-term)
  - Session memories from mem0 (short-term)
  - Attachment text extraction
  - Context summary integration

- **Memory Management**: Handles mem0 operations:
  - Search user and session memories
  - Add conversation memories with importance detection
  - Trigger mem0 inference for important conversations

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running

```bash
# Development mode
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8005 --reload
```

## Endpoints

- `GET /health` - Health check endpoint
- `GET /` - Service information
- `GET /docs` - API documentation (Swagger)
- `POST /context/build` - Build complete chat context
- `POST /memory/add` - Add conversation to mem0
- `POST /memory/search` - Search mem0 memories

## Environment Variables

- `BACKEND_URL` - Backend service URL (default: http://localhost:8080)
- `MEM0_URL` - Mem0 service URL (default: http://localhost:8005)
- `SLIDING_WINDOW_SIZE` - Number of messages in sliding window (default: 6)
- `MEM0_AUTO_SAVE_IMPORTANT` - Auto-save all conversations as important (default: true)
- `LOG_LEVEL` - Logging level (default: INFO)

## Development Status

**Phase 2**: ✅ Service foundation complete
- Basic FastAPI app structure
- Health check endpoint
- Context building with sliding window
- Mem0 integration (search, add, infer)
- Backend client for chat history
- Attachment text extraction

**Next Phases**:
- Phase 9: Orchestrator - Context Manager Integration
- Phase 10: Orchestrator - Intent Classifier Integration

## Related Services

- [Orchestrator](../oss-knowledge-orchestrator/) - Central coordination service
- [Backend](../oss-knowledge-backend/) - Database operations and persistence
- [Mem0](../mem0-azure-deployment/) - Memory service for user/session memories

