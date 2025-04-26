#!/bin/bash

# Start script for AdaptiveCV with remote LaTeX compilation
# This script starts the application with remote LaTeX processing capabilities

set -e

# Default configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000
PROXY_PORT=8080
ENV=${ENV:-"local"}

# Remote LaTeX server configuration
REMOTE_LATEX_SERVER="karol152.mikrus.xyz"
REMOTE_LATEX_PORT=10152
REMOTE_LATEX_USER="root"
REMOTE_LATEX_SSH_KEY="~/.ssh/id_rsa"

# Control flags
USE_REMOTE_LATEX=true
SYNC_ASSETS=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --no-remote-latex)
      USE_REMOTE_LATEX=false
      shift
      ;;
    --no-sync)
      SYNC_ASSETS=false
      shift
      ;;
    --env=*)
      ENV="${1#*=}"
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --no-remote-latex    Disable remote LaTeX compilation (use local instead)"
      echo "  --no-sync            Skip asset synchronization with remote server"
      echo "  --env=ENV            Set environment (local, development, production)"
      echo "  --help               Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information."
      exit 1
      ;;
  esac
done

# Check if required tools are installed
if [ "$USE_REMOTE_LATEX" = true ]; then
  if ! command -v ssh >/dev/null 2>&1; then
    echo "Error: SSH client not found. Please install SSH client."
    exit 1
  fi
  
  if ! command -v rsync >/dev/null 2>&1; then
    echo "Error: rsync not found. Please install rsync."
    exit 1
  fi
  
  # Test SSH connection
  echo "Testing connection to remote LaTeX server..."
  ssh -o BatchMode=yes -o ConnectTimeout=5 -p "$REMOTE_LATEX_PORT" -i "$REMOTE_LATEX_SSH_KEY" "$REMOTE_LATEX_USER@$REMOTE_LATEX_SERVER" exit &>/dev/null
  if [ $? -ne 0 ]; then
    echo "Warning: Cannot connect to remote LaTeX server. Will use local LaTeX compilation."
    USE_REMOTE_LATEX=false
  else
    echo "Remote LaTeX server connection successful!"
  fi
fi

# Synchronize assets with remote server if needed
if [ "$USE_REMOTE_LATEX" = true ] && [ "$SYNC_ASSETS" = true ]; then
  echo "Synchronizing assets with remote LaTeX server..."
  rsync -avz -e "ssh -p $REMOTE_LATEX_PORT -i $REMOTE_LATEX_SSH_KEY" ./assets/templates/ "$REMOTE_LATEX_USER@$REMOTE_LATEX_SERVER:/opt/adaptivecv/assets/templates/"
  echo "Assets synchronized successfully!"
fi

# Kill existing processes if running
kill_process() {
  if [ -f ".$1_pid" ]; then
    PID=$(cat ".$1_pid")
    if ps -p "$PID" > /dev/null; then
      echo "Stopping existing $1 process..."
      kill -9 "$PID" || true
    fi
    rm -f ".$1_pid"
  fi
}

kill_process "backend"
kill_process "frontend"
kill_process "proxy"

# Function to start a component
start_component() {
  COMPONENT=$1
  COMMAND=$2
  LOG_FILE="${3:-${COMPONENT}_log.txt}"
  
  echo "Starting $COMPONENT..."
  eval "$COMMAND" > "$LOG_FILE" 2>&1 &
  PID=$!
  echo $PID > ".$COMPONENT_pid"
  echo "$COMPONENT started with PID $PID"
}

# Set environment variables for backend
export ENV="$ENV"
export BACKEND_PORT="$BACKEND_PORT"

# Set remote LaTeX variables if enabled
if [ "$USE_REMOTE_LATEX" = true ]; then
  export REMOTE_LATEX_SERVER="$REMOTE_LATEX_SERVER"
  export REMOTE_LATEX_PORT="$REMOTE_LATEX_PORT"
  export REMOTE_LATEX_USER="$REMOTE_LATEX_USER"
  export REMOTE_LATEX_SSH_KEY="$REMOTE_LATEX_SSH_KEY"
  export USE_REMOTE_LATEX="true"
  
  echo "Remote LaTeX processing enabled:"
  echo "  Server: $REMOTE_LATEX_SERVER"
  echo "  Port: $REMOTE_LATEX_PORT"
  echo "  User: $REMOTE_LATEX_USER"
  echo "  Key: $REMOTE_LATEX_SSH_KEY"
else
  echo "Using local LaTeX processing."
  export USE_REMOTE_LATEX="false"
fi

# Start backend
cd backend
start_component "backend" "python -m app.main" "../backend_log.txt"
cd ..

# Start frontend
cd frontend
start_component "frontend" "npm start" "../frontend_log.txt"
cd ..

# Start proxy for development environment
start_component "proxy" "node frontend/proxy.mjs" "proxy_log.txt"

echo "AdaptiveCV started successfully!"
echo "Backend running on http://localhost:$BACKEND_PORT"
echo "Frontend running on http://localhost:$FRONTEND_PORT"
echo "Application accessible at http://localhost:$PROXY_PORT"

echo "Use Ctrl+C to stop all processes"
echo "Logs are saved to backend_log.txt, frontend_log.txt, and proxy_log.txt"

# Handle graceful shutdown
trap 'kill_process "backend"; kill_process "frontend"; kill_process "proxy"; echo "All processes stopped."; exit 0' SIGINT SIGTERM

# Keep script running
while true; do
  sleep 1
done

---
# filepath: /Users/maciejkasik/Desktop/adaptive-cv/ansible/sync_project.yml
# Ansible playbook to copy AdaptiveCV project files to remote server
# Usage: ansible-playbook sync_project.yml -i inventory.yml

- name: Sync AdaptiveCV project to remote server
  hosts: all  # Can be limited with -l flag when running
  become: yes  # Use sudo privileges on remote server
  vars:
    remote_dir: /opt/adaptivecv
    app_owner: "{{ ansible_user }}"
    app_group: "{{ ansible_user }}"
    file_mode: '0644'
    dir_mode: '0755'
    exec_mode: '0755'
  
  tasks:
    - name: Ensure target directory exists
      file:
        path: "{{ remote_dir }}"
        state: directory
        mode: "{{ dir_mode }}"
        owner: "{{ app_owner }}"
        group: "{{ app_group }}"

    # Backend files
    - name: Copy backend code
      synchronize:
        src: "{{ playbook_dir }}/../backend/"
        dest: "{{ remote_dir }}/backend/"
        delete: yes
        rsync_opts:
          - "--exclude=__pycache__"
          - "--exclude=*.pyc"
          - "--exclude=.env"
          - "--exclude=*.egg-info"
          - "--exclude=.pytest_cache"
      delegate_to: localhost

    - name: Set backend file permissions
      file:
        path: "{{ remote_dir }}/backend"
        state: directory
        mode: "{{ dir_mode }}"
        owner: "{{ app_owner }}"
        group: "{{ app_group }}"
        recurse: yes

    # Frontend files
    - name: Copy frontend code
      synchronize:
        src: "{{ playbook_dir }}/../frontend/"
        dest: "{{ remote_dir }}/frontend/"
        delete: yes
        rsync_opts:
          - "--exclude=node_modules"
          - "--exclude=dist"
          - "--exclude=.env"
          - "--exclude=.cache"
      delegate_to: localhost

    - name: Set frontend file permissions
      file:
        path: "{{ remote_dir }}/frontend"
        state: directory
        mode: "{{ dir_mode }}"
        owner: "{{ app_owner }}"
        group: "{{ app_group }}"
        recurse: yes

    # Assets
    - name: Copy template assets 
      synchronize:
        src: "{{ playbook_dir }}/../assets/templates/"
        dest: "{{ remote_dir }}/assets/templates/"
        delete: yes
      delegate_to: localhost

    - name: Ensure generated directory exists
      file:
        path: "{{ remote_dir }}/assets/generated"
        state: directory
        mode: "{{ dir_mode }}"
        owner: "{{ app_owner }}"
        group: "{{ app_group }}"

    # Configuration and scripts
    - name: Copy configuration files
      copy:
        src: "{{ playbook_dir }}/../{{ item }}"
        dest: "{{ remote_dir }}/{{ item }}"
        mode: "{{ file_mode }}"
        owner: "{{ app_owner }}"
        group: "{{ app_group }}"
      with_items:
        - README.md
        - LICENSE
      ignore_errors: yes

    - name: Copy startup scripts
      copy:
        src: "{{ playbook_dir }}/../{{ item }}"
        dest: "{{ remote_dir }}/{{ item }}"
        mode: "{{ exec_mode }}"
        owner: "{{ app_owner }}"
        group: "{{ app_group }}"
      with_items:
        - start_app.sh
        - ansible/start_app_remote.sh
      ignore_errors: yes

    - name: Create .env examples if needed
      copy:
        src: "{{ playbook_dir }}/../{{ item }}.example"
        dest: "{{ remote_dir }}/{{ item }}"
        mode: "{{ file_mode }}"
        owner: "{{ app_owner }}"
        group: "{{ app_group }}"
        force: no  # Don't overwrite if exists
      with_items:
        - backend/.env
        - frontend/.env
      ignore_errors: yes

    - name: Show success message
      debug:
        msg: "AdaptiveCV project files successfully copied to {{ remote_dir }}"