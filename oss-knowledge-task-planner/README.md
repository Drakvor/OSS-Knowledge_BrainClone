# OSS Knowledge Task Planner Service

Handles complex task planning, decomposition, and execution with dependencies for the agentic RAG system.

## Architecture

The Task Planner service provides task planning and execution:

```
Orchestrator
  ↓
Task Planner (Port 8004)
  ├─ Planner - Task decomposition
  ├─ Executor - Task execution
  ├─ Neo4j - Topic hierarchy
  ├─ Qdrant - Vector retrieval
  └─ Search Server - RAG queries
```

## Responsibilities

- **Task Planning**: Decompose complex queries into tasks with dependencies
- **Task Execution**: Execute tasks with dependency resolution and parallel execution
- **Task Types**: retrieve, analyze, generate
- **Dynamic Spawning**: Create new tasks based on discoveries during execution
- **Integration**: Neo4j for topic hierarchy, Qdrant for vector retrieval

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
uvicorn main:app --host 0.0.0.0 --port 8004 --reload
```

## Endpoints

- `GET /health` - Health check endpoint
- `GET /` - Service information
- `GET /docs` - API documentation (Swagger)
- `POST /plan` - Create a task plan from a query
- `POST /execute` - Execute a task plan

## Environment Variables

- `LOG_LEVEL` - Logging level (default: INFO)
- `NEO4J_URI` - Neo4j connection URI (default: neo4j://localhost:7687)
- `NEO4J_USERNAME` - Neo4j username (default: neo4j)
- `NEO4J_PASSWORD` - Neo4j password
- `QDRANT_HOST` - Qdrant host (default: localhost)
- `QDRANT_PORT` - Qdrant port (default: 6333)

## Development Status

**Phase 4**: ✅ Service foundation complete
- Basic FastAPI app structure
- Health check endpoint
- Placeholder planner and executor logic

**Next Phases**:
- Phase 5: Task Planner Core Logic
- Phase 6: Task Planner Dependencies & Parallel Execution
- Phase 7: Task Planner Neo4j & Qdrant Integration
- Phase 8: Task Planner Dynamic Spawning

## Related Services

- [Orchestrator](../oss-knowledge-orchestrator/) - Central coordination service
- [Search Server](../oss-knowledge-search/) - RAG queries and vector search
- [Context Manager](../oss-knowledge-context-manager/) - Chat context building
