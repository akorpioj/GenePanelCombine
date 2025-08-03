# PanelMerge Configuration Guide

This guide provides comprehensive configuration instructions for PanelMerge v1.4, covering environment variables, security settings, database configuration, and deployment options.

## 📋 Table of Contents

1. [Environment Variables](#environment-variables)
2. [Database Configuration](#database-configuration)
3. [Security Configuration](#security-configuration)
4. [Redis Configuration](#redis-configuration)
5. [Storage Configuration](#storage-configuration)
6. [API Configuration](#api-configuration)
7. [Deployment Configurations](#deployment-configurations)
8. [Development vs Production](#development-vs-production)
9. [Troubleshooting](#troubleshooting)

---

## 🔧 Environment Variables

### Required Variables

Create a `.env` file in the project root with the following variables:

```bash
# Flask Configuration
FLASK_ENV=production                    # Options: development, production
SECRET_KEY=your-super-secret-key-here   # Must be 32+ characters, cryptographically secure
DEBUG=False                             # Set to True only in development

# Database Configuration
WITHOUT_DB=False                        # Set to True to run without database
DATABASE_URL=postgresql://user:pass@host:port/dbname  # Full database connection string
SQLITE_DB_PATH=instance/gene_panel.db   # Path for SQLite database (development only)
GOOGLE_CLOUD_SQL=True                   # Set to True for Google Cloud SQL (production)

# Security Configuration
ENCRYPTION_KEY=your-encryption-key-here  # 32-byte key for data encryption
SESSION_TIMEOUT=3600                     # Session timeout in seconds (1 hour default)
MAX_LOGIN_ATTEMPTS=5                     # Maximum failed login attempts before lockout
LOCKOUT_DURATION=900                     # Account lockout duration in seconds (15 minutes)

# Redis Configuration
REDIS_URL=redis://localhost:6379/0       # Redis connection string
REDIS_PASSWORD=your-redis-password        # Redis password (if required)
REDIS_SSL=False                          # Set to True for SSL connections

# API Rate Limiting
RATE_LIMIT_PER_MINUTE=60                 # API requests per minute per IP
RATE_LIMIT_PER_HOUR=1000                 # API requests per hour per IP
RATE_LIMIT_PER_DAY=10000                 # API requests per day per IP

# File Upload Configuration
MAX_CONTENT_LENGTH=16777216              # Maximum file size in bytes (16MB default)
UPLOAD_FOLDER=instance/uploads           # Directory for uploaded files
ALLOWED_EXTENSIONS=csv,tsv,xls,xlsx      # Comma-separated allowed file extensions

# External API Configuration
PANELAPP_UK_BASE_URL=https://panelapp.genomicsengland.co.uk/api/v1
PANELAPP_AUS_BASE_URL=https://panelapp.agha.umccr.org/api/v1
API_TIMEOUT=30                           # API request timeout in seconds
API_RETRY_ATTEMPTS=3                     # Number of retry attempts for failed API calls

# Logging Configuration
LOG_LEVEL=INFO                           # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/panelmerge.log            # Log file path
MAX_LOG_SIZE=10485760                    # Maximum log file size in bytes (10MB)
LOG_BACKUP_COUNT=5                       # Number of log backup files to keep

# Audit Configuration
AUDIT_RETENTION_DAYS=365                 # Days to retain audit logs
AUDIT_ENCRYPTION=True                    # Encrypt sensitive audit data
AUDIT_COMPRESSION=True                   # Compress old audit logs

# Security Monitoring
SECURITY_MONITORING_ENABLED=True         # Enable automated security monitoring
THREAT_DETECTION_SENSITIVITY=medium      # Options: low, medium, high
IP_BLOCKING_ENABLED=True                 # Enable automatic IP blocking
BRUTE_FORCE_THRESHOLD=5                  # Failed attempts before brute force detection

# Storage Configuration (New in v1.4)
PRIMARY_STORAGE_BACKEND=local            # Storage backend: gcs or local
LOCAL_STORAGE_PATH=instance/saved_panels # Local storage directory
MAX_PANEL_VERSIONS=10                    # Maximum versions per panel
AUTO_BACKUP_ENABLED=True                 # Enable automatic backups
```

### Optional Variables

```bash
# Development Only
FLASK_DEBUG=True                         # Enable Flask debug mode (development only)
WERKZEUG_DEBUG_PIN=off                   # Disable Werkzeug debug PIN

# Cloud SQL (Google Cloud Platform)
GOOGLE_CLOUD_SQL=True                    # Enable Google Cloud SQL mode
GOOGLE_CLOUD_PROJECT=your-project-id     # GCP project ID  
CLOUD_SQL_CONNECTION_NAME=project:region:instance  # Cloud SQL connection name

# Current Production Instance (gene-panel-user-db)
# CLOUD_SQL_CONNECTION_NAME=PROJECT_ID:europe-north1:gene-panel-user-db
# DB_HOST=35.228.157.4 (or localhost if using proxy)
# DB_NAME=genepanel-userdb
# DB_USER=genepanel_app

# Google Cloud Storage (for saved panels)
# GOOGLE_APPLICATION_CREDENTIALS=gcs-service-account-key.json  # Service account key file (optional - comment out to use user auth)
BACKUP_STORAGE_BACKEND=local             # Backup storage backend
BACKUP_RETENTION_DAYS=90                 # Days to retain backups
STORAGE_ENCRYPTION_ENABLED=True          # Enable storage encryption
STORAGE_ACCESS_LOGGING=True              # Log storage access

# SSL/TLS Configuration
SSL_CERT_PATH=/path/to/cert.pem          # SSL certificate file path
SSL_KEY_PATH=/path/to/key.pem            # SSL private key file path
SSL_CA_PATH=/path/to/ca.pem              # SSL CA certificate file path
FORCE_HTTPS=True                         # Redirect all HTTP to HTTPS

# Email Configuration (for notifications)
MAIL_SERVER=smtp.gmail.com               # SMTP server
MAIL_PORT=587                            # SMTP port
MAIL_USE_TLS=True                        # Use TLS encryption
MAIL_USERNAME=your-email@gmail.com       # Email username
MAIL_PASSWORD=your-app-password          # Email password or app password
MAIL_DEFAULT_SENDER=your-email@gmail.com # Default sender email

# Monitoring and Analytics
SENTRY_DSN=your-sentry-dsn-here          # Sentry error tracking DSN
GOOGLE_ANALYTICS_ID=GA-XXXXXXXXX         # Google Analytics tracking ID
```

---

## 🗃️ Database Configuration

### SQLite (Development)

For local development, SQLite is the simplest option:

```bash
WITHOUT_DB=False
SQLITE_DB_PATH=instance/gene_panel.db
```

**Pros**: Easy setup, no external dependencies  
**Cons**: Single-user, limited performance, not suitable for production

### PostgreSQL (Production)

For production deployments, PostgreSQL is recommended:

```bash
DATABASE_URL=postgresql://username:password@localhost:5432/panelmerge
```

**Connection String Format**: 
```
postgresql://[user[:password]@][netloc][:port][/dbname][?param1=value1&...]
```

**Example with all parameters**:
```bash
DATABASE_URL=postgresql://panelmerge_user:secure_password@db.example.com:5432/panelmerge_db?sslmode=require
```

### Google Cloud SQL

For Google Cloud Platform deployments:

#### Current Production Setup (gene-panel-user-db)

```bash
# Current Production Configuration
GOOGLE_CLOUD_SQL=True
DATABASE_URL=postgresql://genepanel_app:YOUR_PASSWORD@35.228.157.4:5432/genepanel-userdb?sslmode=require
DB_HOST=35.228.157.4
DB_PORT=5432
DB_NAME=genepanel-userdb
DB_USER=genepanel_app
DB_PASSWORD=YOUR_SECURE_APP_PASSWORD
DB_SSLMODE=require

# Instance Details
# Instance Name: gene-panel-user-db
# Database Version: PostgreSQL 14
# Location: europe-north1-c
# Tier: db-f1-micro
```

#### SSL Certificate Configuration (Optional)

For enhanced security with client certificates:

```bash
DB_SSLCERT=client-cert.pem
DB_SSLKEY=client-key.pem
DB_SSLROOTCERT=server-ca.pem
```

#### Cloud SQL Proxy Connection

Alternative secure connection method using Cloud SQL Proxy:

```bash
# Start proxy: ./cloud-sql-proxy.exe PROJECT_ID:europe-north1:gene-panel-user-db
DATABASE_URL=postgresql://genepanel_app:YOUR_PASSWORD@localhost:5432/genepanel-userdb
DB_HOST=localhost
DB_PORT=5432
```

#### Generic Cloud SQL Setup (for reference)

```bash
GOOGLE_CLOUD_PROJECT=my-project
CLOUD_SQL_CONNECTION_NAME=my-project:us-central1:panelmerge-db
CLOUD_SQL_DATABASE_USER=postgres
CLOUD_SQL_DATABASE_PASSWORD=secure_password
CLOUD_SQL_DATABASE_NAME=panelmerge
DATABASE_URL=postgresql+pg8000://postgres:password@/panelmerge?unix_sock=/cloudsql/my-project:us-central1:panelmerge-db/.s.PGSQL.5432
```

**Important**: See [`docs/GOOGLE_CLOUD_POSTGRESQL_SETUP.md`](GOOGLE_CLOUD_POSTGRESQL_SETUP.md) for complete setup instructions and [`docs/POSTGRESQL_QUICK_REFERENCE.md`](POSTGRESQL_QUICK_REFERENCE.md) for daily operations.

### Database-Free Mode

To run without a database (limited functionality):

```bash
WITHOUT_DB=True
```

**Note**: This disables user authentication, audit logging, and admin features.

---

## 🔒 Security Configuration

### Encryption Keys

Generate secure encryption keys:

```bash
# Generate SECRET_KEY (Python)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY (32 bytes, base64 encoded)
python -c "import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

### Session Security

```bash
SESSION_TIMEOUT=3600                     # 1 hour session timeout
SESSION_PERMANENT=False                  # Sessions expire on browser close
SESSION_USE_SIGNER=True                  # Sign session cookies
SESSION_KEY_PREFIX=panelmerge:           # Redis key prefix for sessions
```

### Password Security

```bash
PASSWORD_MIN_LENGTH=8                    # Minimum password length
PASSWORD_REQUIRE_UPPERCASE=True          # Require uppercase letters
PASSWORD_REQUIRE_LOWERCASE=True          # Require lowercase letters
PASSWORD_REQUIRE_NUMBERS=True            # Require numbers
PASSWORD_REQUIRE_SPECIAL=False           # Require special characters
```

### Rate Limiting

```bash
# Global rate limits
RATELIMIT_STORAGE_URL=redis://localhost:6379/1
RATELIMIT_STRATEGY=fixed-window
RATELIMIT_HEADERS_ENABLED=True

# Specific endpoint limits
LOGIN_RATE_LIMIT=5 per minute            # Login attempts
REGISTER_RATE_LIMIT=3 per hour           # Registration attempts
API_RATE_LIMIT=100 per hour              # API calls
UPLOAD_RATE_LIMIT=10 per hour            # File uploads
```

### IP Blocking

```bash
IP_BLOCKING_ENABLED=True                 # Enable automatic IP blocking
IP_BLOCK_DURATION=3600                   # Block duration in seconds (1 hour)
IP_WHITELIST=127.0.0.1,::1              # Comma-separated IP whitelist
IP_BLACKLIST=                            # Comma-separated IP blacklist
```

---

## 🔴 Redis Configuration

### Basic Redis Setup

```bash
REDIS_URL=redis://localhost:6379/0       # Basic Redis connection
REDIS_PASSWORD=                          # Leave empty if no password
REDIS_SSL=False                          # Set to True for SSL connections
REDIS_SOCKET_CONNECT_TIMEOUT=5           # Connection timeout in seconds
REDIS_SOCKET_TIMEOUT=5                   # Socket timeout in seconds
```

### Redis with Authentication

```bash
REDIS_URL=redis://:password@localhost:6379/0
REDIS_PASSWORD=your_redis_password
```

### Redis with SSL

```bash
REDIS_URL=rediss://localhost:6380/0      # Note: rediss:// for SSL
REDIS_SSL=True
REDIS_SSL_CERT_REQS=required
REDIS_SSL_CA_CERTS=/path/to/ca.pem
```

### Redis Cloud Services

**Redis Labs**:
```bash
REDIS_URL=redis://username:password@redis-12345.redislabs.com:12345/0
```

**Google Cloud Memorystore**:
```bash
REDIS_URL=redis://10.0.0.3:6379/0
```

**AWS ElastiCache**:
```bash
REDIS_URL=redis://clustercfg.my-cluster.xxxxx.cache.amazonaws.com:6379/0
```

### Redis Configuration Options

```bash
# Connection Pool Settings
REDIS_CONNECTION_POOL_MAX_CONNECTIONS=50
REDIS_CONNECTION_POOL_RETRY_ON_TIMEOUT=True

# Session Storage
REDIS_SESSION_DB=0                       # Database number for sessions
REDIS_CACHE_DB=1                         # Database number for caching

# Key Expiration
REDIS_DEFAULT_TIMEOUT=300                # Default key expiration (5 minutes)
REDIS_SESSION_TIMEOUT=3600               # Session expiration (1 hour)
REDIS_CACHE_TIMEOUT=1800                 # Cache expiration (30 minutes)
```

---

## 💾 Storage Configuration

PanelMerge v1.4 introduces a robust storage system for saved panels with support for multiple storage backends, including Google Cloud Storage and local file systems.

### Storage Backend Options

#### Google Cloud Storage (Recommended for Production)

```bash
# Google Cloud Storage Configuration
GOOGLE_CLOUD_PROJECT=your-project-id     # GCP project ID
# GOOGLE_APPLICATION_CREDENTIALS=gcs-service-account-key.json  # Service account key file (optional)

# Storage Backend Configuration
PRIMARY_STORAGE_BACKEND=gcs              # Primary storage backend (gcs or local)
BACKUP_STORAGE_BACKEND=local             # Backup storage backend (local or none)
```

**Benefits**:
- Scalable and reliable cloud storage
- Automatic redundancy and backup
- Cost-effective with lifecycle policies
- Global accessibility

**Authentication Options**:
1. **User Authentication (Recommended for Development)**: Comment out `GOOGLE_APPLICATION_CREDENTIALS` to use gcloud user authentication
2. **Service Account (Production)**: Use service account key file for production deployments

**Setup Requirements**:
- Google Cloud Platform account
- Enabled Cloud Storage API
- Either gcloud user authentication OR service account with Storage Object Admin role
- Three GCS buckets (panels, versions, backups)

For detailed setup instructions, see [Google Cloud Storage Setup Guide](GOOGLE_CLOUD_STORAGE_SETUP.md).

#### Local File Storage

```bash
# Local Storage Configuration
PRIMARY_STORAGE_BACKEND=local            # Use local file system
LOCAL_STORAGE_PATH=instance/saved_panels # Local storage directory
BACKUP_STORAGE_BACKEND=none              # No backup storage
```

**Benefits**:
- Simple setup with no external dependencies
- Full control over data location
- No cloud service costs

**Limitations**:
- Limited scalability
- No automatic redundancy
- Requires manual backup strategies

### Panel Storage Configuration

```bash
# Panel Management Settings
MAX_PANEL_VERSIONS=10                    # Maximum versions per panel
AUTO_BACKUP_ENABLED=True                 # Enable automatic backups
BACKUP_RETENTION_DAYS=90                 # Days to retain backups

# Storage Optimization
PANEL_COMPRESSION_ENABLED=True           # Enable panel data compression
METADATA_CACHING_ENABLED=True            # Cache panel metadata
STORAGE_HEALTH_CHECK_INTERVAL=300        # Health check interval (seconds)
```

### Multi-Backend Configuration

You can configure a primary storage backend with a secondary backup backend:

```bash
# Hybrid Configuration Example
PRIMARY_STORAGE_BACKEND=gcs              # Google Cloud Storage for primary
BACKUP_STORAGE_BACKEND=local             # Local backup for redundancy
LOCAL_STORAGE_PATH=instance/backup_panels

# Failover Settings
STORAGE_FAILOVER_ENABLED=True            # Enable automatic failover
STORAGE_RETRY_ATTEMPTS=3                 # Retry attempts before failover
STORAGE_RETRY_DELAY=1                    # Delay between retries (seconds)
```

### Storage Security

```bash
# Encryption Settings
STORAGE_ENCRYPTION_ENABLED=True          # Enable storage encryption
STORAGE_ENCRYPTION_KEY=your-32-byte-key  # Storage encryption key

# Access Control
STORAGE_ACCESS_LOGGING=True              # Log storage access
STORAGE_AUDIT_ENABLED=True               # Enable storage auditing
STORAGE_IP_RESTRICTIONS=                 # Comma-separated allowed IPs (optional)
```

### Monitoring and Maintenance

```bash
# Storage Monitoring
STORAGE_METRICS_ENABLED=True             # Enable storage metrics collection
STORAGE_ALERT_THRESHOLD=90               # Storage usage alert threshold (%)
STORAGE_CLEANUP_ENABLED=True             # Enable automatic cleanup

# Maintenance Settings
STORAGE_CLEANUP_SCHEDULE=daily           # Cleanup schedule (daily, weekly, monthly)
STORAGE_VACUUM_ENABLED=True              # Enable storage optimization
STORAGE_INTEGRITY_CHECK_ENABLED=True     # Enable integrity checks
```

### Environment-Specific Examples

#### Development Configuration

```bash
# Development storage (local only)
PRIMARY_STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=instance/dev_panels
BACKUP_STORAGE_BACKEND=none
MAX_PANEL_VERSIONS=3
AUTO_BACKUP_ENABLED=False
STORAGE_METRICS_ENABLED=False
```

#### Production Configuration

```bash
# Production storage (GCS with service account)
GOOGLE_CLOUD_PROJECT=your-production-project
GOOGLE_APPLICATION_CREDENTIALS=/app/config/gcs-key.json
PRIMARY_STORAGE_BACKEND=gcs
BACKUP_STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=/app/storage/backup_panels
MAX_PANEL_VERSIONS=10
AUTO_BACKUP_ENABLED=True
BACKUP_RETENTION_DAYS=365
STORAGE_ENCRYPTION_ENABLED=True
STORAGE_ACCESS_LOGGING=True
STORAGE_METRICS_ENABLED=True
```

#### Development with Cloud Storage

```bash
# Development storage (GCS with user authentication)
GOOGLE_CLOUD_PROJECT=your-project-id
# GOOGLE_APPLICATION_CREDENTIALS=  # Commented out - use gcloud user auth
PRIMARY_STORAGE_BACKEND=gcs
BACKUP_STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=instance/backup_panels
MAX_PANEL_VERSIONS=5
AUTO_BACKUP_ENABLED=True
STORAGE_METRICS_ENABLED=True
```

### Storage Performance Optimization

```bash
# Performance Settings
STORAGE_CONNECTION_POOL_SIZE=10          # Connection pool size
STORAGE_REQUEST_TIMEOUT=30               # Request timeout (seconds)
STORAGE_BULK_OPERATION_SIZE=100          # Bulk operation batch size
STORAGE_CACHE_SIZE=1000                  # Storage cache size (items)
STORAGE_PREFETCH_ENABLED=True            # Enable data prefetching
```

### Troubleshooting Storage Issues

Common storage configuration issues and solutions:

1. **Authentication Errors (GCS)**:
   - Verify service account key file exists (if using service account authentication)
   - OR ensure `gcloud auth login` is completed (if using user authentication)
   - Check service account permissions OR user account permissions
   - Ensure Storage API is enabled
   - Consider commenting out `GOOGLE_APPLICATION_CREDENTIALS` to use user authentication in development

2. **Permission Issues (Local)**:
   - Verify directory permissions for `LOCAL_STORAGE_PATH`
   - Check write access to backup directories
   - Ensure sufficient disk space

3. **Performance Issues**:
   - Adjust `STORAGE_CONNECTION_POOL_SIZE`
   - Enable compression for large panels
   - Consider regional bucket placement (GCS)

4. **Backup Failures**:
   - Check backup storage configuration
   - Verify sufficient storage space
   - Review backup retention settings

For detailed troubleshooting, see the [Google Cloud Storage Setup Guide](GOOGLE_CLOUD_STORAGE_SETUP.md).

---

## 🌐 API Configuration

### External API Settings

```bash
# PanelApp UK
PANELAPP_UK_BASE_URL=https://panelapp.genomicsengland.co.uk/api/v1
PANELAPP_UK_TIMEOUT=30
PANELAPP_UK_RETRY_ATTEMPTS=3
PANELAPP_UK_CACHE_TIMEOUT=3600

# PanelApp Australia
PANELAPP_AUS_BASE_URL=https://panelapp.agha.umccr.org/api/v1
PANELAPP_AUS_TIMEOUT=30
PANELAPP_AUS_RETRY_ATTEMPTS=3
PANELAPP_AUS_CACHE_TIMEOUT=3600

# API Rate Limiting
API_RATE_LIMIT_ENABLED=True
API_RATE_LIMIT_PER_MINUTE=60
API_RATE_LIMIT_PER_HOUR=1000
API_RATE_LIMIT_BURST=10
```

### Internal API Settings

```bash
# API Authentication
API_KEY_REQUIRED=False                   # Require API keys for internal APIs
API_KEY_HEADER=X-API-Key                 # Header name for API keys
API_VERSION=v1                           # API version prefix

# API Documentation
API_DOCS_ENABLED=True                    # Enable API documentation
API_DOCS_URL=/api/docs                   # URL for API documentation
```

---

## 🚀 Deployment Configurations

### Development Configuration

```bash
# .env.development
FLASK_ENV=development
DEBUG=True
SECRET_KEY=dev-secret-key-not-for-production
WITHOUT_DB=False
SQLITE_DB_PATH=instance/gene_panel_dev.db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=DEBUG
SECURITY_MONITORING_ENABLED=False
RATE_LIMIT_PER_MINUTE=1000
```

### Staging Configuration

```bash
# .env.staging
FLASK_ENV=production
DEBUG=False
SECRET_KEY=staging-secret-key
DATABASE_URL=postgresql://user:pass@staging-db:5432/panelmerge_staging
REDIS_URL=redis://staging-redis:6379/0
LOG_LEVEL=INFO
SECURITY_MONITORING_ENABLED=True
RATE_LIMIT_PER_MINUTE=100
```

### Production Configuration

```bash
# .env.production
FLASK_ENV=production
DEBUG=False
SECRET_KEY=production-secret-key-32-chars-min

# Google Cloud PostgreSQL Configuration
GOOGLE_CLOUD_SQL=True
DATABASE_URL=postgresql://genepanel_app:SECURE_PASSWORD@35.228.157.4:5432/genepanel-userdb?sslmode=require
DB_HOST=35.228.157.4
DB_PORT=5432
DB_NAME=genepanel-userdb
DB_USER=genepanel_app
DB_SSLMODE=require

# Redis Configuration
REDIS_URL=redis://prod-redis:6379/0

# Security Settings
LOG_LEVEL=WARNING
SECURITY_MONITORING_ENABLED=True
RATE_LIMIT_PER_MINUTE=60
FORCE_HTTPS=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Strict

# SSL Certificates (if using client certs)
# DB_SSLCERT=client-cert.pem
# DB_SSLKEY=client-key.pem
# DB_SSLROOTCERT=server-ca.pem
```

### Production with Cloud SQL Proxy

```bash
# Alternative: Using Cloud SQL Proxy for enhanced security
# Start proxy: ./cloud-sql-proxy.exe PROJECT_ID:europe-north1:gene-panel-user-db
DATABASE_URL=postgresql://genepanel_app:SECURE_PASSWORD@localhost:5432/genepanel-userdb
DB_HOST=localhost
DB_PORT=5432
```

### Docker Configuration

```bash
# .env.docker
FLASK_ENV=production
DATABASE_URL=postgresql://postgres:password@db:5432/panelmerge
REDIS_URL=redis://redis:6379/0
UPLOAD_FOLDER=/app/uploads
LOG_FILE=/app/logs/panelmerge.log
```

---

## 🏭 Environment-Specific Settings

### Development vs Production

| Setting | Development | Production |
|---------|-------------|------------|
| `DEBUG` | `True` | `False` |
| `LOG_LEVEL` | `DEBUG` | `WARNING` |
| `SESSION_TIMEOUT` | `7200` (2h) | `3600` (1h) |
| `RATE_LIMIT_PER_MINUTE` | `1000` | `60` |
| `SECURITY_MONITORING_ENABLED` | `False` | `True` |
| `FORCE_HTTPS` | `False` | `True` |
| `SESSION_COOKIE_SECURE` | `False` | `True` |

### Security Headers (Production)

```bash
# Security Headers
SECURITY_HEADERS_ENABLED=True
CONTENT_SECURITY_POLICY=default-src 'self'; script-src 'self' 'unsafe-inline'
X_CONTENT_TYPE_OPTIONS=nosniff
X_FRAME_OPTIONS=DENY
X_XSS_PROTECTION=1; mode=block
STRICT_TRANSPORT_SECURITY=max-age=31536000; includeSubDomains
```

---

## 🔧 Configuration Validation

### Required Environment Check

Create a configuration validation script:

```python
# config_validator.py
import os
import sys

REQUIRED_VARS = [
    'SECRET_KEY',
    'FLASK_ENV',
    'DATABASE_URL',  # or WITHOUT_DB=True
    'REDIS_URL',
]

PRODUCTION_REQUIRED = [
    'ENCRYPTION_KEY',
    'SESSION_TIMEOUT',
    'RATE_LIMIT_PER_MINUTE',
]

def validate_config():
    missing = []
    
    for var in REQUIRED_VARS:
        if not os.getenv(var):
            if var == 'DATABASE_URL' and os.getenv('WITHOUT_DB') == 'True':
                continue
            missing.append(var)
    
    if os.getenv('FLASK_ENV') == 'production':
        for var in PRODUCTION_REQUIRED:
            if not os.getenv(var):
                missing.append(var)
    
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    print("✅ Configuration validation passed")

if __name__ == "__main__":
    validate_config()
```

Run before deployment:
```bash
python config_validator.py
```

---

## 🔍 Troubleshooting

### Common Configuration Issues

**1. Database Connection Errors**

*SQLite (Development):*
```bash
# Check SQLite database path
SQLITE_DB_PATH=instance/gene_panel.db
mkdir -p instance
chmod 755 instance
```

*PostgreSQL (Production):*
```bash
# Check database URL format
DATABASE_URL=postgresql://user:password@host:port/database

# Test connection with psql
psql "postgresql://genepanel_app:PASSWORD@35.228.157.4:5432/genepanel-userdb?sslmode=require"
```

*Google Cloud SQL Specific:*
```bash
# Check instance status
gcloud sql instances describe gene-panel-user-db

# Test connection via gcloud
gcloud sql connect gene-panel-user-db --user=genepanel_app --database=genepanel-userdb

# Test Cloud SQL Proxy connection
./cloud-sql-proxy.exe PROJECT_ID:europe-north1:gene-panel-user-db
psql "postgresql://genepanel_app:PASSWORD@localhost:5432/genepanel-userdb"

# Check authorized networks
gcloud sql instances describe gene-panel-user-db --format="value(settings.ipConfiguration.authorizedNetworks[].value)"

# Test application connection
python -c "
import os
os.environ['GOOGLE_CLOUD_SQL'] = 'true'
os.environ['DATABASE_URL'] = 'postgresql://genepanel_app:PASSWORD@35.228.157.4:5432/genepanel-userdb?sslmode=require'
from app import create_app
app = create_app()
with app.app_context():
    from app.extensions import db
    db.create_all()
    print('Google Cloud SQL connection successful!')
"
```

**2. Redis Connection Errors**
```bash
# Test Redis connection
redis-cli -h localhost -p 6379 ping

# Check Redis URL format
REDIS_URL=redis://[:password@]host:port/db
```

**3. Secret Key Issues**
```bash
# Generate new secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Ensure key is at least 32 characters
```

**4. File Upload Issues**
```bash
# Check upload directory permissions
mkdir -p instance/uploads
chmod 755 instance/uploads

# Verify MAX_CONTENT_LENGTH setting
MAX_CONTENT_LENGTH=16777216  # 16MB in bytes
```

**5. SSL/TLS Issues**
```bash
# Check certificate files
openssl x509 -in cert.pem -text -noout
openssl rsa -in key.pem -check

# Verify SSL configuration
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

**7. Cloud SQL Authentication Conflicts**

If Cloud SQL connection fails after adding Google Cloud Storage configuration:

```bash
# Check for conflicting authentication
echo $GOOGLE_APPLICATION_CREDENTIALS

# If set to GCS service account, temporarily clear it for Cloud SQL
# Option 1: Comment out in .env file
# GOOGLE_APPLICATION_CREDENTIALS=gcs-service-account-key.json

# Option 2: Use different service account with both Cloud SQL and Storage permissions
# Or ensure user account has both roles/cloudsql.client and roles/storage.objectAdmin

# Test Cloud SQL connection without GCS credentials
unset GOOGLE_APPLICATION_CREDENTIALS
gcloud sql connect gene-panel-user-db --user=genepanel_app --database=genepanel-userdb

# Verify user permissions include both Cloud SQL and Storage
gcloud projects get-iam-policy PROJECT_ID --filter="bindings.members:user:YOUR_EMAIL@gmail.com" --format="value(bindings.role)" | grep -E "(sql|storage)"
```

**Root Cause**: Google Cloud libraries automatically use `GOOGLE_APPLICATION_CREDENTIALS` file for all services. If the service account only has storage permissions, Cloud SQL connections will fail.

**Solutions**:
1. **Development**: Use user authentication (comment out `GOOGLE_APPLICATION_CREDENTIALS`)
2. **Production**: Create service account with both Cloud SQL and Storage permissions
3. **Hybrid**: Use different service accounts for different services with explicit credential passing

### Configuration Testing

```bash
# Test configuration loading
python -c "
from app.config_settings import get_config
config = get_config()
print('Configuration loaded successfully')
print(f'Environment: {config.FLASK_ENV}')
print(f'Database: {config.DATABASE_URL[:20]}...')
"

# Test database connection
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database connection successful')
"

# Test Redis connection
python -c "
from app.extensions import redis_client
redis_client.ping()
print('Redis connection successful')
"
```

### Performance Tuning

```bash
# Database connection pool
DATABASE_POOL_SIZE=20
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600

# Redis connection pool
REDIS_CONNECTION_POOL_MAX_CONNECTIONS=50
REDIS_CONNECTION_POOL_TIMEOUT=20

# Worker configuration
WORKERS=4                                # Number of worker processes
WORKER_CONNECTIONS=1000                  # Connections per worker
WORKER_TIMEOUT=30                        # Worker timeout in seconds
```

---

## 📚 Additional Resources

- **Flask Configuration**: https://flask.palletsprojects.com/en/2.3.x/config/
- **PostgreSQL Connection**: https://www.postgresql.org/docs/current/libpq-connect.html
- **Google Cloud PostgreSQL Setup**: See [`GOOGLE_CLOUD_POSTGRESQL_SETUP.md`](GOOGLE_CLOUD_POSTGRESQL_SETUP.md)
- **PostgreSQL Quick Reference**: See [`POSTGRESQL_QUICK_REFERENCE.md`](POSTGRESQL_QUICK_REFERENCE.md)
- **Redis Configuration**: https://redis.io/docs/manual/config/
- **Google Cloud SQL**: https://cloud.google.com/sql/docs/postgres/connect-app-engine
- **Google Cloud Storage Setup**: See [`GOOGLE_CLOUD_STORAGE_SETUP.md`](GOOGLE_CLOUD_STORAGE_SETUP.md)
- **Security Best Practices**: See [`SECURITY_CONFIGURATION_GUIDE.md`](SECURITY_CONFIGURATION_GUIDE.md)

---

**Last Updated**: 2025-08-03  
**Document Version**: 1.2  
**Maintainer**: Development Team

> This configuration guide should be reviewed and updated with each release to ensure all configuration options are documented and current. Updated to include current Google Cloud PostgreSQL production configuration.
