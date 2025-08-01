# PanelMerge Configuration Guide

This guide provides comprehensive configuration instructions for PanelMerge v1.4, covering environment variables, security settings, database configuration, and deployment options.

## 📋 Table of Contents

1. [Environment Variables](#environment-variables)
2. [Database Configuration](#database-configuration)
3. [Security Configuration](#security-configuration)
4. [Redis Configuration](#redis-configuration)
5. [API Configuration](#api-configuration)
6. [Deployment Configurations](#deployment-configurations)
7. [Development vs Production](#development-vs-production)
8. [Troubleshooting](#troubleshooting)

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
```

### Optional Variables

```bash
# Development Only
FLASK_DEBUG=True                         # Enable Flask debug mode (development only)
WERKZEUG_DEBUG_PIN=off                   # Disable Werkzeug debug PIN

# Cloud SQL (Google Cloud Platform)
GOOGLE_CLOUD_PROJECT=your-project-id     # GCP project ID
CLOUD_SQL_CONNECTION_NAME=project:region:instance  # Cloud SQL connection name
CLOUD_SQL_DATABASE_USER=postgres         # Cloud SQL database user
CLOUD_SQL_DATABASE_PASSWORD=password     # Cloud SQL database password
CLOUD_SQL_DATABASE_NAME=panelmerge       # Cloud SQL database name

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

```bash
GOOGLE_CLOUD_PROJECT=my-project
CLOUD_SQL_CONNECTION_NAME=my-project:us-central1:panelmerge-db
CLOUD_SQL_DATABASE_USER=postgres
CLOUD_SQL_DATABASE_PASSWORD=secure_password
CLOUD_SQL_DATABASE_NAME=panelmerge
DATABASE_URL=postgresql+pg8000://postgres:password@/panelmerge?unix_sock=/cloudsql/my-project:us-central1:panelmerge-db/.s.PGSQL.5432
```

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
DATABASE_URL=postgresql://user:pass@prod-db:5432/panelmerge
REDIS_URL=redis://prod-redis:6379/0
LOG_LEVEL=WARNING
SECURITY_MONITORING_ENABLED=True
RATE_LIMIT_PER_MINUTE=60
FORCE_HTTPS=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Strict
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
```bash
# Check database URL format
DATABASE_URL=postgresql://user:password@host:port/database

# Test connection
python -c "from app import create_app; app = create_app(); print('Database connected!')"
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
- **Redis Configuration**: https://redis.io/docs/manual/config/
- **Google Cloud SQL**: https://cloud.google.com/sql/docs/postgres/connect-app-engine
- **Security Best Practices**: See `SECURITY_CONFIGURATION_GUIDE.md`

---

**Last Updated**: 2025-07-27  
**Document Version**: 1.0  
**Maintainer**: Development Team

> This configuration guide should be reviewed and updated with each release to ensure all configuration options are documented and current.
