#!/bin/bash

# OSS Knowledge Local Services Stop Script
# This script stops all running services

echo "🛑 Stopping OSS Knowledge Local Services..."
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to kill process by PID
kill_process() {
    local pid=$1
    local service_name=$2
    
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo -e "${YELLOW}⏳ Stopping $service_name (PID: $pid)...${NC}"
        kill "$pid" 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}   Force stopping $service_name...${NC}"
            kill -9 "$pid" 2>/dev/null || true
        fi
        
        echo -e "${GREEN}✅ $service_name stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  $service_name was not running${NC}"
    fi
}

# Read PIDs from file if it exists
if [ -f "logs/service-pids.txt" ]; then
    read -r SEARCH_PID EMBEDDING_PID BACKEND_PID INTENT_PID FRONTEND_PID < logs/service-pids.txt
    echo -e "${BLUE}📋 Found saved process IDs${NC}"
else
    echo -e "${YELLOW}⚠️  No saved process IDs found, attempting to find processes by port...${NC}"
    
    # Find processes by port
    SEARCH_PID=$(lsof -ti:8002 2>/dev/null || echo "")
    EMBEDDING_PID=$(lsof -ti:8000 2>/dev/null || echo "")
    BACKEND_PID=$(lsof -ti:8080 2>/dev/null || echo "")
    INTENT_PID=$(lsof -ti:8001 2>/dev/null || echo "")
    FRONTEND_PID=$(lsof -ti:3000 2>/dev/null || echo "")
fi

# Stop services in reverse order
echo -e "${BLUE}🛑 Stopping services...${NC}"

# 5. Stop Frontend
kill_process "$FRONTEND_PID" "Frontend"

# 4. Stop Intent Classifier  
kill_process "$INTENT_PID" "Intent Classifier"

# 3. Stop Backend
kill_process "$BACKEND_PID" "Backend"

# 2. Stop Embedding Server
kill_process "$EMBEDDING_PID" "Embedding Server"

# 1. Stop Search Server
kill_process "$SEARCH_PID" "Search Server"

# Clean up PID file
rm -f logs/service-pids.txt

# Additional cleanup - kill any remaining processes on our ports
echo -e "${BLUE}🧹 Cleaning up any remaining processes...${NC}"

for port in 3000 8000 8001 8002 8080; do
    pid=$(lsof -ti:$port 2>/dev/null || echo "")
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}   Killing process on port $port (PID: $pid)${NC}"
        kill -9 "$pid" 2>/dev/null || true
    fi
done

echo ""
echo -e "${GREEN}🎉 All services stopped successfully!${NC}"
echo "=============================================="
echo -e "${BLUE}💡 To start services again, run: ./start-services.sh${NC}"
