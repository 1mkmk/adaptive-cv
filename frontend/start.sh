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

echo "Starting AdaptiveCV Frontend Server..."

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed. Please install Node.js and npm."
    exit 1
fi

# Start the React frontend development server
npm run dev