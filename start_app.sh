#!/usr/bin/env bash

# AdaptiveCV Startup Script for macOS/Linux
# Wersja: 2.6 — z loggingiem, obsługą SIGTERM/SIGINT, status, port checks, auto-kill, ścieżkami absolutnymi, virtualenv i business-card

set -euo pipefail

# -----------------------------------
# Base Directories (absolute)
# -----------------------------------
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$BASE_DIR/backend"
FRONTEND_DIR="$BASE_DIR/frontend"
BUSINESS_CARD_DIR="$BASE_DIR/business-card/business-card"
PID_DIR="$BASE_DIR/.pids"
LOG_DIR="$BASE_DIR/logs"
VENV_DIR="$BASE_DIR/.venv"

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=5173
BUSINESS_CARD_PORT=3002

# Colors
GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

# -----------------------------------
# Helpers
# -----------------------------------
command_exists() { command -v "$1" > /dev/null 2>&1; }

error_exit() {
  echo -e "${RED}[ERROR]${NC} $1" >&2
  exit 1
}

info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

ensure_dirs() {
  mkdir -p "$PID_DIR" "$LOG_DIR"
}

# -----------------------------------
# Virtual Environment Management
# -----------------------------------
ensure_venv() {
  # Check if Python3 is installed
  if ! command_exists python3; then
    error_exit "Python3 not found. Please install Python 3.x"
  fi
  
  # Check if venv module is available
  if ! python3 -m venv --help >/dev/null 2>&1; then
    error_exit "Python venv module not available. Install it with: sudo apt-get install python3-venv"
  fi
  
  # Check if venv exists, create if not
  if [ ! -d "$VENV_DIR" ]; then
    info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR" || error_exit "Failed to create virtual environment"
    # Give it a moment to set up
    sleep 1
  fi

  # Check for Python and pip in the virtual environment
  if [ -f "$VENV_DIR/bin/python" ]; then
    PYTHON_BIN="$VENV_DIR/bin/python"
    info "Using Python binary: $PYTHON_BIN"
    
    # Install pip if needed
    if [ ! -f "$VENV_DIR/bin/pip" ]; then
      info "Installing pip in the virtual environment..."
      $PYTHON_BIN -m ensurepip || $PYTHON_BIN -m ensurepip --upgrade || true
    fi
    
    if [ -f "$VENV_DIR/bin/pip" ]; then
      PIP_BIN="$VENV_DIR/bin/pip"
      info "Using pip binary: $PIP_BIN"
      
      # Install basic packages
      info "Installing basic packages in environment..."
      $PIP_BIN install --upgrade pip
    else
      PIP_BIN="$PYTHON_BIN -m pip"
      info "Using pip module: $PIP_BIN"
      $PYTHON_BIN -m pip install --upgrade pip
    fi
    
    # Try to activate but don't fail if not possible
    if [ -f "$VENV_DIR/bin/activate" ]; then
      # shellcheck disable=SC1090
      source "$VENV_DIR/bin/activate" 2>/dev/null || true
    fi
  else
    # Fallback to system Python
    warn "Virtual environment not properly setup. Using system Python."
    PYTHON_BIN="python3"
    PIP_BIN="pip3"
  fi
}

# -----------------------------------
# Check Port; prompt kill if busy
# -----------------------------------
check_port_free() {
  local port=$1
  local pids=( $(lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null) )
  if [[ ${#pids[@]} -gt 0 ]]; then
    warn "Port $port jest zajęty przez PID: ${pids[*]}"
    read -rp "Zabić procesy ${pids[*]} używające portu $port? (y/N): " yn
    if [[ "$yn" =~ ^[Yy]$ ]]; then
      for p in "${pids[@]}"; do
        if kill "$p" 2>/dev/null; then
          info "Zabito proces PID $p"
        else
          warn "Nie udało się zabić procesu PID $p"
        fi
      done
      sleep 1
    else
      error_exit "Port $port nadal zajęty. Przerywam."
    fi
  fi
}

# -----------------------------------
# PID file operations
# -----------------------------------
write_pid() {
  local name=$1 pid=$2
  echo "$pid" > "$PID_DIR/${name}.pid"
}

read_pid() {
  local name=$1
  [[ -f "$PID_DIR/${name}.pid" ]] && cat "$PID_DIR/${name}.pid" || echo ""
}

service_running() {
  local name=$1 pid
  pid=$(read_pid "$name")
  [[ -n "$pid" && "$(ps -p $pid -o pid=)" =~ $pid ]]
}

trap 'stop_services; exit' SIGINT SIGTERM

# -----------------------------------
# Service Functions
# -----------------------------------
# In the start_backend() function, add dependency checking before starting:

start_backend() {
  info "Sprawdzam port $BACKEND_PORT..."
  check_port_free "$BACKEND_PORT"
  info "Uruchamiam backend..."
  cd "$BACKEND_DIR" || error_exit "Nie znaleziono katalogu backend"
  
  # Activate virtual environment before running backend
  ensure_venv
  
  # Install backend dependencies if needed
  info "Checking backend dependencies..."
  if [ -n "$PIP_BIN" ]; then
    # Using path directly
    if [[ "$PIP_BIN" == *"-m pip"* ]]; then
      # Using as module
      $PYTHON_BIN -m pip install --upgrade pip
      $PYTHON_BIN -m pip install -r requirements.txt
      $PYTHON_BIN -m pip install uvicorn fastapi
    else
      # Using binary
      $PIP_BIN install --upgrade pip
      $PIP_BIN install -r requirements.txt
      $PIP_BIN install uvicorn fastapi
    fi
  else
    # Fallback to system pip if all else fails
    pip3 install --upgrade pip
    pip3 install -r requirements.txt
    pip3 install uvicorn fastapi
  fi
  
  # Start the backend using the best available method
  info "Starting backend server..."
  
  # First try using the module approach with our Python binary
  if [ -n "$PYTHON_BIN" ]; then
    info "Starting with Python binary: $PYTHON_BIN"
    $PYTHON_BIN -m uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT \
      >> "$LOG_DIR/backend.log" 2>&1 &
  elif [ -f "$VENV_DIR/bin/uvicorn" ]; then
    # Try the venv's uvicorn if it exists
    info "Starting with venv uvicorn binary"
    "$VENV_DIR/bin/uvicorn" app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT \
      >> "$LOG_DIR/backend.log" 2>&1 &
  elif command_exists uvicorn; then
    # Try system uvicorn if it exists
    info "Starting with system uvicorn"
    uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT \
      >> "$LOG_DIR/backend.log" 2>&1 &
  else
    # Last resort with system python
    info "Starting with system Python module"
    python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT \
      >> "$LOG_DIR/backend.log" 2>&1 &
  fi
  
  write_pid backend $!
  cd "$BASE_DIR" >/dev/null
  info "Backend PID $(read_pid backend), log: $(basename $LOG_DIR)/backend.log"
}

start_frontend() {
  info "Sprawdzam port $FRONTEND_PORT..."
  check_port_free "$FRONTEND_PORT"
  info "Uruchamiam frontend..."
  cd "$FRONTEND_DIR" || error_exit "Nie znaleziono katalogu frontend"
  npm run dev -- --port $FRONTEND_PORT \
    >> "$LOG_DIR/frontend.log" 2>&1 &
  write_pid frontend $!
  cd "$BASE_DIR" >/dev/null
  info "Frontend PID $(read_pid frontend), log: $(basename $LOG_DIR)/frontend.log"
}

start_proxy() {
  info "Sprawdzam port 3001..."
  check_port_free 3001
  info "Uruchamiam proxy..."
  
  if [ ! -f "$FRONTEND_DIR/proxy.mjs" ]; then
    error_exit "Nie znaleziono pliku proxy.mjs w katalogu frontend"
  fi
  
  cd "$FRONTEND_DIR" || error_exit "Nie znaleziono katalogu frontend"
  
  # Start proxy.mjs
  node proxy.mjs >> "$LOG_DIR/proxy.log" 2>&1 &
  write_pid proxy $!
  cd "$BASE_DIR" >/dev/null
  info "Proxy PID $(read_pid proxy), log: $(basename $LOG_DIR)/proxy.log"
}

start_business_card() {
  info "Sprawdzam port $BUSINESS_CARD_PORT..."
  check_port_free "$BUSINESS_CARD_PORT"
  info "Uruchamiam business-card..."
  cd "$BUSINESS_CARD_DIR" || error_exit "Nie znaleziono katalogu business-card"
  npm run dev -- --port $BUSINESS_CARD_PORT \
    >> "$LOG_DIR/business-card.log" 2>&1 &
  write_pid business-card $!
  cd "$BASE_DIR" >/dev/null
  info "Business-Card PID $(read_pid business-card), log: $(basename $LOG_DIR)/business-card.log"
}

generate_template_previews() {
  info "Generowanie podglądów szablonów..."
  
  cd "$BACKEND_DIR" || error_exit "Nie znaleziono katalogu backend"
  
  # Activate virtual environment
  ensure_venv
  
  # Run the template preview generation script
  info "Uruchamiam skrypt generowania podglądów szablonów..."
  
  # Use the appropriate Python binary
  if [ -n "$PYTHON_BIN" ]; then
    $PYTHON_BIN generate_template_previews.py >> "$LOG_DIR/template_previews.log" 2>&1 || true
  else
    python generate_template_previews.py >> "$LOG_DIR/template_previews.log" 2>&1 || true
  fi
  
  local result=$?
  if [ $result -ne 0 ]; then
    warn "Generowanie podglądów szablonów zakończyło się błędem. Sprawdź log: $(basename $LOG_DIR)/template_previews.log"
  else
    info "Podglądy szablonów zostały wygenerowane pomyślnie."
  fi
  
  cd "$BASE_DIR" >/dev/null
}

install_deps() {
  info "Instaluję zależności backendu..."
  cd "$BACKEND_DIR" || error_exit "Nie znaleziono katalogu backend"
  
  # Activate virtual environment
  ensure_venv
  
  # Use the appropriate pip method
  if [ -n "$PIP_BIN" ]; then
    if [[ "$PIP_BIN" == *"-m pip"* ]]; then
      # Using as module
      $PYTHON_BIN -m pip install --upgrade pip
      $PYTHON_BIN -m pip install -r requirements.txt
      $PYTHON_BIN -m pip install uvicorn fastapi
    else
      # Using binary
      $PIP_BIN install --upgrade pip
      $PIP_BIN install -r requirements.txt
      $PIP_BIN install uvicorn fastapi
    fi
  else
    # Fallback to system pip
    pip3 install --upgrade pip
    pip3 install -r requirements.txt
    pip3 install uvicorn fastapi
  fi
  
  cd "$BASE_DIR" >/dev/null
  info "Instaluję zależności frontendu..."
  cd "$FRONTEND_DIR" || error_exit "Nie znaleziono katalogu frontend"
  
  # Check if npm is available
  if command_exists npm; then
    npm install
  else
    warn "npm not found. Please install Node.js and npm."
  fi
  
  cd "$BASE_DIR" >/dev/null
  
  info "Instaluję zależności business-card..."
  cd "$BUSINESS_CARD_DIR" || error_exit "Nie znaleziono katalogu business-card"
  
  # Check if npm is available
  if command_exists npm; then
    npm install
  else
    warn "npm not found. Please install Node.js and npm."
  fi
  
  cd "$BASE_DIR" >/dev/null
}

stop_services() {
  info "Zatrzymuję serwisy..."
  for name in backend frontend proxy business-card; do
    pid=$(read_pid "$name")
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" && info "Zatrzymano $name (PID $pid)"
    else
      warn "$name nie działa lub PID nieznaleziony"
    fi
    rm -f "$PID_DIR/${name}.pid"
  done
}

status_services() {
  echo
  for name in backend frontend proxy business-card; do
    if service_running "$name"; then
      printf "%-12s: ${GREEN}RUNNING${NC} (PID %s)\n" "$name" "$(read_pid $name)"
    else
      printf "%-12s: ${RED}STOPPED${NC}\n" "$name"
    fi
  done
  echo
}

# -----------------------------------
# Main
# -----------------------------------
ensure_dirs

case "${1:-start}" in
  start)
    if [[ "${2:-}" == "deps" ]]; then
      install_deps
      shift
    fi
    if [[ "${2:-}" != "nodeps" ]]; then
      generate_template_previews || true
    fi
    start_backend
    start_frontend
    start_business_card
    start_proxy
    ;;

  stop)
    stop_services
    ;;

  status)
    status_services
    ;;

  restart)
    stop_services
    if [[ "${2:-}" != "nodeps" ]]; then
      generate_template_previews || true
    fi
    start_backend
    start_frontend
    start_business_card
    start_proxy
    ;;

  *)
    echo -e "${YELLOW}Użycie:${NC} $0 {start|stop|status|restart} [deps|nodeps]" >&2
    exit 1
    ;;
esac