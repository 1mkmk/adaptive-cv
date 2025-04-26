#!/usr/bin/env bash

# AdaptiveCV Startup Script for macOS/Linux
# Versja: 2.5 — z loggingiem, obsługą SIGTERM/SIGINT, status, port checks, auto-kill, ścieżkami absolutnymi i virtualenv

set -euo pipefail

# -----------------------------------
# Base Directories (absolute)
# -----------------------------------
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$BASE_DIR/backend"
FRONTEND_DIR="$BASE_DIR/frontend"
PID_DIR="$BASE_DIR/.pids"
LOG_DIR="$BASE_DIR/logs"
VENV_DIR="$BASE_DIR/.venv"

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=5173

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
  
  # Check if venv exists, create if not
  if [ ! -d "$VENV_DIR" ]; then
    info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR" || error_exit "Failed to create virtual environment"
  fi
  
  # Source the activate script to use the venv
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate" || error_exit "Failed to activate virtual environment"
  
  info "Using Python: $(which python)"
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
  
  # Check if uvicorn is installed, if not install dependencies
  if [ ! -f "$VENV_DIR/bin/uvicorn" ]; then
    info "Uvicorn not found in virtual environment. Installing dependencies..."
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r requirements.txt
    "$VENV_DIR/bin/pip" install uvicorn  # Ensure uvicorn is explicitly installed
    
    if [ ! -f "$VENV_DIR/bin/uvicorn" ]; then
      error_exit "Failed to install uvicorn. Please run './start_app.sh start deps' first."
    fi
  fi
  
  # Use venv's uvicorn
  "$VENV_DIR/bin/uvicorn" app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT \
    >> "$LOG_DIR/backend.log" 2>&1 &
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

install_deps() {
  info "Instaluję zależności backendu..."
  cd "$BACKEND_DIR" || error_exit
  
  # Activate virtual environment
  ensure_venv
  
  # Use venv's pip
  "$VENV_DIR/bin/pip" install --upgrade pip
  "$VENV_DIR/bin/pip" install -r requirements.txt
  
  cd "$BASE_DIR" >/dev/null
  info "Instaluję zależności frontendu..."
  cd "$FRONTEND_DIR" || error_exit
  npm install
  cd "$BASE_DIR" >/dev/null
}

stop_services() {
  info "Zatrzymuję serwisy..."
  for name in backend frontend; do
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
  for name in backend frontend; do
    if service_running "$name"; then
      printf "%-8s: ${GREEN}RUNNING${NC} (PID %s)\n" "$name" "$(read_pid $name)"
    else
      printf "%-8s: ${RED}STOPPED${NC}\n" "$name"
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
    start_backend
    start_frontend
    ;;

  stop)
    stop_services
    ;;

  status)
    status_services
    ;;

  restart)
    stop_services
    start_backend
    start_frontend
    ;;

  *)
    echo -e "${YELLOW}Użycie:${NC} $0 {start|stop|status|restart} [deps]" >&2
    exit 1
    ;;
esac