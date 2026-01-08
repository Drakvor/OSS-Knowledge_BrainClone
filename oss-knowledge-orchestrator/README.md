# OSS Knowledge Orchestrator Service

Central coordination service for the agentic RAG system. Coordinates between Intent Classifier, Task Planner, Search Server, and Backend services.

## Architecture

The Orchestrator service sits at the center of the microservices architecture:

```
Frontend
  ↓
Orchestrator (Port 8000)
  ├─ Intent Classifier (Port 8001)
  ├─ Task Planner (Port 8004)
  ├─ Search Server (Port 8002)
  └─ Backend (Port 8080)
```

## Responsibilities

- **Service Coordination**: Routes requests to appropriate services based on intent
- **Chat Context Management**: Builds and manages chat context (sliding window, attachments)
- **Streaming**: Handles SSE streaming for real-time responses
- **Message Persistence**: Coordinates with Backend for saving messages

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
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints

- `GET /health` - Health check endpoint
- `GET /` - Service information
- `GET /docs` - API documentation (Swagger)

## Environment Variables

(To be added in later phases)

## Development Status

**Phase 1**: ✅ Service foundation complete
- Basic FastAPI app structure
- Health check endpoint
- Placeholder orchestrator logic

**Next Phases**:
- Phase 8: Intent Classifier integration
- Phase 9: Task Planner integration
- Phase 10: Backend integration

## Related Services

- [Intent Classifier](../oss-knowledge-intent-classifier/) - Intent classification and routing
- [Task Planner](../oss-knowledge-task-planner/) - Complex task planning and execution
- [Search Server](../oss-knowledge-search/) - RAG queries and vector search
- [Backend](../oss-knowledge-backend/) - Database operations and persistence

