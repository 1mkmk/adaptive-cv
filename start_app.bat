@echo off
:: Script to start the AdaptiveCV application on Windows
:: Created by Claude Code

:: Configuration
set BACKEND_DIR=.\backend
set FRONTEND_DIR=.\frontend
set BACKEND_PORT=8000
set FRONTEND_PORT=5173

:: Set colors for better output
set GREEN=[92m
set BLUE=[94m
set YELLOW=[93m
set RED=[91m
set RESET=[0m

:: Process command-line arguments
if "%1"=="reset-db" goto reset_database
if "%1"=="reset-and-start" (
    call :reset_database
    goto start_app
)

:start_app
:: Display header
echo %BLUE%
echo   _____     _            _   _            _____   __      __
echo  ^|  __ \   ^| ^|          ^| ^| (_)          / ____^| /\ \    / /
echo  ^| ^|__) ^|__^| ^| __ _ _ __^| ^|_ ___   _____^| ^|     /  \ \  / / 
echo  ^|  ___/ _ \ ^|/ _` ^| '_ \ __^| \ \ / / _ \ ^|    /    \ \/ /  
echo  ^| ^|  ^|  __/ ^| (_^| ^| ^|_) ^| ^|_^| ^|\ V /  __/ ^|___^|    /\  /   
echo  ^|_^|   \___^|_^|\__,_^| .__/ \__^|_^| \_/ \___\_____^|   /  \/    
echo                     ^| ^|                                      
echo                     ^|_^|                                      
echo %RESET%

:: Check prerequisites
echo %BLUE%Checking prerequisites...%RESET%

:: Check for Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %RED%Python is not installed or not in PATH. Please install Python 3 to continue.%RESET%
    exit /b 1
) else (
    echo %GREEN%✓ Python is installed%RESET%
)

:: Check for Node.js
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %RED%Node.js is not installed or not in PATH. Please install Node.js to continue.%RESET%
    exit /b 1
) else (
    echo %GREEN%✓ Node.js is installed%RESET%
)

:: Check for npm
npm --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %RED%npm is not installed or not in PATH. Please install npm to continue.%RESET%
    exit /b 1
) else (
    echo %GREEN%✓ npm is installed%RESET%
)

:: Ask if user wants to install dependencies
echo %YELLOW%Do you want to install dependencies? (y/n)%RESET%
set /p INSTALL_DEPS=

if /i "%INSTALL_DEPS%"=="y" (
    :: Install backend dependencies
    echo %BLUE%Installing backend dependencies...%RESET%
    cd %BACKEND_DIR% || (
        echo %RED%Backend directory not found%RESET%
        exit /b 1
    )
    pip install -r requirements.txt
    
    :: Check if .env file exists, if not create it
    if not exist .env (
        echo %YELLOW%Creating .env file...%RESET%
        (
            echo # Environment variables for Adaptive CV backend
            echo # Replace with your actual API keys in production
            echo.
            echo # OpenAI API Key for CV generation
            echo OPENAI_API_KEY="your-openai-api-key"
            echo.
            echo # Database settings
            echo DATABASE_URL="sqlite:///adaptive_cv.db"
            echo.
            echo # Server settings
            echo HOST="0.0.0.0"
            echo PORT=8000
            echo DEBUG=true
        ) > .env
        echo %YELLOW%Please edit the .env file in the backend directory to add your OpenAI API key%RESET%
    )
    
    cd ..
    echo %GREEN%Backend dependencies installed%RESET%
    
    :: Install frontend dependencies
    echo %BLUE%Installing frontend dependencies...%RESET%
    cd %FRONTEND_DIR% || (
        echo %RED%Frontend directory not found%RESET%
        exit /b 1
    )
    npm install
    
    :: Check if .env file exists, if not create it
    if not exist .env (
        echo %YELLOW%Creating .env file...%RESET%
        (
            echo # Frontend environment variables
            echo VITE_API_URL=http://localhost:8000
        ) > .env
    )
    
    cd ..
    echo %GREEN%Frontend dependencies installed%RESET%
)

:: Start the backend server
echo %BLUE%Starting backend server...%RESET%
start "AdaptiveCV Backend" cmd /c "cd %BACKEND_DIR% && python -m uvicorn app.main:app --reload --port %BACKEND_PORT% && pause"
echo %GREEN%Backend server starting at http://localhost:%BACKEND_PORT%%RESET%

:: Start the frontend server
echo %BLUE%Starting frontend server...%RESET%
start "AdaptiveCV Frontend" cmd /c "cd %FRONTEND_DIR% && npm run dev -- --port %FRONTEND_PORT% && pause"
echo %GREEN%Frontend server starting at http://localhost:%FRONTEND_PORT%%RESET%

echo %GREEN%AdaptiveCV is now running!%RESET%
echo %BLUE%Backend server: %RESET%http://localhost:%BACKEND_PORT%
echo %BLUE%Frontend application: %RESET%http://localhost:%FRONTEND_PORT%
echo %YELLOW%Don't forget to set your OpenAI API key in backend/.env%RESET%
echo.
echo %BLUE%Available commands:%RESET%
echo %BLUE%- To reset the database:%RESET% start_app.bat reset-db
echo %BLUE%- To reset the database and start the app:%RESET% start_app.bat reset-and-start

goto :eof

:reset_database
echo %BLUE%Resetting database...%RESET%
cd %BACKEND_DIR% || (
    echo %RED%Backend directory not found%RESET%
    exit /b 1
)
python reset_db_windows.py
cd ..
echo %GREEN%Database reset completed%RESET%
if "%1"=="reset-db" exit /b 0
goto :eof

:: End of script