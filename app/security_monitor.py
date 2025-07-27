"""
Security Monitoring Service for PanelMerge
Provides automated security event detection and logging
"""

import time
import re
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional
from flask import request, session, current_app, g
from flask_login import current_user
import logging

from app.audit_service import AuditService

logger = logging.getLogger(__name__)

class SecurityMonitor:
    """Security monitoring and threat detection service"""
    
    def __init__(self):
        self.failed_login_attempts = defaultdict(list)
        self.suspicious_ips = set()
        self.rate_limit_violations = defaultdict(list)
        self.security_rules = self._load_security_rules()
    
    def _load_security_rules(self) -> Dict:
        """Load security monitoring rules"""
        return {
            'max_failed_logins': 5,
            'failed_login_window': 300,  # 5 minutes
            'max_requests_per_minute': 100,
            'suspicious_user_agents': [
                'sqlmap', 'nikto', 'burp', 'nessus', 'openvas',
                'python-requests', 'curl', 'wget'
            ],
            'blocked_file_extensions': [
                '.php', '.asp', '.jsp', '.cgi', '.sh', '.py', '.pl'
            ],
            'sensitive_paths': [
                '/admin', '/config', '/backup', '/.env', '/database'
            ]
        }
    
    def before_request(self):
        """Security checks before each request"""
        try:
            # Record request start time for performance monitoring
            g.request_start_time = time.time()
            
            # Get client information
            client_ip = self._get_client_ip()
            user_agent = request.headers.get('User-Agent', '')
            
            # Check for blocked IPs
            if self._is_ip_blocked(client_ip):
                AuditService.log_security_violation(
                    violation_type="BLOCKED_IP_ACCESS",
                    description=f"Access attempt from blocked IP: {client_ip}",
                    severity="HIGH",
                    details={
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "endpoint": request.endpoint,
                        "blocked": True
                    }
                )
                return "Access denied", 403
            
            # Check for suspicious user agents
            if self._is_suspicious_user_agent(user_agent):
                AuditService.log_suspicious_activity(
                    activity_type="SUSPICIOUS_USER_AGENT",
                    description=f"Suspicious user agent detected: {user_agent[:100]}",
                    risk_score=60,
                    details={
                        "user_agent": user_agent,
                        "client_ip": client_ip,
                        "endpoint": request.endpoint
                    }
                )
            
            # Check for path traversal attempts
            if self._check_path_traversal():
                AuditService.log_security_violation(
                    violation_type="PATH_TRAVERSAL",
                    description="Path traversal attempt detected",
                    severity="HIGH",
                    details={
                        "request_path": request.path,
                        "query_string": str(request.query_string),
                        "client_ip": client_ip
                    }
                )
                return "Invalid request", 400
            
            # Check for SQL injection patterns
            if self._check_sql_injection():
                AuditService.log_security_violation(
                    violation_type="SQL_INJECTION",
                    description="Potential SQL injection attempt detected",
                    severity="CRITICAL",
                    details={
                        "request_path": request.path,
                        "query_params": dict(request.args),
                        "client_ip": client_ip,
                        "user_agent": user_agent
                    }
                )
                return "Invalid request", 400
            
            # Rate limiting check
            if self._check_rate_limit(client_ip):
                AuditService.log_suspicious_activity(
                    activity_type="RATE_LIMIT_VIOLATION",
                    description=f"Rate limit exceeded for IP: {client_ip}",
                    risk_score=40,
                    details={
                        "client_ip": client_ip,
                        "request_count": len(self.rate_limit_violations[client_ip]),
                        "time_window": "1 minute"
                    }
                )
        
        except Exception as e:
            logger.error(f"Security monitoring error: {e}")
            # Don't block requests due to monitoring errors
            pass
    
    def after_request(self, response):
        """Security monitoring after request completion"""
        try:
            # Calculate request duration
            if hasattr(g, 'request_start_time'):
                duration_ms = int((time.time() - g.request_start_time) * 1000)
                
                # Log slow requests as potential DoS
                if duration_ms > 10000:  # 10 seconds
                    AuditService.log_suspicious_activity(
                        activity_type="SLOW_REQUEST",
                        description=f"Unusually slow request: {duration_ms}ms",
                        risk_score=30,
                        details={
                            "duration_ms": duration_ms,
                            "endpoint": request.endpoint,
                            "client_ip": self._get_client_ip()
                        }
                    )
            
            # Monitor failed authentication attempts
            if response.status_code == 401:
                self._handle_failed_auth()
            
            # Monitor access denied events
            elif response.status_code == 403:
                self._handle_access_denied()
            
            # Log high-risk status codes
            elif response.status_code in [500, 502, 503]:
                AuditService.log_system_security(
                    event_type="ERROR_RESPONSE",
                    description=f"Server error response: {response.status_code}",
                    severity="ERROR",
                    system_component="web_server"
                )
        
        except Exception as e:
            logger.error(f"Post-request security monitoring error: {e}")
        
        return response
    
    def _get_client_ip(self) -> str:
        """Get the real client IP address"""
        # Check for forwarded headers (when behind proxy/load balancer)
        for header in ['X-Forwarded-For', 'X-Real-IP', 'X-Forwarded-Host']:
            if header in request.headers:
                ip = request.headers[header].split(',')[0].strip()
                if ip:
                    return ip
        return request.remote_addr or 'unknown'
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is in blocked list"""
        # In production, this would check against a database or Redis set
        return ip in self.suspicious_ips
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious"""
        if not user_agent:
            return True
        
        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in self.security_rules['suspicious_user_agents'])
    
    def _check_path_traversal(self) -> bool:
        """Check for path traversal attempts"""
        path = request.path
        query_string = str(request.query_string)
        
        # Common path traversal patterns
        traversal_patterns = [
            '../', '..\\', '%2e%2e/', '%2e%2e\\',
            '..%2f', '..%5c', '%252e%252e%252f'
        ]
        
        full_request = path + query_string
        return any(pattern in full_request.lower() for pattern in traversal_patterns)
    
    def _check_sql_injection(self) -> bool:
        """Check for SQL injection patterns"""
        # Check query parameters and form data
        data_to_check = []
        
        # Add query parameters
        for value in request.args.values():
            data_to_check.append(value.lower())
        
        # Add form data
        if request.form:
            for value in request.form.values():
                data_to_check.append(value.lower())
        
        # Common SQL injection patterns
        sql_patterns = [
            "' or 1=1", "' or '1'='1", "' union select",
            "'; drop table", "'; delete from", "' and 1=1",
            "' having 1=1", "' group by", "' order by",
            "'; exec", "'; execute", "' waitfor delay"
        ]
        
        for data in data_to_check:
            if any(pattern in data for pattern in sql_patterns):
                return True
        
        return False
    
    def _check_rate_limit(self, ip: str) -> bool:
        """Check if IP has exceeded rate limits"""
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Clean old entries
        self.rate_limit_violations[ip] = [
            timestamp for timestamp in self.rate_limit_violations[ip]
            if timestamp > minute_ago
        ]
        
        # Add current request
        self.rate_limit_violations[ip].append(current_time)
        
        # Check if limit exceeded
        return len(self.rate_limit_violations[ip]) > self.security_rules['max_requests_per_minute']
    
    def _handle_failed_auth(self):
        """Handle failed authentication attempts"""
        client_ip = self._get_client_ip()
        current_time = time.time()
        
        # Add failed attempt
        self.failed_login_attempts[client_ip].append(current_time)
        
        # Clean old attempts (older than window)
        window_start = current_time - self.security_rules['failed_login_window']
        self.failed_login_attempts[client_ip] = [
            timestamp for timestamp in self.failed_login_attempts[client_ip]
            if timestamp > window_start
        ]
        
        attempt_count = len(self.failed_login_attempts[client_ip])
        
        # Check for brute force
        if attempt_count >= self.security_rules['max_failed_logins']:
            AuditService.log_brute_force_attempt(
                target_username=request.form.get('username_or_email', 'unknown'),
                attempt_count=attempt_count,
                time_window=f"{self.security_rules['failed_login_window']} seconds",
                source_ip=client_ip
            )
            
            # Add IP to suspicious list
            self.suspicious_ips.add(client_ip)
    
    def _handle_access_denied(self):
        """Handle access denied events"""
        AuditService.log_access_denied(
            resource_type="endpoint",
            resource_id=request.endpoint or request.path,
            reason="Insufficient privileges",
            requested_action=request.method
        )
    
    def check_file_upload_security(self, filename: str, file_content: bytes = None) -> bool:
        """Check uploaded file for security issues"""
        try:
            # Check file extension
            if any(filename.lower().endswith(ext) for ext in self.security_rules['blocked_file_extensions']):
                AuditService.log_security_violation(
                    violation_type="MALICIOUS_FILE_UPLOAD",
                    description=f"Attempt to upload blocked file type: {filename}",
                    severity="HIGH",
                    details={
                        "filename": filename,
                        "file_extension": filename.split('.')[-1] if '.' in filename else 'none',
                        "blocked": True
                    }
                )
                return False
            
            # Check for suspicious content if provided
            if file_content:
                # Check for script tags or PHP code
                content_str = file_content.decode('utf-8', errors='ignore').lower()
                suspicious_patterns = [
                    '<script', '<?php', '<%', 'eval(', 'exec(',
                    'system(', 'shell_exec', 'file_get_contents'
                ]
                
                if any(pattern in content_str for pattern in suspicious_patterns):
                    AuditService.log_security_violation(
                        violation_type="MALICIOUS_FILE_CONTENT",
                        description=f"Malicious content detected in uploaded file: {filename}",
                        severity="CRITICAL",
                        details={
                            "filename": filename,
                            "content_scan": "failed",
                            "blocked": True
                        }
                    )
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"File security check error: {e}")
            # Default to blocking on error
            return False
    
    def log_data_access(self, data_type: str, record_count: int = None, sensitive: bool = False):
        """Log data access events"""
        if sensitive or record_count and record_count > 1000:
            AuditService.log_compliance_event(
                compliance_type="DATA_ACCESS",
                event_description=f"Access to {data_type} data ({record_count} records)",
                compliant=True,
                regulation="GDPR"
            )
    
    def detect_anomalous_behavior(self, user_id: int, action: str, context: Dict = None):
        """Detect anomalous user behavior patterns"""
        # This is a simplified example - in production you'd use ML models
        try:
            current_time = datetime.utcnow()
            
            # Check for unusual timing (e.g., access outside normal hours)
            if current_time.hour < 6 or current_time.hour > 22:
                AuditService.log_suspicious_activity(
                    activity_type="OFF_HOURS_ACCESS",
                    description=f"User {user_id} performing {action} outside normal hours",
                    risk_score=30,
                    details={
                        "user_id": user_id,
                        "action": action,
                        "access_time": current_time.isoformat(),
                        **(context or {})
                    }
                )
            
            # Check for rapid successive actions
            # This would require storing recent actions in cache/database
            
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")


# Global security monitor instance
security_monitor = SecurityMonitor()


def init_security_monitoring(app):
    """Initialize security monitoring for the Flask app"""
    
    @app.before_request
    def before_request_security():
        return security_monitor.before_request()
    
    @app.after_request
    def after_request_security(response):
        return security_monitor.after_request(response)
    
    # Log system startup
    AuditService.log_system_security(
        event_type="SYSTEM_STARTUP",
        description="Security monitoring system initialized",
        severity="INFO",
        system_component="security_monitor"
    )
    
    logger.info("Security monitoring initialized")
    return security_monitor
