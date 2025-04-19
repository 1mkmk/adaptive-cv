#!/bin/bash

# Script to start the AdaptiveCV application on macOS
# Created by Claude Code

# Configuration
BACKEND_DIR="./backend"
FRONTEND_DIR="./frontend"
BACKEND_PORT=8000
FRONTEND_PORT=5173

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
  echo "  _____     _            _   _            _____   __      __"
  echo " |  __ \   | |          | | (_)          / ____| /\ \    / /"
  echo " | |__) |__| | __ _ _ __| |_ ___   _____| |     /  \ \  / / "
  echo " |  ___/ _ \ |/ _\` | '_ \ __| \ \ / / _ \ |    /    \ \/ /  "
  echo " | |  |  __/ | (_| | |_) | |_| |\ V /  __/ |___|    /\  /   "
  echo " |_|   \___|_|\__,_| .__/ \__|_| \_/ \___\_____|   /  \/    "
  echo "                    | |                                      "
  echo "                    |_|                                      "
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

# Start backend server
start_backend() {
  echo -e "${BLUE}Starting backend server...${NC}"
  cd "$BACKEND_DIR" || { echo -e "${RED}Backend directory not found${NC}"; exit 1; }
  
  # Start in a new terminal window on macOS and keep it open
  osascript <<EOF
    tell application "Terminal"
      do script "cd $(pwd) && uvicorn app.main:app --reload --port $BACKEND_PORT; exec bash"
      set current settings of selected tab of front window to settings set "Basic"
      set custom title of front window to "AdaptiveCV Backend"
    end tell
EOF
  
  cd ..
  echo -e "${GREEN}Backend server starting at http://localhost:$BACKEND_PORT${NC}"
}

# Start frontend server
start_frontend() {
  echo -e "${BLUE}Starting frontend server...${NC}"
  cd "$FRONTEND_DIR" || { echo -e "${RED}Frontend directory not found${NC}"; exit 1; }
  
  # Start in a new terminal window on macOS and keep it open
  osascript <<EOF
    tell application "Terminal"
      do script "cd $(pwd) && npm run dev -- --port $FRONTEND_PORT; exec bash"
      set current settings of selected tab of front window to settings set "Basic"
      set custom title of front window to "AdaptiveCV Frontend"
    end tell
EOF
  
  cd ..
  echo -e "${GREEN}Frontend server starting at http://localhost:$FRONTEND_PORT${NC}"
}

# Main function
main() {
  show_header
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
}

# Execute main function
main