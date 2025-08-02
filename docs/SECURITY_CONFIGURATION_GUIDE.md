# Security Configuration Guide

## Overview

This guide provides comprehensive security configuration instructions for the PanelMerge application, covering encryption, HTTPS enforcement, security headers, and best practices for production deployment.

## Security Configuration Checklist

### ✅ Essential Security Features

- [x] **Data Encryption**: Field-level and file encryption implemented
- [x] **HTTPS Enforcement**: Mandatory HTTPS for production
- [x] **Security Headers**: Comprehensive HTTP security headers
- [x] **CSRF Protection**: Cross-site request forgery protection
- [x] **Session Security**: Enhanced session management
- [x] **Rate Limiting**: IP-based request throttling
- [x] **Audit Logging**: Comprehensive security event logging

## Environment Configuration

### Production Environment Variables

```bash
# Security Settings
REQUIRE_HTTPS=true
HSTS_MAX_AGE=31536000
SESSION_TIMEOUT=1800
CSRF_PROTECTION=true

# Encryption Settings
ENCRYPTION_MASTER_KEY=<base64-encoded-256-bit-key>
ENCRYPT_SENSITIVE_FIELDS=true

# Session Security
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Content Security Policy
CSP_ENABLED=true
CSP_REPORT_URI=/security/csp-report
```

### Development Environment

```bash
# Development Settings (less restrictive)
REQUIRE_HTTPS=false
SESSION_TIMEOUT=3600
ENCRYPT_SENSITIVE_FIELDS=true
CSRF_PROTECTION=true
RATE_LIMIT_ENABLED=false
```

## HTTPS Configuration

### 1. Certificate Setup

#### Self-Signed Certificate (Development)
```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

#### Production Certificate
```bash
# Using Let's Encrypt with certbot
sudo certbot --nginx -d your-domain.com

# Or using custom certificate
# Place certificate files in secure location
# /etc/ssl/certs/your-domain.crt
# /etc/ssl/private/your-domain.key
```

### 2. Web Server Configuration

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Application proxy
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Apache Configuration
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    Redirect permanent / https://your-domain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName your-domain.com
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/your-domain.crt
    SSLCertificateKeyFile /etc/ssl/private/your-domain.key
    
    # Modern SSL configuration
    SSLProtocol -all +TLSv1.2 +TLSv1.3
    SSLCipherSuite ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512
    SSLHonorCipherOrder off
    
    # Security Headers
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    Header always set X-Frame-Options "DENY"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    
    # Application proxy
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/
    ProxyPreserveHost On
</VirtualHost>
```

## Content Security Policy (CSP)

### CSP Configuration

```python
# app/security_service.py - CSP configuration
def get_csp_header():
    """Generate Content Security Policy header"""
    directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com",
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: https:",
        "connect-src 'self' https://panelapp.genomicsengland.co.uk",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "upgrade-insecure-requests"
    ]
    
    return "; ".join(directives)
```

### CSP Reporting

```python
@app.route('/security/csp-report', methods=['POST'])
def csp_report():
    """Handle CSP violation reports"""
    try:
        report = request.get_json()
        logger.warning(f"CSP Violation: {report}")
        
        # Store violation for analysis
        csp_violation = CSPViolation(
            document_uri=report.get('document-uri'),
            violated_directive=report.get('violated-directive'),
            blocked_uri=report.get('blocked-uri'),
            timestamp=datetime.datetime.now()
        )
        db.session.add(csp_violation)
        db.session.commit()
        
    except Exception as e:
        logger.error(f"CSP report error: {e}")
    
    return '', 204
```

## Database Security

### Connection Security

```python
# Secure database connection
DATABASE_URL = "postgresql://user:password@host:5432/dbname?sslmode=require"

# Additional security parameters
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

### Database User Permissions

```sql
-- Create application user with minimal permissions
CREATE USER app_user WITH PASSWORD 'strong_password';

-- Grant only necessary permissions
GRANT CONNECT ON DATABASE genepanel_db TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Revoke unnecessary permissions
REVOKE CREATE ON SCHEMA public FROM app_user;
REVOKE ALL ON SCHEMA information_schema FROM app_user;
REVOKE ALL ON SCHEMA pg_catalog FROM app_user;
```

## Rate Limiting Configuration

### Application-Level Rate Limiting

```python
# app/security_service.py
class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.blocked_ips = set()
    
    def is_rate_limited(self, client_ip, limit=100, window=60):
        """Check if client exceeds rate limit"""
        current_time = time.time()
        
        # Clean old entries
        cutoff = current_time - window
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip] 
                if req_time > cutoff
            ]
        
        # Count current requests
        request_count = len(self.requests.get(client_ip, []))
        
        if request_count >= limit:
            self.blocked_ips.add(client_ip)
            return True
        
        # Add current request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)
        
        return False
```

### Nginx Rate Limiting

```nginx
# Rate limiting configuration
http {
    # Define rate limiting zones
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=general:10m rate=200r/m;
    
    server {
        # Apply rate limiting to specific locations
        location /auth/login {
            limit_req zone=login burst=3 nodelay;
            # ... other configuration
        }
        
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            # ... other configuration
        }
        
        location / {
            limit_req zone=general burst=50 nodelay;
            # ... other configuration
        }
    }
}
```

## Session Security

### Session Configuration

```python
# Enhanced session security
app.config.update(
    # Session cookies
    SESSION_COOKIE_SECURE=True,           # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,         # No JavaScript access
    SESSION_COOKIE_SAMESITE='Lax',        # CSRF protection
    
    # Session timeout
    PERMANENT_SESSION_LIFETIME=1800,      # 30 minutes
    
    # Session key rotation
    SESSION_KEY_PREFIX='panelmerge_',
    
    # Additional security
    WTF_CSRF_ENABLED=True,
    WTF_CSRF_TIME_LIMIT=3600,
)
```

### Session Validation

```python
@app.before_request
def validate_session():
    """Enhanced session validation"""
    if 'user_id' in session:
        # Check session timeout
        last_activity = session.get('last_activity', 0)
        if time.time() - last_activity > app.config['PERMANENT_SESSION_LIFETIME']:
            session.clear()
            flash('Session expired. Please log in again.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Update last activity
        session['last_activity'] = time.time()
        
        # Validate session integrity
        expected_hash = session.get('session_hash')
        current_hash = generate_session_hash(session['user_id'])
        
        if expected_hash != current_hash:
            session.clear()
            logger.warning(f"Session integrity violation for user {session.get('user_id')}")
            return redirect(url_for('auth.login'))
```

## File Upload Security

### Secure Upload Configuration

```python
# File upload security
UPLOAD_FOLDER = '/secure/uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'.txt', '.csv', '.tsv', '.bed', '.json', '.xlsx', '.xls'}

# File validation
def secure_file_upload(file):
    """Comprehensive file security validation"""
    
    # Size check
    if len(file.read()) > current_app.config['MAX_CONTENT_LENGTH']:
        raise ValueError("File too large")
    file.seek(0)
    
    # Extension check
    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        raise ValueError("File type not allowed")
    
    # Content validation
    if not validate_file_content(file):
        raise ValueError("File content validation failed")
    
    # Virus scanning (if available)
    if virus_scan_available():
        if not virus_scan_file(file):
            raise ValueError("File failed security scan")
    
    return filename
```

### File Storage Security

```bash
# Secure file storage directory permissions
sudo mkdir -p /secure/uploads
sudo chown app_user:app_group /secure/uploads
sudo chmod 750 /secure/uploads

# SELinux context (if applicable)
sudo setsebool -P httpd_can_network_connect 1
sudo semanage fcontext -a -t httpd_exec_t "/secure/uploads(/.*)?"
sudo restorecon -R /secure/uploads
```

## Monitoring & Alerting

### Security Event Monitoring

```python
# Security event logging
class SecurityMonitor:
    def __init__(self):
        self.alerts = []
        self.thresholds = {
            'failed_logins': 5,
            'encryption_failures': 3,
            'csp_violations': 10,
            'rate_limit_hits': 20
        }
    
    def log_security_event(self, event_type, details):
        """Log and analyze security events"""
        event = {
            'type': event_type,
            'timestamp': datetime.datetime.now(),
            'details': details,
            'ip_address': request.remote_addr,
            'user_agent': request.user_agent.string
        }
        
        logger.warning(f"Security Event: {event}")
        
        # Check for alert conditions
        self.check_alert_thresholds(event_type)
    
    def check_alert_thresholds(self, event_type):
        """Check if event triggers alert threshold"""
        recent_events = self.count_recent_events(event_type, minutes=10)
        threshold = self.thresholds.get(event_type, 999)
        
        if recent_events >= threshold:
            self.send_security_alert(event_type, recent_events)
```

### Alert Configuration

```python
# Email alerts for security events
def send_security_alert(event_type, count):
    """Send security alert to administrators"""
    subject = f"Security Alert: {event_type}"
    body = f"""
    Security threshold exceeded:
    
    Event Type: {event_type}
    Count: {count} in last 10 minutes
    Time: {datetime.datetime.now()}
    
    Please investigate immediately.
    """
    
    send_email(
        to=current_app.config['SECURITY_ALERT_EMAIL'],
        subject=subject,
        body=body
    )
```

## Security Testing

### Automated Security Tests

```python
def test_security_headers():
    """Test security headers are present"""
    with app.test_client() as client:
        response = client.get('/')
        
        # Check required headers
        assert 'Strict-Transport-Security' in response.headers
        assert 'X-Frame-Options' in response.headers
        assert 'X-Content-Type-Options' in response.headers
        assert 'Content-Security-Policy' in response.headers

def test_https_enforcement():
    """Test HTTPS redirection"""
    with app.test_client() as client:
        # Simulate HTTP request
        response = client.get('/', base_url='http://localhost')
        assert response.status_code == 301
        assert response.location.startswith('https://')

def test_csrf_protection():
    """Test CSRF protection is active"""
    with app.test_client() as client:
        # POST without CSRF token should fail
        response = client.post('/auth/login', data={
            'username': 'test',
            'password': 'test'
        })
        assert response.status_code == 403
```

### Manual Security Testing

```bash
# SSL/TLS testing
nmap --script ssl-enum-ciphers -p 443 your-domain.com

# Header security testing
curl -I https://your-domain.com

# CSRF testing
curl -X POST https://your-domain.com/auth/login \
  -d "username=test&password=test" \
  -c cookies.txt

# Rate limiting testing
for i in {1..150}; do
  curl -s https://your-domain.com/api/panels > /dev/null
done
```

## Compliance & Auditing

### GDPR Compliance

```python
# Data protection features
class GDPRCompliance:
    def export_user_data(self, user_id):
        """Export all user data for GDPR compliance"""
        user = User.query.get(user_id)
        data = {
            'personal_info': {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,  # Automatically decrypted
                'last_name': user.last_name,
                'organization': user.organization,
                'created_at': user.created_at.isoformat()
            },
            'audit_logs': [log.to_dict() for log in user.audit_logs],
            'downloads': [dl.to_dict() for dl in user.downloads]
        }
        return data
    
    def anonymize_user_data(self, user_id):
        """Anonymize user data for deletion"""
        user = User.query.get(user_id)
        user.first_name = None
        user.last_name = None
        user.organization = None
        user.email = f"deleted_user_{user_id}@deleted.local"
        user.is_active = False
        db.session.commit()
```

### Audit Requirements

```python
# Comprehensive audit logging
@app.after_request
def log_request(response):
    """Log all requests for audit purposes"""
    if request.endpoint not in ['static', 'health']:
        audit_log = AuditLog(
            action_type=AuditActionType.VIEW,
            action_description=f"{request.method} {request.endpoint}",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            user_id=session.get('user_id'),
            success=200 <= response.status_code < 400,
            details={
                'method': request.method,
                'endpoint': request.endpoint,
                'status_code': response.status_code
            }
        )
        db.session.add(audit_log)
        db.session.commit()
    
    return response
```

## Emergency Procedures

### Security Incident Response

```python
# Emergency lockdown procedures
def emergency_lockdown():
    """Lock down application in case of security incident"""
    
    # Disable new logins
    app.config['MAINTENANCE_MODE'] = True
    
    # Invalidate all sessions
    # Implementation depends on session storage
    
    # Alert administrators
    send_emergency_alert("Security incident - Application locked down")
    
    # Log incident
    logger.critical("Emergency lockdown activated")

def enable_maintenance_mode():
    """Enable maintenance mode"""
    @app.before_request
    def maintenance_mode():
        if app.config.get('MAINTENANCE_MODE') and request.endpoint != 'maintenance':
            return render_template('maintenance.html'), 503
```

### Key Rotation Procedure

```python
def rotate_encryption_key():
    """Emergency key rotation procedure"""
    
    # Generate new key
    new_key = Fernet.generate_key()
    
    # Re-encrypt all data with new key
    users = User.query.all()
    for user in users:
        if user._first_name:
            # Decrypt with old key, encrypt with new key
            old_value = old_encryption_service.decrypt_field(user._first_name)
            user._first_name = new_encryption_service.encrypt_field(old_value)
    
    db.session.commit()
    
    # Update key storage
    save_new_master_key(new_key)
    
    logger.critical("Encryption key rotation completed")
```

## Conclusion

This security configuration guide provides comprehensive protection for the PanelMerge application. Implement all recommended security measures for production deployment and regularly review and update security configurations as threats evolve.

### Security Checklist Summary

- ✅ HTTPS enabled with modern TLS configuration
- ✅ Comprehensive security headers implemented
- ✅ Content Security Policy configured
- ✅ Rate limiting enabled
- ✅ Session security hardened
- ✅ File upload security implemented
- ✅ Database security configured
- ✅ Monitoring and alerting active
- ✅ Incident response procedures documented
- ✅ Compliance features implemented

Regular security assessments and penetration testing are recommended to maintain the highest security standards.
