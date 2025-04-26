#!/bin/bash
# filepath: /Users/maciejkasik/Desktop/adaptive-cv/fix_dependencies.sh

echo "Installing missing tenacity package..."
pip install tenacity

# Update requirements.txt if tenacity isn't already there
if ! grep -q "tenacity" requirements.txt; then
  echo "tenacity" >> requirements.txt
  echo "Added tenacity to requirements.txt"
fi

echo "Restarting application..."
cd ..
./start_app.sh restart