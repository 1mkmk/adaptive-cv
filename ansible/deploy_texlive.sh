#!/bin/bash

# Deploy TeX Live and dependencies to remote server
# This script replaces MiKTeX with TeX Live for better compatibility

set -e

echo "Starting deployment of TeX Live to remote server..."

# Check if ansible is installed
if ! command -v ansible >/dev/null 2>&1; then
  echo "Warning: ansible is not installed. Will use direct SSH method instead."
  USE_SSH=true
else
  USE_SSH=false
fi

# Get server information from inventory file
SERVER=$(grep ansible_host /Users/maciejkasik/Desktop/adaptive-cv/ansible/inventory.yml | head -1 | awk -F: '{print $2}' | tr -d ' ')
PORT=$(grep ansible_port /Users/maciejkasik/Desktop/adaptive-cv/ansible/inventory.yml | head -1 | awk -F: '{print $2}' | tr -d ' ')
USER=$(grep ansible_user /Users/maciejkasik/Desktop/adaptive-cv/ansible/inventory.yml | head -1 | awk -F: '{print $2}' | tr -d ' ')
KEY_FILE=$(grep ansible_ssh_private_key_file /Users/maciejkasik/Desktop/adaptive-cv/ansible/inventory.yml | head -1 | awk -F: '{print $2}' | tr -d ' ')

# Expand ~ in key file path
KEY_FILE=${KEY_FILE/#~/$HOME}

echo "Server: $SERVER"
echo "Port: $PORT"
echo "User: $USER"
echo "SSH Key: $KEY_FILE"

# Check SSH connection
echo "Testing SSH connection..."
ssh -o BatchMode=yes -o ConnectTimeout=5 -p "$PORT" -i "$KEY_FILE" "$USER@$SERVER" exit &>/dev/null
if [ $? -ne 0 ]; then
  echo "Error: Cannot connect to server via SSH. Please check your connection settings."
  exit 1
fi

if [ "$USE_SSH" = false ]; then
  # Update the playbook to use TeX Live instead of MiKTeX
  echo "Creating TeX Live installation playbook..."
  cat > "$(dirname "$0")/texlive_install.yml" << 'EOF'
---
# Ansible playbook to install and configure TeX Live
# Usage: ansible-playbook -i hosts texlive_install.yml

- name: Install and configure TeX Live
  hosts: latex_servers
  become: yes
  
  tasks:
    - name: Update apt cache
      apt:
        update_cache: yes
        cache_valid_time: 3600
    
    # Check if any MiKTeX repository files exist and remove them
    - name: Check if MiKTeX repository files exist
      stat:
        path: /etc/apt/sources.list.d/miktex.list
      register: miktex_repo
      
    - name: Remove existing MiKTeX repository file if it exists
      file:
        path: /etc/apt/sources.list.d/miktex.list
        state: absent
      when: miktex_repo.stat.exists
    
    # Install prerequisites
    - name: Install prerequisites
      apt:
        name:
          - apt-transport-https
          - ca-certificates
          - curl
          - gnupg
          - lsb-release
        state: present
    
    # Install TeX Live packages
    - name: Install TeX Live packages
      apt:
        name:
          - texlive-latex-base
          - texlive-fonts-recommended
          - texlive-fonts-extra
          - texlive-latex-recommended
          - texlive-latex-extra
          - texlive-xetex
          - texlive-pictures
          - texlive-science
          - texlive-pstricks
          - texlive-publishers
          - ghostscript
          - poppler-utils
          - python3-pygments
          - cm-super
          - lmodern
          - fonts-lato
          - fonts-freefont-ttf
          - fonts-liberation
          - fonts-dejavu
        state: present
        update_cache: yes
    
    # Install additional dependencies for PDF processing
    - name: Install additional dependencies and tools
      apt:
        name:
          - imagemagick
          - python3-pip
        state: present
    
    # Configure ImageMagick to allow PDF operations
    - name: Install ImageMagick policy to allow PDF operations
      copy:
        dest: /etc/ImageMagick-6/policy.xml
        content: |
          <?xml version="1.0" encoding="UTF-8"?>
          <!DOCTYPE policymap [
            <!ELEMENT policymap (policy)+>
            <!ATTLIST policymap xmlns CDATA #FIXED ''>
            <!ELEMENT policy EMPTY>
            <!ATTLIST policy xmlns CDATA #FIXED '' domain NMTOKEN #REQUIRED
              name NMTOKEN #IMPLIED pattern CDATA #IMPLIED rights NMTOKEN #IMPLIED
              stealth NMTOKEN #IMPLIED value CDATA #IMPLIED>
          ]>
          <policymap>
            <policy domain="coder" rights="read|write" pattern="PDF" />
            <policy domain="coder" rights="read|write" pattern="LABEL" />
            <policy domain="path" rights="none" pattern="@*" />
            <policy domain="resource" name="memory" value="2GiB"/>
            <policy domain="resource" name="map" value="4GiB"/>
            <policy domain="resource" name="width" value="16KP"/>
            <policy domain="resource" name="height" value="16KP"/>
            <policy domain="resource" name="area" value="128MB"/>
            <policy domain="resource" name="disk" value="8GiB"/>
            <policy domain="resource" name="file" value="768"/>
            <policy domain="resource" name="thread" value="4"/>
            <policy domain="resource" name="throttle" value="0"/>
            <policy domain="resource" name="time" value="3600"/>
          </policymap>
      register: imagemagick_policy
    
    # Install Python packages required for LaTeX processing
    - name: Install Python packages for LaTeX processing
      pip:
        name: "{{ item }}"
        state: present
      with_items:
        - PyLaTeX
        - pypdf
        - pdf2image
        - Pillow
    
    # Setup required directories for AdaptiveCV
    - name: Create directories for AdaptiveCV
      file:
        path: "{{ item }}"
        state: directory
        mode: '0755'
        owner: "{{ ansible_user }}"
        group: "{{ ansible_user }}"
      with_items:
        - /opt/adaptivecv
        - /opt/adaptivecv/assets
        - /opt/adaptivecv/assets/templates
        - /opt/adaptivecv/assets/generated
        - /opt/adaptivecv/assets/generated/latex
        - /opt/adaptivecv/assets/generated/pdf
    
    # Test LaTeX installation by creating a simple document
    - name: Create a test LaTeX file
      copy:
        dest: /tmp/test.tex
        content: |
          \documentclass{article}
          \begin{document}
          Hello, AdaptiveCV!
          \end{document}
    
    - name: Compile the test LaTeX file
      shell: pdflatex -interaction=nonstopmode /tmp/test.tex
      args:
        chdir: /tmp
      register: pdflatex_test
      failed_when: false
      changed_when: false
    
    - name: Verify test LaTeX compilation
      debug:
        msg: "LaTeX installation {{ 'succeeded' if pdflatex_test.rc == 0 else 'failed' }}"
    
    - name: Report LaTeX installation status
      debug:
        msg: "TeX Live installation completed. LaTeX compilation test {{ 'succeeded' if pdflatex_test.rc == 0 else 'failed' }}."
  
  handlers:
    - name: Restart ImageMagick
      service:
        name: imagemagick
        state: restarted
      failed_when: false  # ImageMagick might not have a service, so don't fail
EOF

  # Run the playbook
  echo "Running Ansible playbook to install TeX Live..."
  cd "$(dirname "$0")"
  ansible-playbook -i hosts texlive_install.yml
  RESULT=$?
  
  if [ $RESULT -ne 0 ]; then
    echo "Warning: Ansible playbook failed. Trying direct SSH method..."
    USE_SSH=true
  else
    echo "TeX Live installed successfully via Ansible!"
    exit 0
  fi
fi

if [ "$USE_SSH" = true ]; then
  echo "Installing TeX Live via direct SSH connection..."
  
  # Create installation script
  TMP_SCRIPT=$(mktemp)
  cat > "$TMP_SCRIPT" << 'EOF'
#!/bin/bash
set -e

echo "Updating package lists..."
apt-get update

# Check if any MiKTeX repository files exist and remove them
if [ -f /etc/apt/sources.list.d/miktex.list ]; then
  echo "Removing existing MiKTeX repository file..."
  rm -f /etc/apt/sources.list.d/miktex.list
fi

# Install prerequisites
echo "Installing prerequisites..."
apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Install TeX Live instead of MiKTeX (more reliable on Ubuntu)
echo "Installing TeX Live instead of MiKTeX for better compatibility..."
apt-get install -y texlive-latex-base texlive-fonts-recommended texlive-fonts-extra 
apt-get install -y texlive-latex-recommended texlive-latex-extra texlive-xetex
apt-get install -y texlive-pictures texlive-science texlive-pstricks texlive-publishers
apt-get install -y ghostscript poppler-utils python3-pygments cm-super lmodern
apt-get install -y fonts-lato fonts-freefont-ttf fonts-liberation fonts-dejavu
apt-get install -y imagemagick python3-pip

# Configure ImageMagick to allow PDF operations
echo "Configuring ImageMagick for PDF operations..."
cat > /etc/ImageMagick-6/policy.xml << 'POLICY'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policymap [
  <!ELEMENT policymap (policy)+>
  <!ATTLIST policymap xmlns CDATA #FIXED ''>
  <!ELEMENT policy EMPTY>
  <!ATTLIST policy xmlns CDATA #FIXED '' domain NMTOKEN #REQUIRED
    name NMTOKEN #IMPLIED pattern CDATA #IMPLIED rights NMTOKEN #IMPLIED
    stealth NMTOKEN #IMPLIED value CDATA #IMPLIED>
]>
<policymap>
  <policy domain="coder" rights="read|write" pattern="PDF" />
  <policy domain="coder" rights="read|write" pattern="LABEL" />
  <policy domain="path" rights="none" pattern="@*" />
  <policy domain="resource" name="memory" value="2GiB"/>
  <policy domain="resource" name="map" value="4GiB"/>
  <policy domain="resource" name="width" value="16KP"/>
  <policy domain="resource" name="height" value="16KP"/>
  <policy domain="resource" name="area" value="128MB"/>
  <policy domain="resource" name="disk" value="8GiB"/>
  <policy domain="resource" name="file" value="768"/>
  <policy domain="resource" name="thread" value="4"/>
  <policy domain="resource" name="throttle" value="0"/>
  <policy domain="resource" name="time" value="3600"/>
</policymap>
POLICY

# Install Python packages required for LaTeX processing
echo "Installing Python packages for LaTeX processing..."
pip3 install PyLaTeX pypdf pdf2image Pillow

# Create directories for AdaptiveCV
echo "Creating directories for AdaptiveCV..."
mkdir -p /opt/adaptivecv/assets/templates
mkdir -p /opt/adaptivecv/assets/generated/latex
mkdir -p /opt/adaptivecv/assets/generated/pdf

# Test LaTeX installation
echo "Testing LaTeX installation..."
cd /tmp
cat > test.tex << 'TEX'
\documentclass{article}
\begin{document}
Hello, AdaptiveCV!
\end{document}
TEX

pdflatex -interaction=nonstopmode test.tex
if [ $? -eq 0 ] && [ -f test.pdf ]; then
  echo "LaTeX installation test successful!"
else
  echo "LaTeX installation test failed."
  exit 1
fi

echo "TeX Live installation completed successfully!"
EOF

  # Upload and execute installation script
  chmod +x "$TMP_SCRIPT"
  echo "Uploading installation script to server..."
  scp -P "$PORT" -i "$KEY_FILE" "$TMP_SCRIPT" "$USER@$SERVER:/tmp/install_texlive.sh"
  
  echo "Executing installation script on server..."
  ssh -p "$PORT" -i "$KEY_FILE" "$USER@$SERVER" "chmod +x /tmp/install_texlive.sh && sudo /tmp/install_texlive.sh"
  RESULT=$?
  
  # Clean up temp script
  rm -f "$TMP_SCRIPT"
  
  if [ $RESULT -ne 0 ]; then
    echo "Error: TeX Live installation failed."
    exit 1
  else
    echo "TeX Live installed successfully via SSH!"
  fi
fi

echo "Creating remote directories for assets..."
ssh -p "$PORT" -i "$KEY_FILE" "$USER@$SERVER" "mkdir -p /opt/adaptivecv/assets/templates /opt/adaptivecv/assets/generated/latex /opt/adaptivecv/assets/generated/pdf"

echo "Synchronizing template assets to remote server..."
rsync -avz -e "ssh -p $PORT -i $KEY_FILE" /Users/maciejkasik/Desktop/adaptive-cv/assets/templates/ "$USER@$SERVER:/opt/adaptivecv/assets/templates/"

echo "TeX Live deployment and setup completed successfully!"
