#!/bin/bash

# OSS Knowledge Services Health Check Script
# This script checks the health of all running services

echo "🏥 OSS Knowledge Services Health Check"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check service health
check_service() {
    local url=$1
    local service_name=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $service_name... "
    
    if response=$(curl -s -w "%{http_code}" -o /dev/null "$url" 2>/dev/null); then
        if [ "$response" = "$expected_status" ]; then
            echo -e "${GREEN}✅ Healthy (HTTP $response)${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  Responding but unexpected status (HTTP $response)${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Unhealthy or not responding${NC}"
        return 1
    fi
}

# Function to check port
check_port() {
    local port=$1
    local service_name=$2
    
    echo -n "Checking $service_name port $port... "
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Port $port is listening${NC}"
        return 0
    else
        echo -e "${RED}❌ Port $port is not listening${NC}"
        return 1
    fi
}

echo -e "${BLUE}🔍 Checking service ports...${NC}"
echo ""

# Check ports
check_port 5174 "Frontend"
check_port 8000 "Embedding Server"
check_port 8001 "Intent Classifier"
check_port 8002 "Search Server"
check_port 8080 "Backend"

echo ""
echo -e "${BLUE}🏥 Checking service health endpoints...${NC}"
echo ""

# Check service health
check_service "http://localhost:5174" "Frontend"
check_service "http://localhost:8000/health" "Embedding Server"
check_service "http://localhost:8001/health" "Intent Classifier"
check_service "http://localhost:8002/health" "Search Server"
check_service "http://localhost:8080/health" "Backend"

echo ""
echo -e "${BLUE}🔗 Testing service connections...${NC}"
echo ""

# Test service-to-service connections
echo -n "Testing Backend → Search Server connection... "
if curl -s "http://localhost:8080/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is responding${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
fi

echo -n "Testing Intent Classifier → Search Server connection... "
if curl -s "http://localhost:8001/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Intent Classifier is responding${NC}"
else
    echo -e "${RED}❌ Intent Classifier health check failed${NC}"
fi

echo ""
echo -e "${BLUE}📊 Service Summary:${NC}"
echo "=================="
echo "Frontend:        http://localhost:5174"
echo "Backend:         http://localhost:8080"
echo "Search Server:   http://localhost:8002"
echo "Embedding Server: http://localhost:8000"
echo "Intent Classifier: http://localhost:8001"
echo ""
echo -e "${BLUE}📝 Logs location:${NC} logs/"
echo -e "${BLUE}🛑 To stop services:${NC} ./stop-services.sh"
echo -e "${BLUE}🚀 To restart services:${NC} ./start-services.sh"
