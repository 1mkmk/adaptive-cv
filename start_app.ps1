# AdaptiveCV Startup Script for Windows
# Wersja: 1.0 — z loggingiem, obsługą CTRL+C, status, port checks, auto-kill, ścieżkami absolutnymi i virtualenv

# -----------------------------------
# Base Directories (absolute)
# -----------------------------------
$BASE_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
$BACKEND_DIR = Join-Path $BASE_DIR "backend"
$FRONTEND_DIR = Join-Path $BASE_DIR "frontend"
$PID_DIR = Join-Path $BASE_DIR ".pids"
$LOG_DIR = Join-Path $BASE_DIR "logs"
$VENV_DIR = Join-Path $BASE_DIR ".venv"

# Ports
$BACKEND_PORT = 8000
$FRONTEND_PORT = 5173

# Colors
$GREEN = "Green"
$BLUE = "Cyan"
$YELLOW = "Yellow"
$RED = "Red"
$WHITE = "White"

# -----------------------------------
# Helpers
# -----------------------------------
function Test-CommandExists {
    param($Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Write-Error-Exit {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $RED
    exit 1
}

function Write-Info {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor $BLUE
}

function Write-Warning-Custom {
    param($Message)
    Write-Host "[WARN] $Message" -ForegroundColor $YELLOW
}

function Ensure-Dirs {
    if (-not (Test-Path $PID_DIR)) { New-Item -ItemType Directory -Path $PID_DIR -Force | Out-Null }
    if (-not (Test-Path $LOG_DIR)) { New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null }
}

# -----------------------------------
# Virtual Environment Management
# -----------------------------------
function Ensure-Venv {
    # Check if Python is installed
    if (-not (Test-CommandExists "python")) {
        Write-Error-Exit "Python not found. Please install Python 3.x"
    }
    
    # Check if venv exists, create if not
    if (-not (Test-Path $VENV_DIR)) {
        Write-Info "Creating virtual environment..."
        python -m venv $VENV_DIR
        if ($LASTEXITCODE -ne 0) { Write-Error-Exit "Failed to create virtual environment" }
    }
    
    # Activate the virtual environment
    $activateScript = Join-Path $VENV_DIR "Scripts\Activate.ps1"
    if (-not (Test-Path $activateScript)) { Write-Error-Exit "Activation script not found: $activateScript" }
    
    # PowerShell dot-sourcing to run the activation script in the current scope
    . $activateScript
    
    Write-Info "Using Python: $(Get-Command python | Select-Object -ExpandProperty Source)"
}

function Exit-Venv {
    # Check if deactivate function exists (it's created when a venv is activated)
    if (Get-Command deactivate -ErrorAction SilentlyContinue) {
        Write-Info "Deactivating virtual environment..."
        deactivate
    }
}

# -----------------------------------
# Check Port; prompt kill if busy
# -----------------------------------
function Check-PortFree {
    param($Port)
    
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
                  Where-Object { $_.State -eq "Listen" }
    
    if ($connections) {
        $pids = $connections | ForEach-Object { $_.OwningProcess } | Sort-Object -Unique
        $pidStr = $pids -join ", "
        
        Write-Warning-Custom "Port $Port jest zajęty przez PID: $pidStr"
        $response = Read-Host "Zabić procesy $pidStr używające portu $Port? (y/N)"
        
        if ($response -match "^[Yy]$") {
            foreach ($p in $pids) {
                try {
                    Stop-Process -Id $p -Force
                    Write-Info "Zabito proces PID $p"
                } catch {
                    Write-Warning-Custom "Nie udało się zabić procesu PID $p"
                }
            }
            Start-Sleep -Seconds 1
        } else {
            Write-Error-Exit "Port $Port nadal zajęty. Przerywam."
        }
    }
}

# -----------------------------------
# PID file operations
# -----------------------------------
function Write-Pid {
    param($Name, $ProcessId)
    $ProcessId | Out-File -FilePath (Join-Path $PID_DIR "$Name.pid") -Force
}

function Read-Pid {
    param($Name)
    $pidFile = Join-Path $PID_DIR "$Name.pid"
    if (Test-Path $pidFile) {
        Get-Content -Path $pidFile
    } else {
        ""
    }
}

function Test-ServiceRunning {
    param($Name)
    $pidValue = Read-Pid $Name
    if ($pidValue) {
        try {
            $null = Get-Process -Id $pidValue -ErrorAction Stop
            return $true
        } catch {
            return $false
        }
    }
    return $false
}

# Handle CTRL+C to stop services using PowerShell approach
$PSStopToken = New-Object System.Threading.CancellationTokenSource
try {
    [Console]::TreatControlCAsInput = $true
} catch {
    Write-Warning-Custom "Unable to set TreatControlCAsInput property. CTRL+C handling may not work properly."
}

# -----------------------------------
# Check Dependencies
# -----------------------------------
function Check-NpmAvailable {
    # Check for common Node.js executable paths
    $nodePaths = @(
        # npm.cmd paths
        "C:\Program Files\nodejs\npm.cmd",
        "C:\Program Files (x86)\nodejs\npm.cmd",
        "$env:APPDATA\npm\npm.cmd",
        "$env:ProgramFiles\nodejs\npm.cmd",
        "$env:USERPROFILE\AppData\Roaming\npm\npm.cmd",
        # npm.bat paths
        "C:\Program Files\nodejs\npm.bat",
        "C:\Program Files (x86)\nodejs\npm.bat",
        "$env:APPDATA\npm\npm.bat",
        "$env:ProgramFiles\npm\npm.bat",
        "$env:USERPROFILE\AppData\Roaming\npm\npm.bat",
        # Direct node paths to run npm from node_modules
        "C:\Program Files\nodejs\node.exe",
        "C:\Program Files (x86)\nodejs\node.exe"
    )
    
    # First try npm command
    if (Test-CommandExists "npm") {
        try {
            $npmPath = (Get-Command npm).Source
            Write-Info "Found npm at: $npmPath"
            return "npm"
        } catch {
            Write-Warning-Custom "npm is in PATH but could not be resolved: $_"
        }
    }
    
    # Then try for npm.cmd or npm.bat files
    foreach ($path in $nodePaths) {
        if (Test-Path $path) {
            Write-Info "Found Node.js tool at: $path"
            return $path
        }
    }
    
    # As a last resort, try to find node executable
    if (Test-CommandExists "node") {
        try {
            $nodePath = (Get-Command node).Source
            Write-Info "Found node executable, will use it directly: $nodePath"
            return $nodePath
        } catch {
            Write-Warning-Custom "node is in PATH but could not be resolved"
        }
    }
    
    # If we get here, we couldn't find npm or node
    Write-Error-Exit "Cannot find npm or node. Please install Node.js and ensure it's available in your PATH."
}

# -----------------------------------
# Service Functions
# -----------------------------------
function Start-BackendService {
    Write-Info "Sprawdzam port $BACKEND_PORT..."
    Check-PortFree $BACKEND_PORT
    Write-Info "Uruchamiam backend..."
    
    if (-not (Test-Path $BACKEND_DIR)) {
        Write-Error-Exit "Nie znaleziono katalogu backend"
    }
    
    Push-Location $BACKEND_DIR
    
    # Activate virtual environment
    Ensure-Venv
    
    # Check if uvicorn is installed, if not install dependencies
    $uvicornPath = Join-Path $VENV_DIR "Scripts\uvicorn.exe"
    if (-not (Test-Path $uvicornPath)) {
        Write-Info "Uvicorn not found in virtual environment. Installing dependencies..."
        & python -m pip install --upgrade pip
        & python -m pip install -r requirements.txt
        & python -m pip install uvicorn
        
        if (-not (Test-Path $uvicornPath)) {
            Write-Error-Exit "Failed to install uvicorn. Please run '.\start_app.ps1 start deps' first."
        }
    }
    
    # Start run_server.py in a new process
    $logFile = Join-Path $LOG_DIR "backend.log"
    $errorLogFile = Join-Path $LOG_DIR "backend_error.log"
    $process = Start-Process -FilePath "python" -ArgumentList "run_server.py" -RedirectStandardOutput $logFile -RedirectStandardError $errorLogFile -NoNewWindow -PassThru

    Write-Pid "backend" $process.Id

    Pop-Location
    Write-Info "Backend PID $($process.Id), log: $(Split-Path -Leaf $LOG_DIR)\backend.log, error log: $(Split-Path -Leaf $LOG_DIR)\backend_error.log"
}

function Start-FrontendService {
    Write-Info "Sprawdzam port $FRONTEND_PORT..."
    Check-PortFree $FRONTEND_PORT
    Write-Info "Uruchamiam frontend..."
    
    if (-not (Test-Path $FRONTEND_DIR)) {
        Write-Error-Exit "Nie znaleziono katalogu frontend"
    }
    
    Push-Location $FRONTEND_DIR
    
    # Check for npm and get the correct path
    $npmCmd = Check-NpmAvailable
    Write-Info "Using npm command: $npmCmd"
    
    $logFile = Join-Path $LOG_DIR "frontend.log"
    $errorLogFile = Join-Path $LOG_DIR "frontend_error.log"
    
    # First try using the standard npm command
    try {
        # Check if the npmCmd is a direct node executable
        if ($npmCmd -like "*node.exe") {
            # If we're using node directly, run npm script via node
            $packageJsonPath = Join-Path $FRONTEND_DIR "package.json"
            if (Test-Path $packageJsonPath) {
                Write-Info "Running via node directly using package.json scripts"
                $nodeModulesNpmPath = Join-Path $FRONTEND_DIR "node_modules\npm\bin\npm-cli.js"
                
                if (Test-Path $nodeModulesNpmPath) {
                    $process = Start-Process -FilePath $npmCmd -ArgumentList $nodeModulesNpmPath, "run", "dev", "--", "--port", "$FRONTEND_PORT" -RedirectStandardOutput $logFile -RedirectStandardError $errorLogFile -NoNewWindow -PassThru
                } else {
                    # Use npm that might be in the system node_modules
                    Write-Info "Trying to use command prompt to run npm"
                    $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm run dev -- --port $FRONTEND_PORT" -RedirectStandardOutput $logFile -RedirectStandardError $errorLogFile -NoNewWindow -PassThru
                }
            } else {
                Write-Error-Exit "Package.json not found in $FRONTEND_DIR"
            }
        } else {
            # Use the npmCmd directly
            $process = Start-Process -FilePath $npmCmd -ArgumentList "run", "dev", "--", "--port", "$FRONTEND_PORT" -RedirectStandardOutput $logFile -RedirectStandardError $errorLogFile -NoNewWindow -PassThru
        }
        
        if ($process -and $process.Id) {
            Write-Pid "frontend" $process.Id
            Write-Info "Frontend PID $($process.Id), log: $(Split-Path -Leaf $LOG_DIR)\frontend.log, error log: $(Split-Path -Leaf $LOG_DIR)\frontend_error.log"
        } else {
            Write-Warning-Custom "Frontend process started but couldn't get PID"
        }
    } catch {
        Write-Warning-Custom "First attempt failed: $_"
        
        # Fallback method: Try with cmd.exe
        Write-Info "Trying fallback method with cmd.exe..."
        try {
            $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "cd $FRONTEND_DIR && npm run dev -- --port $FRONTEND_PORT" -RedirectStandardOutput $logFile -RedirectStandardError $errorLogFile -NoNewWindow -PassThru
            
            if ($process -and $process.Id) {
                Write-Pid "frontend" $process.Id
                Write-Info "Frontend started with fallback method. PID $($process.Id)"
            } else {
                Write-Error-Exit "Frontend process started with fallback method but couldn't get PID"
            }
        } catch {
            Write-Error-Exit "Failed to start frontend with fallback method: $_"
        }
    }
    
    Pop-Location
}

function Start-ProxyService {
    Write-Info "Sprawdzam port 3001..."
    Check-PortFree 3001
    Write-Info "Uruchamiam proxy..."
    
    if (-not (Test-Path $FRONTEND_DIR)) {
        Write-Error-Exit "Nie znaleziono katalogu frontend"
    }
    
    Push-Location $FRONTEND_DIR
    
    # Check for nodejs
    if (-not (Test-CommandExists "node")) {
        Write-Error-Exit "Node.js nie został znaleziony. Zainstaluj Node.js i spróbuj ponownie."
    }
    
    $logFile = Join-Path $LOG_DIR "proxy.log"
    $errorLogFile = Join-Path $LOG_DIR "proxy_error.log"
    
    # Start proxy.mjs
    $proxyScript = Join-Path $FRONTEND_DIR "proxy.mjs"
    if (-not (Test-Path $proxyScript)) {
        Write-Error-Exit "Nie znaleziono pliku proxy.mjs w katalogu frontend"
    }
    
    $process = Start-Process -FilePath "node" -ArgumentList $proxyScript -RedirectStandardOutput $logFile -RedirectStandardError $errorLogFile -NoNewWindow -PassThru

    Write-Pid "proxy" $process.Id

    Pop-Location
    Write-Info "Proxy PID $($process.Id), log: $(Split-Path -Leaf $LOG_DIR)\proxy.log, error log: $(Split-Path -Leaf $LOG_DIR)\proxy_error.log"
}

function Generate-TemplatePreviews {
    Write-Info "Generowanie podglądów szablonów..."
    
    Push-Location $BACKEND_DIR
    
    # Activate virtual environment
    Ensure-Venv
    
    # Run the template preview generation script
    $logFile = Join-Path $LOG_DIR "template_previews.log"
    $errorLogFile = Join-Path $LOG_DIR "template_previews_error.log"
    
    Write-Info "Uruchamiam skrypt generowania podglądów szablonów..."
    $process = Start-Process -FilePath "python" -ArgumentList "generate_template_previews.py" -RedirectStandardOutput $logFile -RedirectStandardError $errorLogFile -Wait -NoNewWindow -PassThru
    
    if ($process.ExitCode -ne 0) {
        Write-Warning-Custom "Generowanie podglądów szablonów zakończyło się błędem. Sprawdź log: $(Split-Path -Leaf $LOG_DIR)\template_previews_error.log"
    } else {
        Write-Info "Podglądy szablonów zostały wygenerowane pomyślnie."
    }
    
    Pop-Location
}

function Install-Dependencies {
    Write-Info "Instaluję zależności backendu..."
    Push-Location $BACKEND_DIR
    
    # Activate virtual environment
    Ensure-Venv
    
    # Use venv's pip
    & python -m pip install --upgrade pip
    & python -m pip install -r requirements.txt
    
    Pop-Location
    
    Write-Info "Instaluję zależności frontendu..."
    Push-Location $FRONTEND_DIR
    npm install
    Pop-Location
}

function Stop-Services {
    Write-Info "Zatrzymuję serwisy..."
    
    foreach ($name in @("backend", "frontend", "proxy")) {
        $pidValue = Read-Pid $name
        if ($pidValue) {
            try {
                $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
                if ($process) {
                    Stop-Process -Id $pidValue -Force
                    Write-Info "Zatrzymano $name (PID $pidValue)"
                } else {
                    Write-Warning-Custom "$name nie działa lub PID nieznaleziony"
                }
            } catch {
                Write-Warning-Custom "$name nie działa lub PID nieznaleziony"
            }
            Remove-Item -Path (Join-Path $PID_DIR "$name.pid") -Force -ErrorAction SilentlyContinue
        } else {
            Write-Warning-Custom "$name nie działa lub PID nieznaleziony"
        }
    }
}

function Show-Status {
    Write-Host ""
    
    foreach ($name in @("backend", "frontend", "proxy")) {
        $isRunning = Test-ServiceRunning $name
        $padName = $name.PadRight(8)
        
        if ($isRunning) {
            $pid = Read-Pid $name
            Write-Host "${padName}: " -NoNewline
            Write-Host "RUNNING" -ForegroundColor $GREEN -NoNewline
            Write-Host " (PID $pid)" -ForegroundColor $WHITE
        } else {
            Write-Host "${padName}: " -NoNewline
            Write-Host "STOPPED" -ForegroundColor $RED
        }
    }
    
    Write-Host ""
}

# -----------------------------------
# Main
# -----------------------------------
Ensure-Dirs

$command = if ($args.Count -gt 0) { $args[0] } else { "start" }

switch ($command) {
    "start" {
        if ($args.Count -gt 1 -and $args[1] -eq "deps") {
            Install-Dependencies
        }
        Generate-TemplatePreviews
        Start-BackendService
        Start-FrontendService
        Start-ProxyService
    }
    "stop" {
        Stop-Services
    }
    "status" {
        Show-Status
    }
    "restart" {
        Stop-Services
        Generate-TemplatePreviews
        Start-BackendService
        Start-FrontendService
        Start-ProxyService
    }
    default {
        Write-Host "Użycie: $($MyInvocation.MyCommand.Name) {start|stop|status|restart} [deps]" -ForegroundColor $YELLOW
        exit 1
    }
}

Exit-Venv
