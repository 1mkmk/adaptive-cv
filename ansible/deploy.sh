#!/bin/bash

# Deploy script for Adaptive CV

# Set environment variables from .env file if it exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

# Check for required environment variables
if [ -z "$SERVER_IP" ] || [ -z "$SERVER_USER" ]; then
    echo "Error: SERVER_IP and SERVER_USER environment variables must be set."
    echo "Please create a .env file with these variables or set them in your environment."
    exit 1
fi

if [ -z "$DOMAIN_NAME" ]; then
    echo "Warning: DOMAIN_NAME not set. Using default domain name."
fi

if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo "Warning: Google OAuth credentials not set. Authentication functionality will be limited."
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OpenAI API key not set. AI-powered features will not work."
fi

# Run Ansible playbook
ansible-playbook -i inventory.yml deploy.yml "$@"