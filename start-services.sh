#!/bin/bash

# OSS Knowledge Local Services Startup Script
# This script starts all services in the correct order

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 Starting OSS Knowledge Local Services..."
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
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
    
    echo -e "${YELLOW}⏳ Waiting for $service_name to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        echo -e "${YELLOW}   Attempt $attempt/$max_attempts - waiting...${NC}"
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}❌ $service_name failed to start within timeout${NC}"
    return 1
}

# Service ports
ORCHESTRATOR_PORT=8000
CONTEXT_MANAGER_PORT=8005
TASK_PLANNER_PORT=8004
SEARCH_PORT=8002
EMBEDDING_PORT=8003
INTENT_PORT=8001
BACKEND_PORT=8080
FRONTEND_PORT=5173

# Check all ports first
echo -e "${BLUE}🔍 Checking port availability...${NC}"
check_port $ORCHESTRATOR_PORT || exit 1
check_port $CONTEXT_MANAGER_PORT || exit 1
check_port $TASK_PLANNER_PORT || exit 1
check_port $SEARCH_PORT || exit 1
check_port $EMBEDDING_PORT || exit 1
check_port $INTENT_PORT || exit 1
check_port $BACKEND_PORT || exit 1
check_port $FRONTEND_PORT || exit 1

echo ""

# Create logs directory
mkdir -p logs

# 1. Start Orchestrator (Port 8000)
echo -e "${BLUE}1️⃣ Starting Orchestrator (Port $ORCHESTRATOR_PORT)...${NC}"
cd "$PROJECT_ROOT/oss-knowledge-orchestrator"
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1 || true

# Enable Task Planner by default for COMPLEX intents
export USE_TASK_PLANNER="${USE_TASK_PLANNER:-true}"

nohup env USE_TASK_PLANNER="${USE_TASK_PLANNER}" \
         python3 -m uvicorn main:app --host 0.0.0.0 --port $ORCHESTRATOR_PORT --reload > ../logs/orchestrator.log 2>&1 &
ORCHESTRATOR_PID=$!
echo "Orchestrator PID: $ORCHESTRATOR_PID"
cd "$PROJECT_ROOT"

wait_for_service "http://localhost:$ORCHESTRATOR_PORT/health" "Orchestrator"

# 2. Start Context Manager (Port 8005)
echo -e "${BLUE}2️⃣ Starting Context Manager (Port $CONTEXT_MANAGER_PORT)...${NC}"
cd "$PROJECT_ROOT/oss-knowledge-context-manager"
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1 || true
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port $CONTEXT_MANAGER_PORT --reload > ../logs/context-manager.log 2>&1 &
CONTEXT_MANAGER_PID=$!
echo "Context Manager PID: $CONTEXT_MANAGER_PID"
cd "$PROJECT_ROOT"

wait_for_service "http://localhost:$CONTEXT_MANAGER_PORT/health" "Context Manager"

# 3. Start Task Planner (Port 8004)
echo -e "${BLUE}3️⃣ Starting Task Planner (Port $TASK_PLANNER_PORT)...${NC}"
cd "$PROJECT_ROOT/oss-knowledge-task-planner"
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1 || true

# Load Azure OpenAI credentials from Search Server's environment or .env file
if [ -f "$PROJECT_ROOT/oss-knowledge-search/.env" ]; then
    echo -e "${YELLOW}   Loading Azure OpenAI credentials from Search Server .env...${NC}"
    export $(grep -E '^OPENAI_API_KEY=|^AZURE_OPENAI_ENDPOINT=|^AZURE_OPENAI_API_VERSION=|^AZURE_OPENAI_DEPLOYMENT=' "$PROJECT_ROOT/oss-knowledge-search/.env" | xargs)
fi

nohup env OPENAI_API_KEY="${OPENAI_API_KEY}" \
         AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT:-https://multiagent-openai-service.openai.azure.com/}" \
         AZURE_OPENAI_API_VERSION="${AZURE_OPENAI_API_VERSION:-2024-12-01-preview}" \
         AZURE_OPENAI_DEPLOYMENT="${AZURE_OPENAI_DEPLOYMENT:-gpt-4.1-mini}" \
         python3 -m uvicorn main:app --host 0.0.0.0 --port $TASK_PLANNER_PORT --reload > ../logs/task-planner.log 2>&1 &
TASK_PLANNER_PID=$!
echo "Task Planner PID: $TASK_PLANNER_PID"
cd "$PROJECT_ROOT"

wait_for_service "http://localhost:$TASK_PLANNER_PORT/health" "Task Planner"

# 4. Start Search Server (Port 8002)
echo -e "${BLUE}1️⃣ Starting Search Server (Port 8002)...${NC}"
cd oss-knowledge-search
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1 || true
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port $SEARCH_PORT --reload > ../logs/search-server.log 2>&1 &
SEARCH_PID=$!
echo "Search Server PID: $SEARCH_PID"
cd "$PROJECT_ROOT"

wait_for_service "http://localhost:$SEARCH_PORT/health" "Search Server"

# 5. Start Embedding Server (Port 8003)
echo -e "${BLUE}5️⃣ Starting Embedding Server (Port $EMBEDDING_PORT)...${NC}"
cd "$PROJECT_ROOT/oss-knowledge-embedding-server"
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1 || true
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port $EMBEDDING_PORT --reload > ../logs/embedding-server.log 2>&1 &
EMBEDDING_PID=$!
echo "Embedding Server PID: $EMBEDDING_PID"
cd "$PROJECT_ROOT"

wait_for_service "http://localhost:$EMBEDDING_PORT/health" "Embedding Server"

# 6. Start Backend (Port 8080)
echo -e "${BLUE}6️⃣ Starting Java Backend (Port $BACKEND_PORT)...${NC}"
cd "$PROJECT_ROOT/oss-knowledge-backend"
nohup mvn spring-boot:run > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
cd "$PROJECT_ROOT"

wait_for_service "http://localhost:$BACKEND_PORT/health" "Backend" || wait_for_service "http://localhost:$BACKEND_PORT/actuator/health" "Backend"

# 7. Start Intent Classifier (Port 8001)
echo -e "${BLUE}7️⃣ Starting Intent Classifier (Port $INTENT_PORT)...${NC}"
cd "$PROJECT_ROOT/oss-knowledge-intent-classifier"
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1 || true

# Load Azure OpenAI credentials from Search Server's environment or .env file
# Try to load from Search Server's .env if it exists
if [ -f "$PROJECT_ROOT/oss-knowledge-search/.env" ]; then
    echo -e "${YELLOW}   Loading Azure OpenAI credentials from Search Server .env...${NC}"
    export $(grep -E '^OPENAI_API_KEY=|^AZURE_OPENAI_ENDPOINT=|^AZURE_OPENAI_API_VERSION=|^AZURE_OPENAI_DEPLOYMENT=' "$PROJECT_ROOT/oss-knowledge-search/.env" | xargs)
fi

# Also try to inherit from current shell environment (if already set)
# This allows manual export before running the script

nohup env OPENAI_API_KEY="${OPENAI_API_KEY}" \
         AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT:-https://multiagent-openai-service.openai.azure.com/}" \
         AZURE_OPENAI_API_VERSION="${AZURE_OPENAI_API_VERSION:-2024-12-01-preview}" \
         AZURE_OPENAI_DEPLOYMENT="${AZURE_OPENAI_DEPLOYMENT:-gpt-4.1-mini}" \
         python3 -m uvicorn main:app --host 0.0.0.0 --port $INTENT_PORT --reload > ../logs/intent-classifier.log 2>&1 &
INTENT_PID=$!
echo "Intent Classifier PID: $INTENT_PID"
cd "$PROJECT_ROOT"

wait_for_service "http://localhost:$INTENT_PORT/health" "Intent Classifier" || wait_for_service "http://localhost:$INTENT_PORT/" "Intent Classifier"

# 8. Start Frontend (Port 5173)
echo -e "${BLUE}8️⃣ Starting Frontend (Port $FRONTEND_PORT)...${NC}"
cd "$PROJECT_ROOT/oss-knowledge-front-gitlab"

# Create or update .env file
cat > .env << EOF
# OSS Knowledge Frontend Environment Configuration
VITE_API_BASE_URL=http://localhost:8080
VITE_SEARCH_API_BASE_URL=http://localhost:8002
VITE_EMBEDDING_API_BASE_URL=http://localhost:8003
VITE_ORCHESTRATOR_URL=http://localhost:8000
NODE_ENV=development
VITE_APP_TITLE=OSS Knowledge Agent
VITE_APP_VERSION=1.0.0
EOF
echo "Updated .env file for frontend"

npm install > /dev/null 2>&1 || true
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
cd "$PROJECT_ROOT"

wait_for_service "http://localhost:$FRONTEND_PORT" "Frontend"

echo ""
echo -e "${GREEN}🎉 All services started successfully!${NC}"
echo "=============================================="
echo -e "${BLUE}Service URLs:${NC}"
echo "  Frontend:        http://localhost:$FRONTEND_PORT"
echo "  Orchestrator:    http://localhost:$ORCHESTRATOR_PORT"
echo "  Context Manager: http://localhost:$CONTEXT_MANAGER_PORT"
echo "  Task Planner:    http://localhost:$TASK_PLANNER_PORT"
echo "  Backend:         http://localhost:$BACKEND_PORT"
echo "  Search Server:   http://localhost:$SEARCH_PORT"
echo "  Embedding Server: http://localhost:$EMBEDDING_PORT"
echo "  Intent Classifier: http://localhost:$INTENT_PORT"
echo ""
echo -e "${BLUE}Process IDs:${NC}"
echo "  Orchestrator:    $ORCHESTRATOR_PID"
echo "  Context Manager: $CONTEXT_MANAGER_PID"
echo "  Task Planner:    $TASK_PLANNER_PID"
echo "  Search Server:   $SEARCH_PID"
echo "  Embedding Server: $EMBEDDING_PID"
echo "  Backend:         $BACKEND_PID"
echo "  Intent Classifier: $INTENT_PID"
echo "  Frontend:        $FRONTEND_PID"
echo ""
echo -e "${YELLOW}📝 Logs are available in the logs/ directory${NC}"
echo -e "${YELLOW}🛑 To stop all services, run: ./stop-services.sh${NC}"
echo ""

# Save PIDs for stop script
echo "$ORCHESTRATOR_PID $CONTEXT_MANAGER_PID $TASK_PLANNER_PID $SEARCH_PID $EMBEDDING_PID $BACKEND_PID $INTENT_PID $FRONTEND_PID" > logs/service-pids.txt
