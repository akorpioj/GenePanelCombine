"""
Security Service for PanelMerge Application

Provides comprehensive security features:
- HTTPS enforcement
- Security headers
- Content Security Policy
- Session security
- Rate limiting protection
"""

import logging
from flask import request, redirect, url_for, session, make_response
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps
import secrets
import hashlib
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class SecurityService:
    """
    Centralized security service for the application.
    
    Provides methods for:
    - HTTPS enforcement
    - Security headers
    - Content Security Policy
    - Session security enhancements
    """
    
    def __init__(self):
        self.require_https = False
        self.hsts_max_age = 31536000  # 1 year
        self.session_timeout = 3600   # 1 hour
        self.max_content_length = 16 * 1024 * 1024  # 16MB
        self._rate_limit_storage = {}
        
    def init_app(self, app):
        """Initialize security service with Flask app"""
        self.require_https = app.config.get('REQUIRE_HTTPS', False)
        self.hsts_max_age = app.config.get('HSTS_MAX_AGE', 31536000)
        self.session_timeout = app.config.get('SESSION_TIMEOUT', 3600)
        
        # Configure secure session settings
        app.config.update(
            SESSION_COOKIE_SECURE=self.require_https,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax',
            PERMANENT_SESSION_LIFETIME=self.session_timeout,
            MAX_CONTENT_LENGTH=self.max_content_length
        )
        
        # Add proxy fix for proper IP detection behind reverse proxies
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
        
        # Register security middleware
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
        logger.info("Security service initialized")
    
    def _before_request(self):
        """Handle security checks before each request"""
        # HTTPS enforcement
        if self.require_https and not request.is_secure:
            if request.method == 'GET':
                # Redirect GET requests to HTTPS
                url = request.url.replace('http://', 'https://', 1)
                return redirect(url, code=301)
            else:
                # Reject non-GET requests over HTTP
                return "HTTPS required", 400
        
        # Session security
        self._check_session_security()
        
        # Rate limiting
        if self._check_rate_limit():
            return "Too many requests", 429
    
    def _after_request(self, response):
        """Add security headers to response"""
        # Security headers
        self._add_security_headers(response)
        
        # Content Security Policy
        self._add_csp_header(response)
        
        # HSTS header for HTTPS
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = f'max-age={self.hsts_max_age}; includeSubDomains'
        
        return response
    
    def _add_security_headers(self, response):
        """Add comprehensive security headers"""
        headers = {
            # Prevent MIME type sniffing
            'X-Content-Type-Options': 'nosniff',
            
            # Enable XSS protection
            'X-XSS-Protection': '1; mode=block',
            
            # Prevent clickjacking
            'X-Frame-Options': 'DENY',
            
            # Referrer policy
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            
            # Feature policy
            'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=()',
            
            # Remove server information
            'Server': 'PanelMerge',
            
            # Cache control for sensitive pages
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
        for header, value in headers.items():
            response.headers[header] = value
    
    def _add_csp_header(self, response):
        """Add Content Security Policy header"""
        # Define CSP directives
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' https://panelapp.genomicsengland.co.uk",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        
        csp_header = "; ".join(csp_directives)
        response.headers['Content-Security-Policy'] = csp_header
    
    def _check_session_security(self):
        """Enhanced session security checks"""
        if 'user_id' in session:
            # Check session timeout
            last_activity = session.get('last_activity')
            if last_activity:
                if time.time() - last_activity > self.session_timeout:
                    session.clear()
                    logger.info("Session expired due to inactivity")
                    return
            
            # Update last activity
            session['last_activity'] = time.time()
            
            # Session fixation protection
            if 'session_created' not in session:
                session['session_created'] = time.time()
                session['csrf_token'] = secrets.token_urlsafe(32)
            
            # Check for session hijacking
            user_agent_hash = hashlib.sha256(
                request.headers.get('User-Agent', '').encode()
            ).hexdigest()[:16]
            
            stored_ua_hash = session.get('user_agent_hash')
            if stored_ua_hash and stored_ua_hash != user_agent_hash:
                session.clear()
                logger.warning("Potential session hijacking detected")
                return
            
            session['user_agent_hash'] = user_agent_hash
    
    def _check_rate_limit(self) -> bool:
        """Simple rate limiting based on IP address"""
        client_ip = self.get_client_ip()
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_rate_limit_storage(current_time)
        
        # Check current IP
        if client_ip in self._rate_limit_storage:
            requests = self._rate_limit_storage[client_ip]
            # Allow 100 requests per minute
            recent_requests = [ts for ts in requests if current_time - ts < 60]
            
            if len(recent_requests) >= 100:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return True
            
            # Update request list
            recent_requests.append(current_time)
            self._rate_limit_storage[client_ip] = recent_requests
        else:
            self._rate_limit_storage[client_ip] = [current_time]
        
        return False
    
    def _cleanup_rate_limit_storage(self, current_time: float):
        """Clean up old rate limit entries"""
        # Remove entries older than 5 minutes
        cutoff_time = current_time - 300
        
        for ip in list(self._rate_limit_storage.keys()):
            self._rate_limit_storage[ip] = [
                ts for ts in self._rate_limit_storage[ip] 
                if ts > cutoff_time
            ]
            
            # Remove empty entries
            if not self._rate_limit_storage[ip]:
                del self._rate_limit_storage[ip]
    
    def get_client_ip(self) -> str:
        """Get the real client IP address, considering proxies"""
        # Check for proxy headers (in order of preference)
        for header in ['X-Forwarded-For', 'X-Real-IP', 'X-Forwarded-Host']:
            if header in request.headers:
                # Take the first IP in case of comma-separated list
                ip = request.headers[header].split(',')[0].strip()
                if ip:
                    return ip
        
        return request.remote_addr or 'unknown'
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token for forms"""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_urlsafe(32)
        return session['csrf_token']
    
    def validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token"""
        return session.get('csrf_token') == token
    
    def secure_filename(self, filename: str) -> str:
        """Create a secure filename for file uploads"""
        import re
        import unicodedata
        
        # Normalize unicode characters
        filename = unicodedata.normalize('NFKD', filename)
        
        # Remove non-ASCII characters
        filename = filename.encode('ascii', 'ignore').decode('ascii')
        
        # Remove or replace dangerous characters
        filename = re.sub(r'[^\w\s.-]', '', filename).strip()
        
        # Replace spaces with underscores
        filename = re.sub(r'\s+', '_', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename or 'unnamed_file'
    
    def log_security_event(self, event_type: str, details: Dict = None):
        """Log security-related events"""
        log_data = {
            'event_type': event_type,
            'ip_address': self.get_client_ip(),
            'user_agent': request.headers.get('User-Agent', ''),
            'url': request.url,
            'method': request.method,
            'details': details or {}
        }
        
        logger.warning(f"Security event: {event_type} - {log_data}")


# Decorators for enhanced security
def require_https(f):
    """Decorator to require HTTPS for specific routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_secure:
            return redirect(request.url.replace('http://', 'https://', 1), code=301)
        return f(*args, **kwargs)
    return decorated_function


def csrf_protect(f):
    """Decorator to protect routes against CSRF attacks"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            if not security_service.validate_csrf_token(token):
                security_service.log_security_event('csrf_token_mismatch')
                return "CSRF token mismatch", 403
        return f(*args, **kwargs)
    return decorated_function


def rate_limit(requests_per_minute: int = 60):
    """Decorator for rate limiting specific routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This would integrate with the main rate limiting system
            # For now, using the global rate limiter
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Global security service instance
security_service = SecurityService()


def init_security(app):
    """Initialize security service with Flask app"""
    security_service.init_app(app)
    return security_service
