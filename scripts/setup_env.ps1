# Load environment variables from .env file
$envFile = ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, 'Process')
            Write-Host "Set $name"
        }
    }
}

# Start Cloud SQL Proxy
Write-Host "Starting Cloud SQL Proxy..."
$env:INSTANCE_CONNECTION_NAME = [Environment]::GetEnvironmentVariable("CLOUD_SQL_CONNECTION_NAME")
$PORT = 5433

# Kill any existing Cloud SQL proxy processes
Get-Process cloud_sql_proxy -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "Starting proxy for $env:INSTANCE_CONNECTION_NAME on port $PORT"
Start-Process -FilePath ".\cloud-sql-proxy.exe" -ArgumentList "-instances=$env:INSTANCE_CONNECTION_NAME=tcp:$PORT" -NoNewWindow
