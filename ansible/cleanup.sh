#!/bin/bash

# Cleanup script for AdaptiveCV deployments
# This script removes deployed resources and configuration

set -e

echo "Starting cleanup of AdaptiveCV resources..."

# Check if we have root access
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

# Stop and remove Docker containers
if command -v docker >/dev/null 2>&1; then
  echo "Stopping and removing Docker containers..."
  docker-compose -f /opt/adaptivecv/docker-compose.yml down 2>/dev/null || true
  docker rm -f $(docker ps -a | grep adaptivecv | awk '{print $1}') 2>/dev/null || true
  echo "Removing Docker images..."
  docker rmi $(docker images | grep adaptivecv | awk '{print $3}') 2>/dev/null || true
fi

# Remove Nginx configuration
echo "Removing Nginx configuration..."
rm -f /etc/nginx/sites-available/adaptivecv
rm -f /etc/nginx/sites-enabled/adaptivecv
systemctl restart nginx

# Remove application files
echo "Removing application files..."
rm -rf /opt/adaptivecv

echo "Cleanup completed successfully."
