# PowerShell script to create or manage admin users for PanelMerge
# This script sets up the environment and runs the Python admin user management script

param(
    [string]$Username,
    [string]$Email,
    [string]$Password,
    [string]$FirstName,
    [string]$LastName,
    [string]$Organization,
    [switch]$ChangePassword,
    [switch]$NonInteractive
)

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$PythonScript = Join-Path $ScriptDir "db\create_admin_user.py"

Write-Host "PanelMerge - Admin User Management Script" -ForegroundColor Green
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

if ($ChangePassword) { 
    $PythonArgs += @("--change-password") 
    Write-Host "Mode: Change Password" -ForegroundColor Cyan
} else {
    Write-Host "Mode: Create New Admin User" -ForegroundColor Cyan
}
Write-Host ""

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
Write-Host "Running admin user management script..." -ForegroundColor Yellow
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
