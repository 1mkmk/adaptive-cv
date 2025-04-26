#!/bin/bash

# Script to deploy MiKTeX to the server
# Usage: ./deploy_miktex.sh

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Server information
SERVER="karol152.mikrus.xyz"
PORT="10152"
USER="root"
SSH_KEY="~/.ssh/id_rsa"

# Header
echo -e "${BLUE}"
echo "  _____     _            _   _            _____   __      __"
echo " |  __ \   | |          | | (_)          / ____| /\ \    / /"
echo " | |__) |__| | __ _ _ __| |_ ___   _____| |     /  \ \  / / "
echo " |  ___/ _ \ |/ _\` | '_ \ __| \ \ / / _ \ |    /    \ \/ /  "
echo " | |  |  __/ | (_| | |_) | |_| |\ V /  __/ |___|    /\  /   "
echo " |_|   \___|_|\__,_| .__/ \__|_| \_/ \___\_____|   /  \/    "
echo "                    | |                                      "
echo "                    |_|                                      "
echo "                 MiKTeX Deployment                           "
echo -e "${NC}"

# Check if ansible is installed
if ! command -v ansible &> /dev/null; then
  echo -e "${RED}Ansible is not installed. Please install Ansible to continue.${NC}"
  exit 1
fi

# Check if ansible-playbook is installed
if ! command -v ansible-playbook &> /dev/null; then
  echo -e "${RED}ansible-playbook command not found. Please install Ansible properly.${NC}"
  exit 1
fi

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa ]; then
  echo -e "${RED}SSH key not found at ~/.ssh/id_rsa${NC}"
  echo -e "${YELLOW}Please make sure your SSH key is properly set up.${NC}"
  exit 1
fi

# Check if the hosts file exists
if [ ! -f hosts ]; then
  echo -e "${RED}hosts file not found.${NC}"
  echo -e "${YELLOW}Make sure you are in the ansible directory.${NC}"
  exit 1
fi

# Check connectivity to the server
echo -e "${BLUE}Checking connectivity to the server...${NC}"
if ! ansible all -i hosts -m ping; then
  echo -e "${RED}Failed to connect to the server using Ansible.${NC}"
  echo -e "${YELLOW}Trying direct SSH connection...${NC}"
  
  # Try direct SSH connection
  if ! ssh -i "$SSH_KEY" -p "$PORT" "$USER@$SERVER" "echo Connected successfully" &>/dev/null; then
    echo -e "${RED}Failed to connect to the server via SSH.${NC}"
    echo -e "${YELLOW}Please check your SSH key and server settings.${NC}"
    exit 1
  else
    echo -e "${GREEN}Direct SSH connection successful!${NC}"
  fi
fi

echo -e "${GREEN}Successfully connected to the server.${NC}"

# Ask user if they want to install MiKTeX directly or use Ansible playbook
echo -e "${YELLOW}Choose installation method:${NC}"
echo -e "1) ${GREEN}Use Ansible playbook (recommended for Ubuntu/Debian systems)${NC}"
echo -e "2) ${GREEN}Direct SSH installation (useful for other Linux distributions)${NC}"
echo -e "Select option (1/2): \c"
read INSTALL_METHOD

# Default to option 1 if no input is provided
if [ -z "$INSTALL_METHOD" ]; then
  INSTALL_METHOD="1"
  echo "No option selected, defaulting to Ansible playbook installation."
fi

if [ "$INSTALL_METHOD" == "1" ]; then
  # Run the MiKTeX installation playbook
  echo -e "${BLUE}Starting MiKTeX installation via Ansible...${NC}"
  ansible-playbook -i hosts miktex_install.yml -v
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}MiKTeX installation via Ansible completed successfully!${NC}"
    INSTALL_COMPLETED="true"
  else
    echo -e "${RED}MiKTeX installation via Ansible failed. Please check the logs.${NC}"
    echo -e "${YELLOW}Would you like to try direct SSH installation instead? (y/n)${NC}"
    read -p "" TRY_DIRECT
    
    if [ "$TRY_DIRECT" != "y" ]; then
      INSTALL_COMPLETED="false"
    else
      INSTALL_METHOD="2"
    fi
  fi
fi

if [ "$INSTALL_METHOD" == "2" ]; then
  echo -e "${BLUE}Starting MiKTeX installation via direct SSH...${NC}"
  
  # Determine OS
  OS_INFO=$(ssh -i "$SSH_KEY" -p "$PORT" "$USER@$SERVER" "cat /etc/os-release | grep -E 'ID=|VERSION_ID='")
  
  if echo "$OS_INFO" | grep -q "ubuntu"; then
    DISTRO="ubuntu"
    VERSION=$(echo "$OS_INFO" | grep VERSION_ID | cut -d= -f2 | tr -d '"')
    
    if [[ "$VERSION" == "18.04" ]]; then
      CODENAME="bionic"
    elif [[ "$VERSION" == "20.04" ]]; then
      CODENAME="focal"
    else
      CODENAME="focal"  # Default to focal for newer versions
    fi
  elif echo "$OS_INFO" | grep -q "debian"; then
    DISTRO="debian"
    VERSION=$(echo "$OS_INFO" | grep VERSION_ID | cut -d= -f2 | tr -d '"')
    
    if [[ "$VERSION" == "9" ]]; then
      CODENAME="stretch"
    elif [[ "$VERSION" == "10" ]]; then
      CODENAME="buster"
    else
      CODENAME="bullseye"  # Default to bullseye for newer versions
    fi
  else
    echo -e "${RED}Unsupported distribution for direct installation.${NC}"
    echo -e "${YELLOW}Detected OS info:${NC}"
    echo "$OS_INFO"
    exit 1
  fi
  
  echo -e "${BLUE}Detected ${DISTRO} ${VERSION} (${CODENAME})${NC}"
  
  # Install MiKTeX via SSH commands
  echo -e "${BLUE}Installing MiKTeX...${NC}"
  
  ssh -i "$SSH_KEY" -p "$PORT" "$USER@$SERVER" "
    # Remove any existing malformed repo files
    if [ -f /etc/apt/sources.list.d/miktex.list ]; then
      echo "Removing existing MiKTeX repository file..."
      rm -f /etc/apt/sources.list.d/miktex.list
    fi
    
    # Install prerequisites
    apt-get update || true  # Continue even if there are some errors
    apt-get install -y apt-transport-https ca-certificates curl gnupg

    # Install TeX Live instead of MiKTeX (more reliable on Ubuntu)
    echo "Installing TeX Live instead of MiKTeX for better compatibility..."
    apt-get install -y texlive-latex-base texlive-fonts-recommended texlive-fonts-extra 
    apt-get install -y texlive-latex-recommended texlive-latex-extra texlive-xetex
    apt-get install -y texlive-pictures texlive-science texlive-pstricks texlive-publishers
    apt-get install -y ghostscript poppler-utils python3-pygments cm-super lmodern
    apt-get install -y fonts-lato fonts-freefont-ttf fonts-liberation fonts-dejavu
    
    # Install additional packages
    apt-get install -y ghostscript poppler-utils python3-pip python3-pygments imagemagick fonts-lato fonts-freefont-ttf fonts-liberation fonts-dejavu cm-super lmodern
    
    # Setup MiKTeX (shared installation)
    miktexsetup --shared=yes finish
    
    # Enable auto-installation of packages
    initexmf --admin --set-config-value [MPM]AutoInstall=1
    
    # Create directories for AdaptiveCV
    mkdir -p /opt/adaptivecv/assets/templates
    mkdir -p /opt/adaptivecv/assets/generated/latex
    mkdir -p /opt/adaptivecv/assets/generated/pdf
    chmod -R 755 /opt/adaptivecv
    
    # Install Python packages
    pip3 install PyLaTeX pypdf pdf2image Pillow
    
    # Create test LaTeX file
    echo '\\documentclass{article}
\\begin{document}
Hello, AdaptiveCV!
\\end{document}' > /tmp/test.tex
    
    # Try to compile test file
    cd /tmp && pdflatex -interaction=nonstopmode test.tex
    
    # Check result
    if [ -f /tmp/test.pdf ]; then
      echo 'LaTeX test compilation successful!'
    else
      echo 'LaTeX test compilation failed!'
    fi
  "
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}MiKTeX installation via direct SSH completed!${NC}"
    INSTALL_COMPLETED="true"
  else
    echo -e "${RED}MiKTeX installation failed. Please check the logs above for errors.${NC}"
    INSTALL_COMPLETED="false"
  fi
fi

# Only proceed with assets if MiKTeX was installed successfully
if [ "$INSTALL_COMPLETED" == "true" ]; then
  # Create assets directory
  echo -e "${BLUE}Setting up assets directory...${NC}"
  ssh -i "$SSH_KEY" -p "$PORT" "$USER@$SERVER" "mkdir -p /opt/adaptivecv/assets"

  # Upload assets
  echo -e "${BLUE}Syncing assets to remote server...${NC}"
  rsync -avz -e "ssh -i $SSH_KEY -p $PORT" ../assets/ "$USER@$SERVER:/opt/adaptivecv/assets/"

  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Assets synced successfully!${NC}"
  else
    echo -e "${RED}Failed to sync assets.${NC}"
    echo -e "${YELLOW}Please check your SSH connection and try again.${NC}"
  fi

  echo -e "${GREEN}MiKTeX deployment completed successfully!${NC}"
  echo -e "${YELLOW}MiKTeX is now installed and configured on your server.${NC}"
  echo -e "${BLUE}You can now use the remote server for LaTeX document generation.${NC}"
else
  echo -e "${RED}MiKTeX installation was not completed. Skipping asset sync.${NC}"
  echo -e "${YELLOW}Please fix the installation issues before trying again.${NC}"
  exit 1
fi