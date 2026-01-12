# Local Deployment Guide

**Last Updated**: 2026-01-12  
**Purpose**: Complete guide for deploying the OSS Knowledge System locally from the GitHub repository

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Required Credentials](#required-credentials)
3. [Environment File Setup](#environment-file-setup)
4. [Quick Start](#quick-start)
5. [Service-Specific Setup](#service-specific-setup)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.9+** - For Python services (Orchestrator, Search Server, Embedding Server, Task Planner, Context Manager, Mem0, Intent Classifier)
- **Java 21** - For Backend service (Spring Boot)
- **Maven 3.6+** - For building and running the Backend
- **Node.js 18+** - For Frontend (optional)
- **Git** - For cloning the repository

### Required Services

You have two options for databases:

**Option 1: Remote Databases (Recommended for Quick Start)**
- Access to remote PostgreSQL server
- Access to remote Neo4j server (optional)
- Access to remote Qdrant server

**Option 2: Local Databases**
- PostgreSQL 14+ with pgvector extension (or use Qdrant instead)
- Neo4j 5+ (optional)
- Qdrant (can use remote instance)

### Required API Keys

- **Azure OpenAI API Key** - Required for LLM and embedding services
- **Azure OpenAI Endpoint** - Your Azure OpenAI service endpoint URL

---

## Required Credentials

### Azure OpenAI Credentials

These are required for all services that use LLM or embeddings:

- `AZURE_OPENAI_API_KEY` - Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint URL (e.g., `https://your-service.openai.azure.com/`)
- `AZURE_OPENAI_API_VERSION` - API version (default: `2024-12-01-preview`)
- `AZURE_OPENAI_DEPLOYMENT` - LLM deployment name (default: `gpt-4.1-mini`)
- `AZURE_EMBEDDING_DEPLOYMENT` - Embedding deployment name (default: `oss-embedding`)

**Where to get these:**
- Log into Azure Portal
- Navigate to your Azure OpenAI resource
- Go to "Keys and Endpoint" section
- Copy the API key and endpoint URL
- Check your deployments for the deployment names

### Database Credentials

#### PostgreSQL

- `POSTGRES_HOST` - Database host (e.g., `localhost` or remote IP like `20.214.89.216`)
- `POSTGRES_PORT` - Database port (default: `5432`)
- `POSTGRES_DATABASE` - Database name (default: `oss_knowledge`)
- `POSTGRES_USER` - Database username (default: `oss`)
- `POSTGRES_PASSWORD` - Database password

#### Neo4j (Optional)

- `NEO4J_URI` - Neo4j connection URI (format: `bolt://host:7687` or `neo4j://host:7687`)
- `NEO4J_USERNAME` - Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD` - Neo4j password
- `NEO4J_DATABASE` - Database name (default: `neo4j`)

#### Qdrant (Vector Database)

- `QDRANT_HOST` - Qdrant host (default: remote IP or `localhost`)
- `QDRANT_PORT` - Qdrant port (default: `6333`)
- `QDRANT_API_KEY` - Optional API key for authentication

### Backend (Spring Boot) Credentials

- `DB_URL` - Full JDBC URL (optional if using `application-local.properties`)
  - Format: `jdbc:postgresql://host:port/database`
  - Example: `jdbc:postgresql://20.214.89.216:5432/oss_knowledge`
- `DB_USERNAME` - Database username
- `DB_PASSWORD` - Database password
- `JWT_SECRET` - JWT signing secret (must be at least 32 characters for HMAC-SHA256)

---

## Environment File Setup

Each service requires a `.env` file (or `application-local.properties` for Backend). Follow these steps:

### Step 1: Search Server

**File**: `oss-knowledge-search/.env`

```bash
cd oss-knowledge-search
cp .env.example .env  # If .env.example exists
# Edit .env with your credentials
```

**Required variables:**
```bash
# PostgreSQL
POSTGRES_HOST=your-postgres-host
POSTGRES_PORT=5432
POSTGRES_DATABASE=oss_knowledge
POSTGRES_USER=oss
POSTGRES_PASSWORD=your-postgres-password

# Neo4j (optional)
NEO4J_URI=neo4j://your-neo4j-host:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Azure OpenAI
OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-service.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_EMBEDDING_DEPLOYMENT=oss-embedding

# Qdrant
QDRANT_HOST=your-qdrant-host
QDRANT_PORT=6333
```

### Step 2: Embedding Server

**File**: `oss-knowledge-embedding-server/.env`

```bash
cd oss-knowledge-embedding-server
cp .env.example .env  # If .env.example exists
# Edit .env with your credentials
```

**Required variables:**
```bash
# Azure OpenAI
OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-service.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_EMBEDDING_DEPLOYMENT=oss-embedding

# Qdrant
QDRANT_HOST=your-qdrant-host
QDRANT_PORT=6333

# Neo4j (optional)
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password

# PostgreSQL (optional)
POSTGRES_HOST=your-postgres-host
POSTGRES_PORT=5432
POSTGRES_DATABASE=oss_knowledge
POSTGRES_USER=oss
POSTGRES_PASSWORD=your-postgres-password
```

### Step 3: Task Planner

**File**: `oss-knowledge-task-planner/.env`

```bash
cd oss-knowledge-task-planner
# Create .env file (no .env.example exists yet)
# Edit .env with your credentials
```

**Required variables:**
```bash
# Neo4j
NEO4J_URI=neo4j://your-neo4j-host:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Azure OpenAI
OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-service.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini

# Qdrant
QDRANT_HOST=your-qdrant-host
QDRANT_PORT=6333

# Search Server URL
SEARCH_SERVER_URL=http://localhost:8002
```

### Step 4: Context Manager

**File**: `oss-knowledge-context-manager/.env`

```bash
cd oss-knowledge-context-manager
# Create .env file (no .env.example exists yet)
# Edit .env with your credentials
```

**Required variables:**
```bash
# Service URLs
BACKEND_URL=http://localhost:8080
MEM0_URL=http://localhost:8006
```

### Step 5: Mem0

**File**: `mem0-azure-deployment/server/.env`

```bash
cd mem0-azure-deployment/server
cp .env.example .env  # If .env.example exists
# Edit .env with your credentials
```

**Required variables:**
```bash
# Azure OpenAI
OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-service.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
AZURE_EMBEDDING_DEPLOYMENT=oss-embedding

# Mem0 internal Azure OpenAI env vars (to prevent DefaultAzureCredential)
LLM_AZURE_OPENAI_API_KEY=your-azure-openai-api-key
EMBEDDING_AZURE_OPENAI_API_KEY=your-azure-openai-api-key
LLM_AZURE_ENDPOINT=https://your-service.openai.azure.com/
EMBEDDING_AZURE_ENDPOINT=https://your-service.openai.azure.com/
LLM_AZURE_API_VERSION=2024-12-01-preview
EMBEDDING_AZURE_API_VERSION=2024-12-01-preview
LLM_AZURE_DEPLOYMENT=gpt-4.1-mini
EMBEDDING_AZURE_DEPLOYMENT=oss-embedding

# Qdrant
QDRANT_URL=http://your-qdrant-host:6333

# Neo4j (optional - leave empty to disable)
NEO4J_URI=
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password

# PostgreSQL (optional - for pgvector, but we use Qdrant)
POSTGRES_HOST=your-postgres-host
POSTGRES_PORT=5432
POSTGRES_DB=mem0db
POSTGRES_USER=mem0admin
POSTGRES_PASSWORD=your-postgres-password
```

### Step 6: Backend (Spring Boot)

**File**: `oss-knowledge-backend/src/main/resources/application-local.properties`

```bash
cd oss-knowledge-backend/src/main/resources
cp application-local.properties.example application-local.properties  # If example exists
# Edit application-local.properties with your credentials
```

**Required variables:**
```properties
# Database Configuration
spring.datasource.url=${DB_URL:jdbc:postgresql://your-postgres-host:5432/oss_knowledge}
spring.datasource.password=${DB_PASSWORD:your-postgres-password}

# JWT Secret (must be at least 32 characters for HMAC-SHA256)
security.jwt.secret=${JWT_SECRET:your-jwt-secret-key-minimum-32-characters-long}
```

**Important**: The Backend requires `SPRING_PROFILES_ACTIVE=local` to use this file. The deployment script sets this automatically.

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Drakvor/OSS-Knowledge_BrainClone.git
cd OSS-Knowledge_BrainClone
```

### 2. Set Up Environment Files

Follow the steps in [Environment File Setup](#environment-file-setup) to create all required `.env` files and `application-local.properties`.

### 3. Run the Deployment Script

```bash
./deploy-all-local.sh
```

This script will:
- Check port availability
- Start all services in order:
  1. Orchestrator (port 8000)
  2. Context Manager (port 8005)
  3. Task Planner (port 8004)
  4. Search Server (port 8002)
  5. Embedding Server (port 8003)
  6. Mem0 (port 8006)
  7. Backend (port 8080)
  8. Intent Classifier (port 8001)
  9. Frontend (port 5173)

### 4. Verify Services

Check that all services are running:

```bash
# Check service health
curl http://localhost:8000/health  # Orchestrator
curl http://localhost:8002/health  # Search Server
curl http://localhost:8003/health  # Embedding Server
curl http://localhost:8004/health  # Task Planner
curl http://localhost:8005/health  # Context Manager
curl http://localhost:8006/health  # Mem0
curl http://localhost:8080/health  # Backend
curl http://localhost:8001/health  # Intent Classifier
```

---

## Service-Specific Setup

### Backend

**Important Configuration:**
- Requires `SPRING_PROFILES_ACTIVE=local` to use `application-local.properties`
- The deployment script sets this automatically
- JWT_SECRET must be at least 32 characters

**Manual Start:**
```bash
cd oss-knowledge-backend
export SPRING_PROFILES_ACTIVE=local
export JWT_SECRET=your-jwt-secret-key-minimum-32-characters-long
export DB_PASSWORD=your-postgres-password
mvn spring-boot:run
```

### Mem0

**Important Configuration:**
- Requires `.env` file to be loaded before startup
- The deployment script loads the `.env` file automatically
- Neo4j is optional - set `NEO4J_URI=""` to disable

**Manual Start:**
```bash
cd mem0-azure-deployment/server
source venv/bin/activate
source .env  # Load environment variables
python3 -m uvicorn main:app --host 0.0.0.0 --port 8006 --reload
```

### Database Access

**Remote Databases:**
- Set the appropriate host IP addresses in your `.env` files
- Ensure network access to the remote databases
- Use the same credentials as provided by your database administrator

**Local Databases:**
- Install PostgreSQL, Neo4j, and/or Qdrant locally
- Update `.env` files to use `localhost`
- For PostgreSQL, ensure the database and user exist:
  ```sql
  CREATE DATABASE oss_knowledge;
  CREATE USER oss WITH PASSWORD 'your-password';
  GRANT ALL PRIVILEGES ON DATABASE oss_knowledge TO oss;
  ```

---

## Troubleshooting

### Backend Fails to Start

**Error: `WeakKeyException: JWT secret is 0 bits`**
- **Solution**: Ensure `JWT_SECRET` is set in the environment or `application-local.properties`
- The deployment script sets this automatically, but if starting manually, export it:
  ```bash
  export JWT_SECRET=your-secret-key-minimum-32-characters
  ```

**Error: `Schema-validation: missing table`**
- **Solution**: This is a database schema issue. The Backend uses `ddl-auto: validate` which checks that tables exist.
- Either create the missing tables in the database, or contact your database administrator.

**Error: Cannot connect to database**
- **Solution**: 
  1. Verify database host, port, and credentials in `application-local.properties`
  2. Test connection: `psql -h your-host -p 5432 -U oss -d oss_knowledge`
  3. Ensure `SPRING_PROFILES_ACTIVE=local` is set

### Mem0 Fails to Start

**Error: `Could not connect to Neo4j database`**
- **Solution**: Neo4j is optional. Set `NEO4J_URI=""` in `.env` to disable it.

**Error: `Tenant mismatch` (Azure OpenAI)**
- **Solution**: Ensure all Azure OpenAI environment variables are set in `.env`:
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_ENDPOINT`
  - `LLM_AZURE_OPENAI_API_KEY`
  - `EMBEDDING_AZURE_OPENAI_API_KEY`
  - And their corresponding endpoint variables

### Services Can't Connect to Databases

**PostgreSQL Connection Failed**
- Verify `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD` in `.env` files
- Test connection: `nc -zv your-host 5432`
- Check firewall rules if using remote database

**Neo4j Connection Failed**
- Verify `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` in `.env` files
- Test connection: `nc -zv your-host 7687`
- Neo4j is optional - you can disable it by setting `NEO4J_URI=""`

### Services Not Using Remote Databases

**Backend using localhost instead of remote DB**
- **Solution**: Ensure `SPRING_PROFILES_ACTIVE=local` is set
- Check that `application-local.properties` has the correct remote host in `spring.datasource.url`

**Mem0 using localhost instead of remote DB**
- **Solution**: Ensure `.env` file is loaded before starting Mem0
- The deployment script loads it automatically, but if starting manually:
  ```bash
  source .env
  ```

### Port Already in Use

**Error: Port XXXX is already in use**
- **Solution**: Stop the service using that port:
  ```bash
  lsof -ti :8000 | xargs kill -9  # Replace 8000 with your port
  ```
- Or modify the port in the service configuration

### Verify Database Connections

**Test PostgreSQL:**
```bash
psql -h your-host -p 5432 -U oss -d oss_knowledge
```

**Test Neo4j:**
```bash
cypher-shell -a bolt://your-host:7687 -u neo4j -p your-password
```

**Test Qdrant:**
```bash
curl http://your-qdrant-host:6333/collections
```

### Check Service Logs

All services log to the `logs/` directory:
- `logs/backend.log` - Backend logs
- `logs/mem0-server.log` - Mem0 logs
- `logs/search-server.log` - Search Server logs
- etc.

Check logs for detailed error messages:
```bash
tail -50 logs/backend.log
```

---

## Additional Resources

- **Backend API Documentation**: `http://localhost:8080/swagger-ui.html`
- **Service Health Checks**: All services expose `/health` endpoint
- **Deployment Script**: `./deploy-all-local.sh` - Automates service startup

---

## Getting Help

If you encounter issues not covered in this guide:

1. Check the service logs in `logs/` directory
2. Verify all environment variables are set correctly
3. Test database connections manually
4. Ensure all required software is installed and up to date
5. Check that ports are not in use by other services

---

**Note**: This guide assumes you have access to the required credentials (API keys, database passwords, etc.). These are not included in the repository for security reasons. Contact your system administrator or project maintainer to obtain the necessary credentials.

