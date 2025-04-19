#!/bin/bash

# Print AdaptiveCV ASCII logo
echo "
     _             _   _            _______      __
    /\\      | |           | | (_)          / ____\\ \\    / /
   /  \\   __| | __ _ _ __ | |_ ___   _____| |     \\ \\  / / 
  / /\\ \\ / _\` |/ _\` | '_ \\| __| \\ \\ / / _ \\ |      \\ \\/ /  
 / ____ \\ (_| | (_| | |_) | |_| |\\ V /  __/ |____   \\  /   
/_/    \\_\\__,_|\\__,_| .__/ \\__|_| \\_/ \\___|\\_____|   \\/    
                    | |                                    
                    |_|                                    
"

# Change to the directory containing this script
cd "$(dirname "$0")"

echo "Starting AdaptiveCV Backend Server..."

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "Error: uvicorn is not installed. Please install it using 'pip install uvicorn'."
    exit 1
fi

# Generate template previews if needed
echo "Generating LaTeX template previews..."
python pdf_to_jpg.py

# Start the FastAPI backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000