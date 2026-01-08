#!/bin/bash

# OSS Knowledge System - Complete Local Deployment Script
# Includes all services: Backend, Frontend, Search, Embedding, Intent Classifier, and Mem0

# Don't exit on error - we want to continue even if Mem0 fails
set +e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="/Users/drakvor/Development/oss-knowledge"
cd "$PROJECT_ROOT"

# Service ports
ORCHESTRATOR_PORT=8000
EMBEDDING_PORT=8003  # Moved from 8000 to avoid conflict with Orchestrator
SEARCH_PORT=8002
INTENT_PORT=8001
TASK_PLANNER_PORT=8004
CONTEXT_MANAGER_PORT=8005
BACKEND_PORT=8080
FRONTEND_PORT=5173
MEM0_PORT=8006  # Moved from 8005 to avoid conflict with Context Manager

echo -e "${BLUE}🚀 OSS Knowledge System - Complete Local Deployment${NC}"
echo "=================================================="

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Port $port is already in use${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Port $port is available${NC}"
        return 0
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    local optional=${3:-false}  # Optional parameter to make service optional
    
    echo -e "${YELLOW}⏳ Waiting for $service_name to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        # Check if process is still running (for optional services)
        if [ "$optional" = "true" ]; then
            local pid=$4
            if [ -n "$pid" ]; then
                if ! ps -p $pid >/dev/null 2>&1; then
                    echo ""
                    echo -e "${YELLOW}⚠️  $service_name process died. Checking logs...${NC}"
                    return 1
                fi
                # For Mem0, also check log for fatal errors
                if [ "$service_name" = "Mem0 Server" ] && [ -f "$PROJECT_ROOT/logs/mem0-server.log" ]; then
                    if grep -q -i "FATAL\|OperationalError\|does not exist" "$PROJECT_ROOT/logs/mem0-server.log" 2>/dev/null; then
                        echo ""
                        echo -e "${YELLOW}⚠️  $service_name has fatal errors in log. Continuing...${NC}"
                        return 1
                    fi
                fi
            fi
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    if [ "$optional" = "true" ]; then
        echo ""
        echo -e "${YELLOW}⚠️  $service_name failed to start within timeout (optional service - continuing)${NC}"
        return 1
    else
    echo -e "${RED}❌ $service_name failed to start within timeout${NC}"
    return 1
    fi
}

# Initialize Mem0 status
MEM0_STARTED=false
MEM0_PID=""
SKIP_MEM0=false

# Check all ports
echo -e "${BLUE}🔍 Checking port availability...${NC}"
check_port $ORCHESTRATOR_PORT || exit 1
check_port $SEARCH_PORT || exit 1
check_port $INTENT_PORT || exit 1
check_port $TASK_PLANNER_PORT || exit 1
check_port $CONTEXT_MANAGER_PORT || exit 1
check_port $BACKEND_PORT || exit 1
check_port $FRONTEND_PORT || exit 1
# Embedding Server and Mem0 are optional - warn but don't exit
if ! check_port $EMBEDDING_PORT; then
    echo -e "${YELLOW}⚠️  Embedding Server port in use - will skip Embedding Server startup${NC}"
    SKIP_EMBEDDING=true
fi
if ! check_port $MEM0_PORT; then
    echo -e "${YELLOW}⚠️  Mem0 port in use - will skip Mem0 startup${NC}"
    SKIP_MEM0=true
fi

echo ""

# Create logs directory
mkdir -p logs

# 1. Start Orchestrator (Port 8000)
echo -e "${BLUE}1️⃣ Starting Orchestrator (Port $ORCHESTRATOR_PORT)...${NC}"
cd "$PROJECT_ROOT/oss-knowledge-orchestrator"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt >/dev/null 2>&1 || true
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port $ORCHESTRATOR_PORT --reload > ../logs/orchestrator.log 2>&1 &
ORCHESTRATOR_PID=$!
echo "Orchestrator PID: $ORCHESTRATOR_PID"
cd "$PROJECT_ROOT"

wait_for_service "http://localhost:$ORCHESTRATOR_PORT/health" "Orchestrator" || exit 1

# 2. Start Context Manager (Port 8005)
echo -e "${BLUE}2️⃣ Starting Context Manager (Port $CONTEXT_MANAGER_PORT)...${NC}"
cd "$PROJECT_ROOT/oss-knowledge-context-manager"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt >/dev/null 2>&1 || true
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port $CONTEXT_MANAGER_PORT --reload > ../logs/context-manager.log 2>&1 &
CONTEXT_MANAGER_PID=$!
echo "Context Manager PID: $CONTEXT_MANAGER_PID"
cd "$PROJECT_ROOT"

wait_for_service "http://localhost:$CONTEXT_MANAGER_PORT/health" "Context Manager" || exit 1

# 3. Start Task Planner (Port 8004)
echo -e "${BLUE}3️⃣ Starting Task Planner (Port $TASK_PLANNER_PORT)...${NC}"
cd "$PROJECT_ROOT/oss-knowledge-task-planner"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt >/dev/null 2>&1 || true
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port $TASK_PLANNER_PORT --reload > ../logs/task-planner.log 2>&1 &
TASK_PLANNER_PID=$!
echo "Task Planner PID: $TASK_PLANNER_PID"
cd "$PROJECT_ROOT"

wait_for_service "http://localhost:$TASK_PLANNER_PORT/health" "Task Planner" || exit 1

# 4. Start Search Server (Port 8002)
echo -e "${BLUE}4️⃣ Starting Search Server (Port $SEARCH_PORT)...${NC}"
cd "$PROJECT_ROOT/oss-knowledge-search"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt >/dev/null 2>&1 || true
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port $SEARCH_PORT --reload > ../logs/search-server.log 2>&1 &
SEARCH_PID=$!
echo "Search Server PID: $SEARCH_PID"
cd "$PROJECT_ROOT"

wait_for_service "http://localhost:$SEARCH_PORT/health" "Search Server" || exit 1

# 5. Start Embedding Server (Port 8003) - OPTIONAL
if [ "${SKIP_EMBEDDING:-false}" != "true" ]; then
    echo -e "${BLUE}5️⃣ Starting Embedding Server (Port $EMBEDDING_PORT)...${NC}"
    cd "$PROJECT_ROOT/oss-knowledge-embedding-server"
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -q -r requirements.txt >/dev/null 2>&1 || true
    nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port $EMBEDDING_PORT --reload > ../logs/embedding-server.log 2>&1 &
    EMBEDDING_PID=$!
    echo "Embedding Server PID: $EMBEDDING_PID"
    cd "$PROJECT_ROOT"
    
    wait_for_service "http://localhost:$EMBEDDING_PORT/health" "Embedding Server" "true" "$EMBEDDING_PID" || {
        echo -e "${YELLOW}⚠️  Embedding Server failed to start - this is optional, continuing...${NC}"
        EMBEDDING_PID=""
    }
else
    echo -e "${YELLOW}5️⃣ Skipping Embedding Server (port in use)${NC}"
    EMBEDDING_PID=""
fi

# 6. Start Mem0 Server (Port 8006) - OPTIONAL
if [ "$SKIP_MEM0" != "true" ]; then
    echo -e "${BLUE}6️⃣ Starting Mem0 Server (Port $MEM0_PORT) [OPTIONAL]...${NC}"
cd "$PROJECT_ROOT/mem0-azure-deployment/server"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt >/dev/null 2>&1 || true

# Set environment variables for Mem0
export POSTGRES_HOST=${POSTGRES_HOST:-localhost}
export POSTGRES_PORT=${POSTGRES_PORT:-5432}
export POSTGRES_DB=${POSTGRES_DB:-mem0db}
export POSTGRES_USER=${POSTGRES_USER:-mem0admin}
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-}
export OPENAI_API_KEY=${OPENAI_API_KEY:-${AZURE_OPENAI_API_KEY}}

# Use Azure OpenAI if available, otherwise use OpenAI
if [ -n "$AZURE_OPENAI_API_KEY" ] && [ -n "$AZURE_OPENAI_ENDPOINT" ]; then
    export AZURE_OPENAI_API_KEY
    export AZURE_OPENAI_ENDPOINT
    export AZURE_OPENAI_API_VERSION=${AZURE_OPENAI_API_VERSION:-2024-02-15-preview}
fi

nohup python3 -m uvicorn main:app --host 0.0.0.0 --port $MEM0_PORT --reload > ../../logs/mem0-server.log 2>&1 &
MEM0_PID=$!
echo "Mem0 Server PID: $MEM0_PID"
cd "$PROJECT_ROOT"

    # Wait for Mem0 with shorter timeout and make it optional
    wait_for_service "http://localhost:$MEM0_PORT/docs" "Mem0 Server" "true" "$MEM0_PID" || \
    wait_for_service "http://localhost:$MEM0_PORT/" "Mem0 Server" "true" "$MEM0_PID" || {
        echo -e "${YELLOW}⚠️  Mem0 Server failed to start - this is optional, continuing with other services...${NC}"
        echo -e "${YELLOW}   Check logs/mem0-server.log for details${NC}"
        MEM0_PID=""
        MEM0_STARTED=false
    }
    
    if [ -n "$MEM0_PID" ] && ps -p $MEM0_PID >/dev/null 2>&1; then
        MEM0_STARTED=true
    else
        MEM0_STARTED=false
        MEM0_PID=""
    fi
else
    echo -e "${YELLOW}3️⃣ Skipping Mem0 Server (port in use)${NC}"
    MEM0_PID=""
    MEM0_STARTED=false
fi

# 7. Start Backend (Port 8080)
echo -e "${BLUE}7️⃣ Starting Java Backend (Port $BACKEND_PORT)...${NC}"
cd "$PROJECT_ROOT/oss-knowledge-backend"
nohup mvn spring-boot:run -Dspring-boot.run.arguments=--spring.jpa.hibernate.ddl-auto=validate > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
cd "$PROJECT_ROOT"

wait_for_service "http://localhost:$BACKEND_PORT/actuator/health" "Backend" || wait_for_service "http://localhost:$BACKEND_PORT/health" "Backend" || exit 1

# 8. Start Intent Classifier (Port 8001)
echo -e "${BLUE}8️⃣ Starting Intent Classifier (Port $INTENT_PORT)...${NC}"
cd "$PROJECT_ROOT/oss-knowledge-intent-classifier"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt >/dev/null 2>&1 || true
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port $INTENT_PORT --reload > ../logs/intent-classifier.log 2>&1 &
INTENT_PID=$!
echo "Intent Classifier PID: $INTENT_PID"
cd "$PROJECT_ROOT"

wait_for_service "http://localhost:$INTENT_PORT/health" "Intent Classifier" || wait_for_service "http://localhost:$INTENT_PORT/" "Intent Classifier" || exit 1

# 9. Start Frontend (Port 5173)
echo -e "${BLUE}9️⃣ Starting Frontend (Port $FRONTEND_PORT)...${NC}"
cd "$PROJECT_ROOT/oss-knowledge-front-gitlab"

# Create .env file if it doesn't exist or update it
cat > .env << EOF
# OSS Knowledge Frontend Environment Configuration
VITE_API_BASE_URL=http://localhost:8080
VITE_SEARCH_API_BASE_URL=http://localhost:8002
VITE_EMBEDDING_API_BASE_URL=http://localhost:8003
VITE_ORCHESTRATOR_URL=http://localhost:8000
VITE_MEM0_API_BASE_URL=http://localhost:8006
NODE_ENV=development
VITE_APP_TITLE=OSS Knowledge Agent
VITE_APP_VERSION=1.0.0
EOF
echo "Updated .env file for frontend"

npm install >/dev/null 2>&1 || true
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
cd "$PROJECT_ROOT"

wait_for_service "http://localhost:$FRONTEND_PORT" "Frontend" || exit 1

echo ""
if [ "$MEM0_STARTED" = "true" ]; then
echo -e "${GREEN}🎉 All services started successfully!${NC}"
else
    echo -e "${GREEN}🎉 Core services started successfully!${NC}"
    echo -e "${YELLOW}⚠️  Mem0 Server is not running (optional service)${NC}"
fi
echo "=================================================="
echo -e "${BLUE}Service URLs:${NC}"
echo "  Frontend:        http://localhost:$FRONTEND_PORT"
echo "  Orchestrator:    http://localhost:$ORCHESTRATOR_PORT"
echo "  Context Manager: http://localhost:$CONTEXT_MANAGER_PORT"
echo "  Task Planner:    http://localhost:$TASK_PLANNER_PORT"
echo "  Backend:         http://localhost:$BACKEND_PORT"
echo "  Search Server:   http://localhost:$SEARCH_PORT"
echo "  Intent Classifier: http://localhost:$INTENT_PORT"
if [ -n "$EMBEDDING_PID" ]; then
    echo "  Embedding Server: http://localhost:$EMBEDDING_PORT ✅"
else
    echo "  Embedding Server: http://localhost:$EMBEDDING_PORT ⚠️  (not started)"
fi
if [ "$MEM0_STARTED" = "true" ]; then
    echo "  Mem0 Server:     http://localhost:$MEM0_PORT ✅"
else
    echo "  Mem0 Server:     http://localhost:$MEM0_PORT ⚠️  (not running - port conflict)"
fi
echo ""
echo -e "${BLUE}Process IDs:${NC}"
echo "  Orchestrator:    $ORCHESTRATOR_PID"
echo "  Context Manager: $CONTEXT_MANAGER_PID"
echo "  Task Planner:    $TASK_PLANNER_PID"
echo "  Search Server:   $SEARCH_PID"
if [ -n "$EMBEDDING_PID" ]; then
    echo "  Embedding Server: $EMBEDDING_PID"
else
    echo "  Embedding Server: (not started)"
fi
if [ -n "$MEM0_PID" ]; then
    echo "  Mem0 Server:     $MEM0_PID"
else
    echo "  Mem0 Server:     (not started)"
fi
echo "  Backend:         $BACKEND_PID"
echo "  Intent Classifier: $INTENT_PID"
echo "  Frontend:        $FRONTEND_PID"
echo ""
echo -e "${YELLOW}📝 Logs are available in the logs/ directory${NC}"
echo -e "${YELLOW}🛑 To stop all services, run: ./stop-services.sh${NC}"
echo ""

# Save PIDs for stop script
PIDS="$ORCHESTRATOR_PID $CONTEXT_MANAGER_PID $TASK_PLANNER_PID $SEARCH_PID $BACKEND_PID $INTENT_PID $FRONTEND_PID"
if [ -n "$EMBEDDING_PID" ]; then
    PIDS="$PIDS $EMBEDDING_PID"
fi
if [ -n "$MEM0_PID" ]; then
    PIDS="$PIDS $MEM0_PID"
fi
echo $PIDS > logs/service-pids.txt

echo -e "${GREEN}✅ Deployment complete!${NC}"

