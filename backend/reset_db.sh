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

echo "Resetting database..."

# Check if Python can be called directly
if command -v python3 &> /dev/null; then
    python3 reset_db.py
elif command -v python &> /dev/null; then
    python reset_db.py
else
    echo "Error: Python not found. Please install Python 3."
    exit 1
fi

echo "Database reset completed"