# PowerShell script to create an admin user for GenePanelCombine
# This script sets up the environment and runs the Python admin user creation script

param(
    [string]$Username,
    [string]$Email,
    [string]$Password,
    [string]$FirstName,
    [string]$LastName,
    [string]$Organization,
    [switch]$NonInteractive
)

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$PythonScript = Join-Path $ScriptDir "db\create_admin_user.py"

Write-Host "GenePanelCombine - Admin User Creation Script" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""

# Check if Python script exists
if (-not (Test-Path $PythonScript)) {
    Write-Host "Error: Python script not found at $PythonScript" -ForegroundColor Red
    exit 1
}

# Change to project root directory
Set-Location $ProjectRoot

# Build Python command arguments
$PythonArgs = @()

if ($Username) { $PythonArgs += @("-u", $Username) }
if ($Email) { $PythonArgs += @("-e", $Email) }
if ($Password) { $PythonArgs += @("-p", $Password) }
if ($FirstName) { $PythonArgs += @("-f", $FirstName) }
if ($LastName) { $PythonArgs += @("-l", $LastName) }
if ($Organization) { $PythonArgs += @("-o", $Organization) }
if ($NonInteractive) { $PythonArgs += @("--non-interactive") }

# Try to determine Python executable
$PythonExecutable = $null
$PythonCommands = @("python", "python3", "py")

foreach ($cmd in $PythonCommands) {
    try {
        $version = & $cmd --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $PythonExecutable = $cmd
            Write-Host "Found Python: $cmd ($version)" -ForegroundColor Cyan
            break
        }
    } catch {
        # Command not found, continue
    }
}

if (-not $PythonExecutable) {
    Write-Host "Error: Python not found. Please install Python or ensure it's in your PATH." -ForegroundColor Red
    exit 1
}

# Run the Python script
Write-Host "Running admin user creation script..." -ForegroundColor Yellow
Write-Host ""

try {
    if ($PythonArgs.Count -gt 0) {
        & $PythonExecutable $PythonScript @PythonArgs
    } else {
        & $PythonExecutable $PythonScript
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Script completed successfully!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Script failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "Error running Python script: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
