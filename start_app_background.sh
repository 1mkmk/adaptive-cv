#!/bin/bash

# Script to start the AdaptiveCV application on macOS in background mode
# Created by Claude Code

# Configuration
BACKEND_DIR="./backend"
FRONTEND_DIR="./frontend"
BACKEND_PORT=8000
FRONTEND_PORT=5173
BACKEND_LOG="./backend_log.txt"
FRONTEND_LOG="./frontend_log.txt"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to display ASCII art header
show_header() {
  echo -e "${BLUE}"
  echo "    _       _            _   _          _____   __    "
  echo "   / \   __| | __ _ _ __| |_(_)_   ____|_   _|  \ \   "
  echo "  / _ \ / _\` |/ _\` | '__| __| \ \ / / _ \| |_____| |  "
  echo " / ___ \ (_| | (_| | |  | |_| |\ V /  __/| |_____| |  "
  echo "/_/   \_\__,_|\__,_|_|   \__|_| \_/ \___||_|     | |  "
  echo "                                                 /_/   "
  echo "                 AdaptiveCV                            "
  echo -e "${NC}"
}

# Check prerequisites
check_prerequisites() {
  echo -e "${BLUE}Checking prerequisites...${NC}"
  
  # Check for Python
  if ! command_exists python3; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 to continue.${NC}"
    exit 1
  else
    echo -e "${GREEN}✓ Python 3 is installed${NC}"
  fi
  
  # Check for Node.js
  if ! command_exists node; then
    echo -e "${RED}Node.js is not installed. Please install Node.js to continue.${NC}"
    exit 1
  else
    echo -e "${GREEN}✓ Node.js is installed${NC}"
  fi
  
  # Check for npm
  if ! command_exists npm; then
    echo -e "${RED}npm is not installed. Please install npm to continue.${NC}"
    exit 1
  else
    echo -e "${GREEN}✓ npm is installed${NC}"
  fi
  
  # Check for pip
  if ! command_exists pip3; then
    echo -e "${RED}pip3 is not installed. Please install pip3 to continue.${NC}"
    exit 1
  else
    echo -e "${GREEN}✓ pip3 is installed${NC}"
  fi
}

# Install backend dependencies
install_backend_deps() {
  echo -e "${BLUE}Installing backend dependencies...${NC}"
  cd "$BACKEND_DIR" || { echo -e "${RED}Backend directory not found${NC}"; exit 1; }
  pip3 install -r requirements.txt
  
  # Check if .env file exists, if not create it
  if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    echo "# Environment variables for Adaptive CV backend
# Replace with your actual API keys in production

# OpenAI API Key for CV generation
OPENAI_API_KEY=\"your-openai-api-key\"

# Database settings
DATABASE_URL=\"sqlite:///adaptive_cv.db\"

# Server settings
HOST=\"0.0.0.0\"
PORT=8000
DEBUG=true" > .env
    echo -e "${YELLOW}Please edit the .env file in the backend directory to add your OpenAI API key${NC}"
  fi
  
  cd ..
  echo -e "${GREEN}Backend dependencies installed${NC}"
}

# Install frontend dependencies
install_frontend_deps() {
  echo -e "${BLUE}Installing frontend dependencies...${NC}"
  cd "$FRONTEND_DIR" || { echo -e "${RED}Frontend directory not found${NC}"; exit 1; }
  npm install
  
  # Check if .env file exists, if not create it
  if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    echo "# Frontend environment variables
VITE_API_URL=http://localhost:8000" > .env
  fi
  
  cd ..
  echo -e "${GREEN}Frontend dependencies installed${NC}"
}

# Function to check if a port is in use
is_port_in_use() {
  lsof -i :"$1" >/dev/null 2>&1
  return $?
}

# Start backend server
start_backend() {
  echo -e "${BLUE}Starting backend server...${NC}"
  
  # Zatrzymaj wszystkie istniejące procesy na tym porcie
  if is_port_in_use "$BACKEND_PORT"; then
    echo -e "${YELLOW}Port $BACKEND_PORT is already in use. Stopping existing process...${NC}"
    lsof -ti :$BACKEND_PORT | xargs kill -9 2>/dev/null
    sleep 1
  fi
  
  cd "$BACKEND_DIR" || { echo -e "${RED}Backend directory not found${NC}"; exit 1; }
  
  # Clear previous log file
  > "../$BACKEND_LOG"
  
  # Dodaj informacje diagnostyczne do loga
  {
    echo "=== BACKEND SERVER START - $(date) ==="
    echo "Working directory: $(pwd)"
    echo "Python version: $(python --version 2>&1)"
    echo "Installed packages:"
    pip list 2>&1
    echo "Environment variables:"
    env | grep -v "SECRET\|KEY\|PASSWORD\|TOKEN" 2>&1
    echo "=== STARTING SERVER ==="
  } >> "../$BACKEND_LOG"
  
  # Generate template previews
  echo -e "${GREEN}Generating LaTeX template previews...${NC}"
  python pdf_to_jpg.py >> "../$BACKEND_LOG" 2>&1
  
  # Start backend with more verbose logging
  echo -e "${GREEN}Starting uvicorn with enhanced logging...${NC}"
  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT" --log-level debug >> "../$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!
  
  # Save PID to file for easy shutdown later
  echo "$BACKEND_PID" > "../.backend_pid"
  
  # Wait a bit to ensure the server has started
  echo -e "${BLUE}Waiting for backend to start...${NC}"
  max_retries=10
  retries=0
  
  while [ $retries -lt $max_retries ]; do
    sleep 2
    if curl -s "http://localhost:$BACKEND_PORT/docs" > /dev/null; then
      echo -e "${GREEN}Backend server started successfully at http://localhost:$BACKEND_PORT (PID: $BACKEND_PID)${NC}"
      break
    fi
    retries=$((retries+1))
    echo -e "${YELLOW}Waiting for backend to start (attempt $retries/$max_retries)...${NC}"
    
    # Check if process is still running
    if ! ps -p "$BACKEND_PID" > /dev/null; then
      echo -e "${RED}Backend process died. Check the logs for details.${NC}"
      echo -e "${YELLOW}Last few lines of backend log:${NC}"
      tail -n 20 "../$BACKEND_LOG"
      
      # Try to restart
      echo -e "${YELLOW}Attempting to restart backend...${NC}"
      python -m uvicorn app.main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT" --log-level debug >> "../$BACKEND_LOG" 2>&1 &
      BACKEND_PID=$!
      echo "$BACKEND_PID" > "../.backend_pid"
    fi
  done
  
  if [ $retries -eq $max_retries ]; then
    echo -e "${RED}Failed to start backend server after $max_retries attempts.${NC}"
    echo -e "${YELLOW}Last few lines of backend log:${NC}"
    tail -n 30 "../$BACKEND_LOG"
  fi
  
  cd ..
  echo -e "${BLUE}Backend logs are being written to $BACKEND_LOG${NC}"
}

# Start proxy server
start_proxy() {
  echo -e "${BLUE}Starting API proxy server...${NC}"
  
  # Zatrzymaj wszystkie istniejące procesy na tym porcie
  if is_port_in_use "3001"; then
    echo -e "${YELLOW}Port 3001 is already in use. Stopping existing process...${NC}"
    lsof -ti :3001 | xargs kill -9 2>/dev/null
    sleep 1
  fi
  
  cd "$FRONTEND_DIR" || { echo -e "${RED}Frontend directory not found${NC}"; exit 1; }
  
  # Clear previous log file
  > "../proxy_log.txt"
  
  # Dodaj informacje diagnostyczne do loga
  {
    echo "=== PROXY SERVER START - $(date) ==="
    echo "Working directory: $(pwd)"
    echo "Node version: $(node --version 2>&1)"
    echo "NPM version: $(npm --version 2>&1)"
    echo "Installed packages:"
    grep -A50 "dependencies" package.json 2>&1
    echo "Environment variables:"
    env | grep "NODE\|NPM\|PATH" | grep -v "SECRET\|KEY\|PASSWORD\|TOKEN" 2>&1
    echo "=== STARTING PROXY ==="
  } >> "../proxy_log.txt"
  
  # Start proxy in background
  echo -e "${GREEN}Starting API proxy server...${NC}"
  NODE_OPTIONS="--trace-warnings --trace-uncaught" npm run proxy >> "../proxy_log.txt" 2>&1 &
  PROXY_PID=$!
  
  # Save PID to file for easy shutdown later
  echo "$PROXY_PID" > "../.proxy_pid"
  
  # Wait a bit to ensure the server has started
  echo -e "${BLUE}Waiting for proxy to start...${NC}"
  max_retries=10
  retries=0
  
  while [ $retries -lt $max_retries ]; do
    sleep 2
    if curl -s "http://localhost:3001" > /dev/null; then
      echo -e "${GREEN}API proxy server started successfully at http://localhost:3001 (PID: $PROXY_PID)${NC}"
      break
    fi
    retries=$((retries+1))
    echo -e "${YELLOW}Waiting for proxy to start (attempt $retries/$max_retries)...${NC}"
    
    # Check if process is still running
    if ! ps -p "$PROXY_PID" > /dev/null; then
      echo -e "${RED}Proxy process died. Check the logs for details.${NC}"
      echo -e "${YELLOW}Last few lines of proxy log:${NC}"
      tail -n 20 "../proxy_log.txt"
      
      # Try to restart
      echo -e "${YELLOW}Attempting to restart proxy...${NC}"
      NODE_OPTIONS="--trace-warnings --trace-uncaught" npm run proxy >> "../proxy_log.txt" 2>&1 &
      PROXY_PID=$!
      echo "$PROXY_PID" > "../.proxy_pid"
    fi
  done
  
  if [ $retries -eq $max_retries ]; then
    echo -e "${RED}Failed to start proxy server after $max_retries attempts.${NC}"
    echo -e "${YELLOW}Last few lines of proxy log:${NC}"
    tail -n 30 "../proxy_log.txt"
  fi
  
  cd ..
}

# Start frontend server
start_frontend() {
  echo -e "${BLUE}Starting frontend server...${NC}"
  
  # Start proxy server first
  start_proxy
  
  # Check if port is already in use
  if is_port_in_use "$FRONTEND_PORT"; then
    echo -e "${YELLOW}Port $FRONTEND_PORT is already in use. Frontend may already be running.${NC}"
    return
  fi
  
  cd "$FRONTEND_DIR" || { echo -e "${RED}Frontend directory not found${NC}"; exit 1; }
  
  # Clear previous log file
  > "../$FRONTEND_LOG"
  
  # Ensure environment variables are set correctly
  echo "# Frontend environment variables
VITE_API_URL=http://localhost:3001/api" > .env
  
  # Start frontend in background and direct output to log file
  echo -e "${GREEN}Starting Vite dev server...${NC}"
  
  # Different handling for newer npm that uses exec which can lose the PID
  npx --no -- vite --port "$FRONTEND_PORT" --host > "../$FRONTEND_LOG" 2>&1 &
  FRONTEND_PID=$!
  
  # Also get child process in case npm creates a sub-process
  sleep 2
  CHILD_PID=$(pgrep -P $FRONTEND_PID 2>/dev/null || echo "")
  
  # Save PIDs to file for easy shutdown later
  echo "$FRONTEND_PID" > "../.frontend_pid"
  if [ -n "$CHILD_PID" ]; then
    echo "$CHILD_PID" >> "../.frontend_pid"
  fi
  
  # Wait a bit to ensure the server has started
  sleep 5
  
  # Check if server started successfully
  if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null; then
    echo -e "${GREEN}Frontend server started successfully at http://localhost:$FRONTEND_PORT (PID: $FRONTEND_PID)${NC}"
  else
    echo -e "${RED}Frontend server might have failed to start. Check the logs for details.${NC}"
    echo -e "${YELLOW}Last few lines of frontend log:${NC}"
    tail "../$FRONTEND_LOG"
  fi
  
  cd ..
  echo -e "${BLUE}Frontend logs are being written to $FRONTEND_LOG${NC}"
}

# Function to stop servers
stop_servers() {
  echo -e "${BLUE}Stopping AdaptiveCV servers...${NC}"
  
  # Stop backend
  if [ -f ".backend_pid" ]; then
    BACKEND_PID=$(cat .backend_pid)
    if ps -p "$BACKEND_PID" > /dev/null; then
      echo -e "${GREEN}Stopping backend server (PID: $BACKEND_PID)...${NC}"
      kill "$BACKEND_PID" 2>/dev/null || kill -9 "$BACKEND_PID" 2>/dev/null
      sleep 1
    else
      echo -e "${YELLOW}Backend server process not found${NC}"
    fi
    rm .backend_pid
  else
    echo -e "${YELLOW}No backend PID file found${NC}"
  fi
  
  # Stop proxy server
  if [ -f ".proxy_pid" ]; then
    PROXY_PID=$(cat .proxy_pid)
    if ps -p "$PROXY_PID" > /dev/null; then
      echo -e "${GREEN}Stopping proxy server (PID: $PROXY_PID)...${NC}"
      kill "$PROXY_PID" 2>/dev/null || kill -9 "$PROXY_PID" 2>/dev/null
      sleep 1
    else
      echo -e "${YELLOW}Proxy server process not found${NC}"
    fi
    rm .proxy_pid
  else
    echo -e "${YELLOW}No proxy PID file found${NC}"
  fi
  
  # Stop frontend - read all PIDs from file
  if [ -f ".frontend_pid" ]; then
    echo -e "${GREEN}Stopping frontend server...${NC}"
    while IFS= read -r PID; do
      if ps -p "$PID" > /dev/null; then
        echo -e "${GREEN}Stopping frontend process (PID: $PID)${NC}"
        kill "$PID" 2>/dev/null || kill -9 "$PID" 2>/dev/null
      fi
    done < .frontend_pid
    rm .frontend_pid
  else
    echo -e "${YELLOW}No frontend PID file found${NC}"
  fi
  
  # Kill any remaining related processes
  echo -e "${BLUE}Checking for any remaining processes...${NC}"
  
  # Try more targeted kill for specific processes
  for PROC in "uvicorn app.main:app" "vite" "node.*vite" "node.*proxy.mjs"; do
    PIDS=$(pgrep -f "$PROC" 2>/dev/null)
    if [ -n "$PIDS" ]; then
      echo -e "${YELLOW}Found remaining $PROC processes, stopping...${NC}"
      for PID in $PIDS; do
        kill "$PID" 2>/dev/null || kill -9 "$PID" 2>/dev/null
      done
    fi
  done
  
  echo -e "${GREEN}All AdaptiveCV servers stopped${NC}"
  
  # Free up the ports
  for PORT in $BACKEND_PORT $FRONTEND_PORT 3001; do
    if lsof -ti :$PORT > /dev/null; then
      echo -e "${YELLOW}Force closing any process on port $PORT${NC}"
      lsof -ti :$PORT | xargs kill -9 2>/dev/null
    fi
  done
}

# Show logs
show_logs() {
  echo -e "${BLUE}Showing the most recent logs:${NC}"
  
  if [ -f "$BACKEND_LOG" ]; then
    echo -e "${YELLOW}Backend logs:${NC}"
    tail -n 20 "$BACKEND_LOG"
    echo
  else
    echo -e "${RED}Backend log file not found${NC}"
  fi
  
  if [ -f "proxy_log.txt" ]; then
    echo -e "${YELLOW}Proxy logs:${NC}"
    tail -n 20 "proxy_log.txt"
    echo
  else
    echo -e "${RED}Proxy log file not found${NC}"
  fi
  
  if [ -f "$FRONTEND_LOG" ]; then
    echo -e "${YELLOW}Frontend logs:${NC}"
    tail -n 20 "$FRONTEND_LOG"
  else
    echo -e "${RED}Frontend log file not found${NC}"
  fi
}

# Reset database
reset_database() {
  echo -e "${BLUE}Resetting database...${NC}"
  
  # Stop the backend server if it's running
  if [ -f ".backend_pid" ]; then
    BACKEND_PID=$(cat .backend_pid)
    if ps -p "$BACKEND_PID" > /dev/null; then
      echo -e "${YELLOW}Stopping backend server to reset database...${NC}"
      kill "$BACKEND_PID" 2>/dev/null || kill -9 "$BACKEND_PID" 2>/dev/null
      sleep 1
      rm .backend_pid
    fi
  fi
  
  # Run the reset script
  cd "$BACKEND_DIR" || { echo -e "${RED}Backend directory not found${NC}"; exit 1; }
  
  # Run the reset_db.py script
  python reset_db.py
  
  echo -e "${GREEN}Database reset completed${NC}"
  cd ..
}

# Main function
main() {
  show_header
  
  # Process command line arguments
  case "$1" in
    stop)
      stop_servers
      exit 0
      ;;
    logs)
      show_logs
      exit 0
      ;;
    restart)
      stop_servers
      echo "Restarting servers..."
      sleep 2
      # Continue with normal startup
      ;;
    reset-db)
      reset_database
      exit 0
      ;;
    reset-and-start)
      reset_database
      # Continue with normal startup
      ;;
    *)
      # Continue with normal startup
      ;;
  esac
  
  check_prerequisites
  
  # Ask if user wants to install dependencies
  echo -e "${YELLOW}Do you want to install dependencies? (y/n)${NC}"
  read -r INSTALL_DEPS
  
  if [[ "$INSTALL_DEPS" =~ ^[Yy]$ ]]; then
    install_backend_deps
    install_frontend_deps
  fi
  
  # Start backend and frontend servers
  start_backend
  start_frontend
  
  echo -e "${GREEN}AdaptiveCV is now running!${NC}"
  echo -e "${BLUE}Backend server: ${NC}http://localhost:$BACKEND_PORT"
  echo -e "${BLUE}Frontend application: ${NC}http://localhost:$FRONTEND_PORT"
  echo -e "${YELLOW}Don't forget to set your OpenAI API key in backend/.env${NC}"
  echo
  echo -e "${BLUE}To stop the servers, run: ${NC}./$(basename "$0") stop"
  echo -e "${BLUE}To view logs, run: ${NC}./$(basename "$0") logs"
  echo -e "${BLUE}To restart the servers, run: ${NC}./$(basename "$0") restart"
  echo -e "${BLUE}To reset the database, run: ${NC}./$(basename "$0") reset-db"
  echo -e "${BLUE}To reset the database and start the app, run: ${NC}./$(basename "$0") reset-and-start"
}

# Execute main function
main "$@"