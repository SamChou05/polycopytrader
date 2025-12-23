#!/bin/bash

# ╔════════════════════════════════════════════════════════╗
# ║         POLYMARKET TERMINAL - START SCRIPT             ║
# ╚════════════════════════════════════════════════════════╝

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║         POLYMARKET TERMINAL - STARTING...              ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Copy .env.example and add your keys:${NC}"
    echo "   cp .env.example .env"
    echo ""
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    kill $API_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start API server in background
echo -e "${GREEN}Starting API server...${NC}"
python run_api.py &
API_PID=$!

# Wait for API to be ready
sleep 2

# Start frontend
echo -e "${GREEN}Starting frontend...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 3

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    ✅ READY!                           ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Frontend:   http://localhost:3000                     ║${NC}"
echo -e "${GREEN}║  API:        http://localhost:5001/api                 ║${NC}"
echo -e "${GREEN}║  Health:     http://localhost:5001/api/health          ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Press Ctrl+C to stop all services                     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Wait for processes
wait
