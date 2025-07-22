# Kill any existing Cloud SQL proxy processes
Get-Process cloud_sql_proxy -ErrorAction SilentlyContinue | Stop-Process -Force

$env:GOOGLE_PROJECT_ID = "gene-panel-combine"
$env:INSTANCE_CONNECTION_NAME = "gene-panel-combine:europe-north1:gene-panel-user-db"
$PORT = 5433  # Use a different port to avoid conflicts

Write-Host "Starting Cloud SQL Auth Proxy on port $PORT..."
Write-Host "Press Ctrl+C to stop the proxy"

# Function to find an available port
function Find-AvailablePort {
    param(
        [int]$StartPort = 5433
    )
    $port = $StartPort
    while ($port -lt $StartPort + 100) {
        try {
            $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Parse("127.0.0.1"), $port)
            $listener.Start()
            $listener.Stop()
            return $port
        }
        catch {
            $port++
        }
    }
    throw "No available ports found in range $StartPort to $($StartPort + 100)"
}

# Try to find an available port
$PORT = Find-AvailablePort -StartPort 5433
Write-Host "Found available port: $PORT"

# Check if we already have cloud-sql-proxy.exe
if (-not (Test-Path "cloud-sql-proxy.exe")) {
    Write-Host "Downloading Cloud SQL Auth Proxy..."
    $proxyUrl = "https://dl.google.com/cloudsql/cloud_sql_proxy_x64.exe"
    Invoke-WebRequest -Uri $proxyUrl -OutFile "cloud-sql-proxy.exe"
}

try {    Write-Host "Starting proxy for $env:INSTANCE_CONNECTION_NAME on port $PORT"
    # Use the v1 syntax since we're using the v1 proxy
    .\cloud-sql-proxy.exe -instances="$env:INSTANCE_CONNECTION_NAME=tcp:$PORT"
}
catch {
    Write-Error "Failed to start Cloud SQL proxy: $_"
    exit 1
}
finally {
    Write-Host "Cleaning up..."
    Get-Process cloud_sql_proxy -ErrorAction SilentlyContinue | Stop-Process -Force
}
