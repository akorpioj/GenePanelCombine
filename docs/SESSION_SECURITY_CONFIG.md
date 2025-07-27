# Session Security Configuration Guide

## Production Deployment Configuration

This guide provides comprehensive configuration instructions for deploying the Enhanced Session Security System in production environments.

## Environment Configuration

### Required Environment Variables

```bash
# Core Session Security Settings
SESSION_TIMEOUT=1800                     # 30 minutes for production
MAX_CONCURRENT_SESSIONS=3                # Limit to 3 sessions per user
SESSION_ROTATION_INTERVAL=900            # Rotate every 15 minutes
ENABLE_SESSION_ANALYTICS=true            # Enable monitoring

# Redis Configuration (Required for Production)
REDIS_URL=rediss://username:password@host:port/db  # Use SSL in production
REDIS_SSL_CERT_REQS=required            # Require SSL certificates
REDIS_SSL_CHECK_HOSTNAME=true           # Verify hostname

# Security Settings
REQUIRE_HTTPS=true                       # Force HTTPS
HSTS_MAX_AGE=31536000                   # 1 year HSTS
SESSION_COOKIE_SECURE=true              # Secure cookies only
SESSION_COOKIE_HTTPONLY=true            # Prevent XSS access
SESSION_COOKIE_SAMESITE=Strict          # CSRF protection

# Encryption Settings
ENCRYPTION_MASTER_KEY=your_32_byte_key   # Strong encryption key
ENCRYPT_SENSITIVE_FIELDS=true           # Enable field encryption
```

### Redis Production Configuration

#### Redis Security Configuration

```redis
# redis.conf
bind 127.0.0.1                          # Bind to localhost only
protected-mode yes                       # Enable protected mode
requirepass your_strong_redis_password   # Set strong password
timeout 300                             # Client timeout
tcp-keepalive 300                       # TCP keepalive

# Memory and Performance
maxmemory 2gb                           # Set memory limit
maxmemory-policy allkeys-lru            # LRU eviction policy
save 900 1                              # Persistence settings
save 300 10
save 60 10000

# Security
rename-command FLUSHDB ""               # Disable dangerous commands
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG ""
```

#### Redis SSL/TLS Configuration

```redis
# Enable TLS
tls-port 6380
port 0                                  # Disable non-TLS port

# TLS Configuration
tls-cert-file /path/to/redis.crt
tls-key-file /path/to/redis.key
tls-ca-cert-file /path/to/ca.crt
tls-protocols "TLSv1.2 TLSv1.3"
```

## Application Configuration

### Production Flask Configuration

```python
class ProductionConfig(Config):
    """Production configuration with enhanced security"""
    
    # Basic Settings
    DEBUG = False
    TESTING = False
    
    # Security Settings
    REQUIRE_HTTPS = True
    HSTS_MAX_AGE = 31536000                     # 1 year
    SESSION_TIMEOUT = 1800                      # 30 minutes
    ENCRYPT_SENSITIVE_FIELDS = True
    
    # Enhanced Session Configuration
    MAX_CONCURRENT_SESSIONS = 3                 # Stricter limit
    SESSION_ROTATION_INTERVAL = 900             # 15 minutes
    ENABLE_SESSION_ANALYTICS = True
    
    # Cookie Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    SESSION_COOKIE_NAME = '__Secure-session'
    
    # Additional Security Headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'"
    }
```

### Docker Configuration

#### Dockerfile for Production

```dockerfile
FROM python:3.11-slim

# Security: Create non-root user
RUN useradd --create-home --shell /bin/bash app
WORKDIR /home/app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .
RUN chown -R app:app /home/app

# Switch to non-root user
USER app

# Security: Run with limited privileges
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "300", "run:app"]
```

#### Docker Compose for Production

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - FLASK_CONFIG=production
      - REDIS_URL=redis://redis:6379/0
      - SESSION_TIMEOUT=1800
      - MAX_CONCURRENT_SESSIONS=3
      - REQUIRE_HTTPS=true
    depends_on:
      - redis
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  redis_data:
```

## Web Server Configuration

### Nginx Configuration

```nginx
# nginx.conf
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    
    location /auth/login {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://app:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location / {
        proxy_pass http://app:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## Monitoring and Alerting

### Application Monitoring

#### Health Check Endpoint

```python
@app.route('/health/sessions')
def session_health():
    """Health check for session service"""
    try:
        # Check Redis connectivity
        session_service.redis_client.ping()
        
        # Check session creation capability
        test_token = session_service._generate_session_token()
        
        return {
            'status': 'healthy',
            'redis_connected': True,
            'token_generation': True,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }, 503
```

#### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Session metrics
session_created_total = Counter('sessions_created_total', 'Total sessions created')
session_destroyed_total = Counter('sessions_destroyed_total', 'Total sessions destroyed')
session_hijacking_attempts = Counter('session_hijacking_attempts_total', 'Session hijacking attempts')
session_duration = Histogram('session_duration_seconds', 'Session duration in seconds')
active_sessions = Gauge('active_sessions_total', 'Current active sessions')

# Update metrics in session service
def create_session(self, user_id, ...):
    session_created_total.inc()
    # ... session creation logic
    
def destroy_session(self, session_token):
    session_destroyed_total.inc()
    # ... session destruction logic
```

### Log Configuration

#### Structured Logging

```python
import logging
import json
from datetime import datetime

class SessionSecurityFormatter(logging.Formatter):
    """Custom formatter for session security events"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'component': 'session_security',
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add session context if available
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'session_token'):
            log_entry['session_token'] = record.session_token[:8] + '...'
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
            
        return json.dumps(log_entry)

# Configure logging
logging.getLogger('app.session_service').addHandler(
    logging.StreamHandler()
)
logging.getLogger('app.session_service').setLevel(logging.INFO)
```

### Security Monitoring

#### Alert Configuration

```yaml
# alerts.yml for Prometheus AlertManager
groups:
- name: session_security
  rules:
  - alert: HighSessionHijackingAttempts
    expr: rate(session_hijacking_attempts_total[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High rate of session hijacking attempts"
      description: "{{ $value }} hijacking attempts per second"
      
  - alert: SessionServiceDown
    expr: up{job="session_health"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Session service is down"
      
  - alert: RedisConnectionLoss
    expr: redis_connected_clients == 0
    for: 30s
    labels:
      severity: critical
    annotations:
      summary: "Redis connection lost"
```

## Database Configuration

### PostgreSQL Configuration for Audit Logs

```sql
-- Optimize audit log table
CREATE INDEX CONCURRENTLY idx_audit_log_user_id_timestamp 
ON audit_log (user_id, timestamp DESC);

CREATE INDEX CONCURRENTLY idx_audit_log_action_type_timestamp 
ON audit_log (action_type, timestamp DESC);

CREATE INDEX CONCURRENTLY idx_audit_log_session_management 
ON audit_log (action_type, timestamp DESC) 
WHERE action_type = 'SESSION_MANAGEMENT';

-- Partition audit table by month (optional for large deployments)
CREATE TABLE audit_log_2025_07 PARTITION OF audit_log
FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');
```

### Database Connection Security

```python
# Secure database configuration
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'connect_args': {
        'sslmode': 'require',
        'sslcert': '/path/to/client-cert.pem',
        'sslkey': '/path/to/client-key.pem',
        'sslrootcert': '/path/to/ca-cert.pem'
    }
}
```

## Backup and Recovery

### Redis Backup Strategy

```bash
#!/bin/bash
# redis_backup.sh

BACKUP_DIR="/backups/redis"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
redis-cli BGSAVE
sleep 10

# Copy RDB file
cp /var/lib/redis/dump.rdb "$BACKUP_DIR/redis_backup_$DATE.rdb"

# Compress backup
gzip "$BACKUP_DIR/redis_backup_$DATE.rdb"

# Keep only last 7 days
find "$BACKUP_DIR" -name "redis_backup_*.rdb.gz" -mtime +7 -delete
```

### Recovery Procedures

```bash
#!/bin/bash
# redis_recovery.sh

BACKUP_FILE=$1
REDIS_DATA_DIR="/var/lib/redis"

# Stop Redis
systemctl stop redis

# Backup current data
mv "$REDIS_DATA_DIR/dump.rdb" "$REDIS_DATA_DIR/dump.rdb.backup"

# Restore from backup
gunzip -c "$BACKUP_FILE" > "$REDIS_DATA_DIR/dump.rdb"
chown redis:redis "$REDIS_DATA_DIR/dump.rdb"

# Start Redis
systemctl start redis
```

## Performance Tuning

### Redis Optimization

```redis
# Performance settings
tcp-keepalive 300
timeout 300

# Memory optimization
maxmemory-policy allkeys-lru
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes

# Persistence optimization
save 900 1
save 300 10
save 60 10000
rdbcompression yes
rdbchecksum yes
```

### Session Cleanup Optimization

```python
# Optimized session cleanup
class SessionCleanupTask:
    def __init__(self, session_service):
        self.session_service = session_service
        
    def cleanup_expired_sessions(self):
        """Background task to clean up expired sessions"""
        current_time = time.time()
        
        # Get all session keys
        session_keys = self.session_service.redis_client.keys("session:*")
        
        # Batch process cleanup
        pipe = self.session_service.redis_client.pipeline()
        
        for key in session_keys:
            session_data = self.session_service.redis_client.hgetall(key)
            if session_data:
                last_activity = float(session_data.get('last_activity', 0))
                if current_time - last_activity > self.session_service.session_timeout:
                    pipe.delete(key)
                    # Remove from user sessions set
                    user_id = session_data.get('user_id')
                    if user_id:
                        pipe.srem(f"user_sessions:{user_id}", key.split(':')[1])
        
        pipe.execute()
```

## Security Checklist

### Pre-Production Checklist

- [ ] **SSL/TLS Configuration**
  - [ ] Valid SSL certificates installed
  - [ ] TLS 1.2+ enforced
  - [ ] Strong cipher suites configured
  - [ ] HSTS headers enabled

- [ ] **Session Security**
  - [ ] HTTPS-only cookies enabled
  - [ ] Secure session timeouts configured
  - [ ] Session rotation intervals set
  - [ ] Concurrent session limits enforced

- [ ] **Redis Security**
  - [ ] Authentication enabled
  - [ ] Network access restricted
  - [ ] Dangerous commands disabled
  - [ ] SSL/TLS enabled for Redis

- [ ] **Monitoring & Alerting**
  - [ ] Health checks configured
  - [ ] Security alerts set up
  - [ ] Log aggregation enabled
  - [ ] Metrics collection active

- [ ] **Database Security**
  - [ ] SSL connections enforced
  - [ ] Access controls configured
  - [ ] Audit log retention set
  - [ ] Backup procedures tested

### Post-Deployment Verification

```bash
# Verify HTTPS enforcement
curl -I http://yourdomain.com
# Should redirect to HTTPS

# Test session security
curl -k -c cookies.txt https://yourdomain.com/auth/login
# Verify secure cookie attributes

# Check Redis connectivity
redis-cli -h redis-host ping
# Should return PONG

# Verify session creation
curl -X POST https://yourdomain.com/auth/login \
  -d "username=test&password=test" \
  -c session_cookies.txt

# Check session management
curl -b session_cookies.txt https://yourdomain.com/profile/sessions
```

## Recent Updates

### Individual Session Revocation (v2.0)

The Enhanced Session Security System now supports individual session revocation in addition to bulk session revocation:

#### New Features
- **Individual Session Control**: Users can now revoke specific sessions instead of all sessions at once
- **Enhanced UI**: Each session display includes an individual "Revoke" button for non-current sessions
- **Granular Security**: Better user control over active sessions across devices
- **Audit Logging**: All individual session revocations are logged with specific session details

#### Configuration Notes
- No additional configuration required - feature is enabled automatically
- Uses existing Redis session storage
- Compatible with all existing session security features
- Maintains backward compatibility with bulk revocation

#### Testing Individual Session Revocation
```bash
# Create test sessions for testing
python create_test_sessions.py

# Access session management interface
curl -b session_cookies.txt https://yourdomain.com/profile/sessions

# Test individual revocation (replace SESSION_ID with actual session ID)
curl -X POST -b session_cookies.txt \
  https://yourdomain.com/profile/sessions/revoke/SESSION_ID
```

This configuration guide ensures your Enhanced Session Security System is properly configured for production environments with maximum security and performance.
