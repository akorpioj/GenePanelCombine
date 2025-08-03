# Google Cloud PostgreSQL Database Setup Guide

## Overview

This guide provides step-by-step instructions for setting up and configuring the Google Cloud PostgreSQL database for the GenePanelCombine application.

## Current Database Configuration

- **Instance Name**: `gene-panel-user-db`
- **Database Version**: PostgreSQL 14
- **Location**: `europe-north1-c`
- **Tier**: `db-f1-micro`
- **Public IP**: `35.228.157.4`
- **Database Name**: `genepanel-userdb`

## Prerequisites

1. **Google Cloud SDK** installed and configured
2. **gcloud CLI** authenticated with appropriate permissions
3. **PostgreSQL client** (psql) installed locally
4. **Project permissions**: Cloud SQL Admin or Editor role

## Initial Setup (If Creating New Instance)

### 1. Create Cloud SQL Instance

```bash
# Create PostgreSQL instance
gcloud sql instances create gene-panel-user-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=europe-north1 \
    --zone=europe-north1-c \
    --storage-type=SSD \
    --storage-size=10GB \
    --storage-auto-increase \
    --backup-start-time=03:00 \
    --backup-location=europe-north1 \
    --enable-bin-log \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=04 \
    --maintenance-release-channel=production
```

### 2. Create Database

```bash
# Create the application database
gcloud sql databases create genepanel-userdb \
    --instance=gene-panel-user-db \
    --charset=UTF8 \
    --collation=en_US.UTF8
```

## Database User Management

### 1. Set Root Password

```bash
# Set a secure password for the postgres user
gcloud sql users set-password postgres \
    --instance=gene-panel-user-db \
    --password="YOUR_SECURE_ROOT_PASSWORD"
```

### 2. Create Application User

```bash
# Create a dedicated user for the application
gcloud sql users create genepanel_app \
    --instance=gene-panel-user-db \
    --password="YOUR_SECURE_APP_PASSWORD"
```

### 3. Grant Permissions

```bash
# Connect to the database to grant permissions
gcloud sql connect gene-panel-user-db --user=postgres --database=genepanel-userdb
```

Then run these SQL commands:

```sql
-- Grant all privileges on the database to the app user
GRANT ALL PRIVILEGES ON DATABASE "genepanel-userdb" TO genepanel_app;

-- Grant permissions on the public schema
GRANT ALL ON SCHEMA public TO genepanel_app;

-- Grant permissions on all tables (current and future)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO genepanel_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO genepanel_app;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO genepanel_app;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO genepanel_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO genepanel_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO genepanel_app;

-- Exit
\q
```

## Security Configuration

### 1. Configure Authorized Networks

```bash
# Add your local IP for development (replace with your actual IP)
gcloud sql instances patch gene-panel-user-db \
    --authorized-networks=YOUR_LOCAL_IP/32

# For production, add your application server IPs
gcloud sql instances patch gene-panel-user-db \
    --authorized-networks=YOUR_PRODUCTION_SERVER_IP/32
```

### 2. Enable SSL

```bash
# Require SSL connections
gcloud sql instances patch gene-panel-user-db \
    --require-ssl
```

### 3. Download SSL Certificates

```bash
# Download server certificate
gcloud sql ssl-certs describe server-ca-cert \
    --instance=gene-panel-user-db \
    --format="value(cert)" > server-ca.pem

# Create client certificate (optional but recommended)
gcloud sql ssl-certs create client-cert client-key.pem \
    --instance=gene-panel-user-db

# Download client certificate
gcloud sql ssl-certs describe client-cert \
    --instance=gene-panel-user-db \
    --format="value(cert)" > client-cert.pem
```

## Connection Configuration

### 1. Environment Variables

Create or update your `.env` file:

```bash
# Google Cloud PostgreSQL Configuration
DATABASE_URL=postgresql://genepanel_app:YOUR_SECURE_APP_PASSWORD@35.228.157.4:5432/genepanel-userdb?sslmode=require
DB_HOST=35.228.157.4
DB_PORT=5432
DB_NAME=genepanel-userdb
DB_USER=genepanel_app
DB_PASSWORD=YOUR_SECURE_APP_PASSWORD
DB_SSLMODE=require

# For SSL certificate authentication (if using client certificates)
DB_SSLCERT=client-cert.pem
DB_SSLKEY=client-key.pem
DB_SSLROOTCERT=server-ca.pem
```

### 2. Application Configuration

Update your `app/config_settings.py`:

```python
import os
from urllib.parse import urlparse

class Config:
    # ... existing configuration ...
    
    # Google Cloud PostgreSQL Configuration
    if os.getenv('GOOGLE_CLOUD_SQL'):
        # Cloud SQL configuration
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    else:
        # Local development fallback
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    
    # SSL Configuration for production
    if os.getenv('DB_SSLMODE'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'connect_args': {
                'sslmode': os.getenv('DB_SSLMODE', 'require'),
                'sslcert': os.getenv('DB_SSLCERT'),
                'sslkey': os.getenv('DB_SSLKEY'),
                'sslrootcert': os.getenv('DB_SSLROOTCERT'),
            }
        }
```

## Database Initialization

### 1. Run Database Migrations

```bash
# Set environment variable to use Cloud SQL
export GOOGLE_CLOUD_SQL=true

# Initialize the database
python db_init.py

# Or if you have Flask-Migrate set up
flask db upgrade
```

### 2. Verify Connection

```bash
# Test connection using psql
psql "postgresql://genepanel_app:YOUR_PASSWORD@35.228.157.4:5432/genepanel-userdb?sslmode=require"

# Test from Python
python -c "
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    print('Database connection successful!')
    print(f'Database URL: {app.config[\"SQLALCHEMY_DATABASE_URI\"]}')
"
```

## Cloud SQL Proxy (Alternative Connection Method)

For enhanced security and simplified connection management:

### 1. Download Cloud SQL Proxy

```bash
# Download the proxy (already exists in your project)
# The cloud-sql-proxy.exe is already in your project root

# Or download latest version
curl -o cloud-sql-proxy.exe https://dl.google.com/cloudsql/cloud_sql_proxy_x64.exe
```

### 2. Start Cloud SQL Proxy

```bash
# Start the proxy (replace PROJECT_ID with your actual project ID)
./cloud-sql-proxy.exe PROJECT_ID:europe-north1:gene-panel-user-db
```

### 3. Connect via Proxy

When using the proxy, connect to `localhost:5432`:

```bash
# Environment variables for proxy connection
DATABASE_URL=postgresql://genepanel_app:YOUR_PASSWORD@localhost:5432/genepanel-userdb
DB_HOST=localhost
DB_PORT=5432
```

## Monitoring and Maintenance

### 1. Check Instance Status

```bash
# List instances
gcloud sql instances list

# Get detailed instance info
gcloud sql instances describe gene-panel-user-db

# Check operations
gcloud sql operations list --instance=gene-panel-user-db
```

### 2. Database Monitoring

```bash
# Check database connections
gcloud sql instances describe gene-panel-user-db \
    --format="value(stats.databaseConnections)"

# Monitor performance
gcloud logging read "resource.type=cloudsql_database AND resource.labels.database_id=PROJECT_ID:gene-panel-user-db"
```

### 3. Backup Management

```bash
# List backups
gcloud sql backups list --instance=gene-panel-user-db

# Create manual backup
gcloud sql backups create --instance=gene-panel-user-db \
    --description="Manual backup before major update"

# Restore from backup (if needed)
gcloud sql backups restore BACKUP_ID \
    --restore-instance=gene-panel-user-db
```

## Performance Optimization

### 1. Instance Scaling

```bash
# Scale up instance tier
gcloud sql instances patch gene-panel-user-db \
    --tier=db-custom-2-7680

# Increase storage
gcloud sql instances patch gene-panel-user-db \
    --storage-size=20GB
```

### 2. Database Optimization

Connect to the database and run:

```sql
-- Create indexes for better performance
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_users_username ON users(username);
CREATE INDEX CONCURRENTLY idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX CONCURRENTLY idx_panel_downloads_user_id ON panel_downloads(user_id);
CREATE INDEX CONCURRENTLY idx_visits_timestamp ON visits(timestamp);

-- Analyze tables for query optimization
ANALYZE;

-- Check for unused indexes
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE tablename IN ('users', 'audit_logs', 'panel_downloads', 'visits');
```

## Troubleshooting

### Common Issues

1. **Authentication Conflicts with Google Cloud Storage**
   ```
   google.auth.exceptions.DefaultCredentialsError: 403 NOT_AUTHORIZED
   Failed to initialize Cloud SQL connector: File gcs-service-account-key.json was not found
   ```
   **Root Cause**: Google Cloud libraries automatically use `GOOGLE_APPLICATION_CREDENTIALS` for all services. If the service account only has storage permissions, Cloud SQL connections will fail.
   
   **Solutions**:
   - **Development**: Comment out `GOOGLE_APPLICATION_CREDENTIALS` in `.env` to use user authentication
   - **Production**: Create service account with both Cloud SQL and Storage permissions
   - **Verify user has both roles**: `gcloud projects get-iam-policy PROJECT_ID --filter="bindings.members:user:YOUR_EMAIL" --format="value(bindings.role)" | grep -E "(sql|storage)"`

2. **Connection Timeout**
   ```bash
   # Check firewall rules
   gcloud compute firewall-rules list --filter="direction:INGRESS AND allowed.ports:5432"
   ```

3. **SSL Certificate Issues**
   ```bash
   # Regenerate SSL certificates
   gcloud sql ssl-certs delete client-cert --instance=gene-panel-user-db
   gcloud sql ssl-certs create client-cert client-key.pem --instance=gene-panel-user-db
   ```

4. **Permission Denied**
   ```sql
   -- Re-grant permissions
   GRANT ALL PRIVILEGES ON DATABASE "genepanel-userdb" TO genepanel_app;
   ```

### Useful Commands

```bash
# Check instance logs
gcloud logging read "resource.type=cloudsql_database" --limit=50

# Test connection
gcloud sql connect gene-panel-user-db --user=genepanel_app --database=genepanel-userdb

# Export database
gcloud sql export sql gene-panel-user-db gs://YOUR_BUCKET/backup.sql \
    --database=genepanel-userdb

# Import database
gcloud sql import sql gene-panel-user-db gs://YOUR_BUCKET/backup.sql \
    --database=genepanel-userdb
```

## Security Best Practices

1. **Regular Password Updates**: Rotate database passwords quarterly
2. **Network Security**: Limit authorized networks to essential IPs only
3. **SSL/TLS**: Always use encrypted connections
4. **Backup Security**: Encrypt backups and limit access
5. **Monitoring**: Set up alerts for unusual database activity
6. **Access Control**: Use principle of least privilege for database users

## Cost Optimization

1. **Right-sizing**: Monitor CPU and memory usage to optimize instance tier
2. **Storage**: Use automatic storage increase to avoid over-provisioning
3. **Backups**: Configure retention policies to manage backup costs
4. **Scheduling**: Use maintenance windows during low-traffic periods

---

This setup guide ensures a secure, scalable, and maintainable PostgreSQL database configuration for the GenePanelCombine application.
