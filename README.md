# OSS Knowledge System

Monorepo for the OSS Knowledge agentic RAG microservices architecture.

## Architecture

This repository contains multiple microservices that work together to provide a RAG (Retrieval-Augmented Generation) system:

- **Orchestrator** (Port 8000) - Main orchestration service
- **Intent Classifier** (Port 8001) - Intent classification using EXAONE
- **Search Server** (Port 8002) - Vector search and RAG query processing
- **Task Planner** (Port 8004) - Complex task decomposition and execution
- **Context Manager** (Port 8005) - Chat context building and memory management
- **Backend** (Port 8080) - Java Spring Boot API for data persistence
- **Mem0** (Port 8006) - Memory service for user and session memories

## Repository Structure

Each service is maintained in its own git repository:

- `oss-knowledge-orchestrator/` - Orchestrator service
- `oss-knowledge-intent-classifier/` - Intent Classifier service
- `oss-knowledge-search/` - Search Server service
- `oss-knowledge-task-planner/` - Task Planner service
- `oss-knowledge-context-manager/` - Context Manager service
- `oss-knowledge-backend/` - Backend API service
- `oss-knowledge-embedding-server/` - Embedding service
- `oss-knowledge-front-gitlab/` - Frontend application
- `oss-knowledge-gitops/` - GitOps configurations
- `mem0-azure-deployment/` - Mem0 service deployment

## Top-Level Scripts

- `comprehensive_system_e2e_test.sh` - Comprehensive end-to-end testing
- `deploy-all-local.sh` - Local deployment script
- `start-services.sh` - Start all services
- `stop-services.sh` - Stop all services
- `health-check.sh` - Health check for all services

## Testing

Test scripts are located in the `tests/` directory. See `tests/README.md` for details.

## Development

Each service directory contains its own README with service-specific setup instructions.

## Note

This is a monorepo structure where each subdirectory maintains its own git repository. The top-level repository tracks shared configuration, deployment scripts, and documentation.

