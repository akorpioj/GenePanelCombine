"""
Audit Trail Service for PanelMerge
Provides comprehensive logging of user actions and system changes
"""

import json
import time
import datetime
from typing import Optional, Dict, Any, Union
from flask import request, session, current_app
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.models import db, AuditLog, AuditActionType

# Use Flask's logger
logger = logging.getLogger(__name__)

class AuditService:
    """Service class for managing audit trail logging"""
    
    @staticmethod
    def log_action(
        action_type: AuditActionType,
        action_description: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> Optional[AuditLog]:
        """
        Log an action to the audit trail
        
        Args:
            action_type: Type of action being performed
            action_description: Human-readable description of the action
            resource_type: Type of resource affected (e.g., 'panel', 'user')
            resource_id: ID of the affected resource
            old_values: Previous values before change
            new_values: New values after change
            details: Additional context/metadata
            success: Whether the action was successful
            error_message: Error message if action failed
            duration_ms: Duration of action in milliseconds
            user_id: Override user ID (uses current user if not provided)
            ip_address: Override IP address (uses request IP if not provided)
            
        Returns:
            AuditLog instance if successful, None if failed
        """
        try:
            # Get user information
            if user_id is not None:
                audit_user_id = user_id
                username = None  # Will be populated from database if needed
            elif current_user and current_user.is_authenticated:
                audit_user_id = current_user.id
                username = current_user.username
            else:
                audit_user_id = None
                username = None
            
            logger.info(f"🔍 AUDIT DEBUG: User info - audit_user_id: {audit_user_id}, username: {username}")
            
            # Get request information
            if ip_address is None:
                ip_address = AuditService._get_client_ip()
            
            user_agent = None
            session_id = None
            
            if request:
                user_agent = request.headers.get('User-Agent', '')[:500]  # Limit length
                session_id = session.get('_id') if session else None
            
            logger.info(f"🔍 AUDIT DEBUG: Request info - ip: {ip_address}, user_agent exists: {user_agent is not None}")
            
            # Create audit log entry
            audit_log = AuditLog(
                user_id=audit_user_id,
                username=username,
                action_type=action_type,
                action_description=action_description[:500],  # Limit length
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                old_values=json.dumps(old_values) if old_values else None,
                new_values=json.dumps(new_values) if new_values else None,
                details=json.dumps(details) if details else None,
                timestamp=datetime.datetime.now(),
                success=success,
                error_message=error_message[:1000] if error_message else None,
                duration_ms=duration_ms
            )
            
            logger.info(f"🔍 AUDIT DEBUG: Created audit_log object: {audit_log.action_type}, {audit_log.action_description}")
            
            db.session.add(audit_log)
            logger.info(f"🔍 AUDIT DEBUG: Added to session")
            
            db.session.commit()
            logger.info(f"🔍 AUDIT DEBUG: Committed to database, ID: {audit_log.id}")
            
            return audit_log
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to log audit action: {e}")
            db.session.rollback()
            return None
        except Exception as e:
            logger.error(f"Unexpected error logging audit action: {e}")
            return None
    
    @staticmethod
    def log_login(username: str, success: bool = True, error_message: Optional[str] = None):
        """Log a login attempt"""
        return AuditService.log_action(
            action_type=AuditActionType.LOGIN,
            action_description=f"User '{username}' login attempt",
            resource_type="user",
            resource_id=username,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    def log_logout(username: str):
        """Log a logout action"""
        from flask import current_app
        try:
            current_app.logger.info(f"🔍 AUDIT DEBUG: Starting log_logout for: {username}")
            result = AuditService.log_action(
                action_type=AuditActionType.LOGOUT,
                action_description=f"User '{username}' logged out",
                resource_type="user",
                resource_id=username
            )
            current_app.logger.info(f"🔍 AUDIT DEBUG: log_action returned: {result}")
            if result:
                current_app.logger.info(f"🔍 AUDIT DEBUG: Audit log created with ID: {result.id}")
            return result
        except Exception as e:
            current_app.logger.error(f"🔍 AUDIT DEBUG: Exception in log_logout: {e}")
            import traceback
            current_app.logger.error(f"🔍 AUDIT DEBUG: Traceback: {traceback.format_exc()}")
            return None
    
    @staticmethod
    def log_registration(username: str, email: str, success: bool = True, error_message: Optional[str] = None):
        """Log a user registration"""
        return AuditService.log_action(
            action_type=AuditActionType.REGISTER,
            action_description=f"New user registration: '{username}' ({email})",
            resource_type="user",
            resource_id=username,
            new_values={"username": username, "email": email},
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    def log_profile_update(user_id: int, username: str, old_data: Dict[str, Any], new_data: Dict[str, Any]):
        """Log a profile update"""
        return AuditService.log_action(
            action_type=AuditActionType.PROFILE_UPDATE,
            action_description=f"Profile updated for user '{username}'",
            resource_type="user",
            resource_id=str(user_id),
            old_values=old_data,
            new_values=new_data
        )
    
    @staticmethod
    def log_password_change(username: str, success: bool = True):
        """Log a password change"""
        return AuditService.log_action(
            action_type=AuditActionType.PASSWORD_CHANGE,
            action_description=f"Password changed for user '{username}'",
            resource_type="user",
            resource_id=username,
            success=success
        )
    
    @staticmethod
    def log_panel_download(panel_ids: str, list_types: str, gene_count: int, file_name: str = None):
        """Log a panel download"""
        details = {
            "panel_ids": panel_ids,
            "list_types": list_types,
            "gene_count": gene_count
        }
        if file_name:
            details["file_name"] = file_name
            
        return AuditService.log_action(
            action_type=AuditActionType.PANEL_DOWNLOAD,
            action_description=f"Downloaded gene list with {gene_count} genes from panels: {panel_ids}",
            resource_type="panel",
            resource_id=panel_ids,
            details=details
        )
    
    @staticmethod
    def log_panel_upload(file_name: str, gene_count: int, success: bool = True, error_message: Optional[str] = None):
        """Log a panel upload"""
        return AuditService.log_action(
            action_type=AuditActionType.PANEL_UPLOAD,
            action_description=f"Uploaded panel file '{file_name}' with {gene_count} genes",
            resource_type="panel",
            resource_id=file_name,
            details={"file_name": file_name, "gene_count": gene_count},
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    def log_search(search_term: str, results_count: int = None):
        """Log a search action"""
        details = {"search_term": search_term}
        if results_count is not None:
            details["results_count"] = results_count
            
        return AuditService.log_action(
            action_type=AuditActionType.SEARCH,
            action_description=f"Search performed: '{search_term}'",
            resource_type="search",
            resource_id=search_term,
            details=details
        )
    
    @staticmethod
    def log_admin_action(action_description: str, target_user_id: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        """Log an admin action"""
        return AuditService.log_action(
            action_type=AuditActionType.ADMIN_ACTION,
            action_description=action_description,
            resource_type="admin",
            resource_id=str(target_user_id) if target_user_id else None,
            details=details
        )
    
    @staticmethod
    def log_cache_clear(cache_type: str = "all"):
        """Log cache clearing"""
        return AuditService.log_action(
            action_type=AuditActionType.CACHE_CLEAR,
            action_description=f"Cache cleared: {cache_type}",
            resource_type="cache",
            resource_id=cache_type
        )
    
    @staticmethod
    def log_error(error_description: str, error_message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        """Log an error"""
        return AuditService.log_action(
            action_type=AuditActionType.ERROR,
            action_description=error_description,
            resource_type=resource_type,
            resource_id=resource_id,
            success=False,
            error_message=error_message
        )
    
    @staticmethod
    def log_panel_delete(panel_id: str, panel_name: str = None):
        """Log a panel deletion"""
        description = f"Deleted panel '{panel_name}'" if panel_name else f"Deleted panel ID: {panel_id}"
        return AuditService.log_action(
            action_type=AuditActionType.PANEL_DELETE,
            action_description=description,
            resource_type="panel",
            resource_id=panel_id,
            details={"panel_id": panel_id, "panel_name": panel_name}
        )
    
    @staticmethod
    def log_view(resource_type: str, resource_id: str, description: str, details: Optional[Dict[str, Any]] = None):
        """Log a view action"""
        return AuditService.log_action(
            action_type=AuditActionType.VIEW,
            action_description=description,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details
        )
    
    @staticmethod
    def log_user_create(username: str, email: str, role: str, created_by_admin: bool = False):
        """Log user creation by admin"""
        action_type = AuditActionType.USER_CREATE if created_by_admin else AuditActionType.REGISTER
        return AuditService.log_action(
            action_type=action_type,
            action_description=f"Created new user: '{username}' ({email}) with role {role}",
            resource_type="user",
            resource_id=username,
            new_values={"username": username, "email": email, "role": role}
        )
    
    @staticmethod
    def log_user_update(user_id: int, username: str, changes: Dict[str, Any], old_values: Dict[str, Any] = None):
        """Log user updates by admin"""
        return AuditService.log_action(
            action_type=AuditActionType.USER_UPDATE,
            action_description=f"Updated user '{username}': {', '.join(changes.keys())}",
            resource_type="user",
            resource_id=str(user_id),
            old_values=old_values,
            new_values=changes
        )
    
    @staticmethod
    def log_user_delete(user_id: int, username: str):
        """Log user deletion by admin"""
        return AuditService.log_action(
            action_type=AuditActionType.USER_DELETE,
            action_description=f"Deleted user '{username}'",
            resource_type="user",
            resource_id=str(user_id),
            details={"deleted_username": username}
        )
    
    @staticmethod
    def log_role_change(user_id: int, username: str, old_role: str, new_role: str):
        """Log role changes"""
        return AuditService.log_action(
            action_type=AuditActionType.ROLE_CHANGE,
            action_description=f"Changed role for user '{username}' from {old_role} to {new_role}",
            resource_type="user",
            resource_id=str(user_id),
            old_values={"role": old_role},
            new_values={"role": new_role}
        )
    
    @staticmethod
    def log_data_export(export_type: str, record_count: int, file_name: str = None):
        """Log data export operations"""
        details = {
            "export_type": export_type,
            "record_count": record_count
        }
        if file_name:
            details["file_name"] = file_name
            
        return AuditService.log_action(
            action_type=AuditActionType.DATA_EXPORT,
            action_description=f"Exported {record_count} {export_type} records",
            resource_type="export",
            resource_id=export_type,
            details=details
        )
    
    @staticmethod
    def log_config_change(config_key: str, old_value: Any, new_value: Any):
        """Log configuration changes"""
        return AuditService.log_action(
            action_type=AuditActionType.CONFIG_CHANGE,
            action_description=f"Changed configuration '{config_key}'",
            resource_type="config",
            resource_id=config_key,
            old_values={config_key: old_value},
            new_values={config_key: new_value}
        )

    # Enhanced Security Audit Methods
    
    @staticmethod
    def log_security_violation(violation_type: str, description: str, severity: str = "HIGH", details: Optional[Dict[str, Any]] = None):
        """Log security violations and potential threats"""
        return AuditService.log_action(
            action_type=AuditActionType.SECURITY_VIOLATION,
            action_description=f"Security violation: {description}",
            success=False,
            details={
                "violation_type": violation_type,
                "severity": severity,
                "timestamp": datetime.datetime.now().isoformat(),
                **(details or {})
            }
        )

    @staticmethod
    def log_access_denied(resource_type: str, resource_id: str, reason: str, requested_action: str = None):
        """Log access denied events"""
        return AuditService.log_action(
            action_type=AuditActionType.ACCESS_DENIED,
            action_description=f"Access denied to {resource_type} {resource_id}: {reason}",
            resource_type=resource_type,
            resource_id=resource_id,
            success=False,
            details={
                "reason": reason,
                "requested_action": requested_action,
                "user_agent": request.headers.get('User-Agent') if request else None
            }
        )

    @staticmethod
    def log_privilege_escalation(target_privilege: str, source_privilege: str = None, success: bool = True):
        """Log privilege escalation attempts"""
        return AuditService.log_action(
            action_type=AuditActionType.PRIVILEGE_ESCALATION,
            action_description=f"Privilege escalation from {source_privilege or 'unknown'} to {target_privilege}",
            success=success,
            details={
                "source_privilege": source_privilege,
                "target_privilege": target_privilege,
                "escalation_method": "session_service",
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

    @staticmethod
    def log_suspicious_activity(activity_type: str, description: str, risk_score: int = 50, details: Optional[Dict[str, Any]] = None):
        """Log suspicious user activity that may indicate security threats"""
        return AuditService.log_action(
            action_type=AuditActionType.SUSPICIOUS_ACTIVITY,
            action_description=f"Suspicious activity detected: {description}",
            details={
                "activity_type": activity_type,
                "risk_score": risk_score,
                "detection_method": "automated",
                "requires_review": risk_score >= 70,
                **(details or {})
            }
        )

    @staticmethod
    def log_brute_force_attempt(target_username: str, attempt_count: int, time_window: str, source_ip: str = None):
        """Log brute force attack attempts"""
        return AuditService.log_action(
            action_type=AuditActionType.BRUTE_FORCE_ATTEMPT,
            action_description=f"Brute force attempt against user '{target_username}': {attempt_count} attempts in {time_window}",
            success=False,
            details={
                "target_username": target_username,
                "attempt_count": attempt_count,
                "time_window": time_window,
                "source_ip": source_ip or AuditService._get_client_ip(),
                "detection_time": datetime.datetime.now().isoformat(),
                "threat_level": "HIGH" if attempt_count >= 10 else "MEDIUM"
            }
        )

    @staticmethod
    def log_account_lockout(username: str, reason: str, lockout_duration: str = None, automatic: bool = True):
        """Log account lockout events"""
        return AuditService.log_action(
            action_type=AuditActionType.ACCOUNT_LOCKOUT,
            action_description=f"Account locked: {username} - {reason}",
            details={
                "username": username,
                "reason": reason,
                "lockout_duration": lockout_duration,
                "automatic": automatic,
                "lockout_time": datetime.datetime.now().isoformat(),
                "admin_action_required": not automatic
            }
        )

    @staticmethod
    def log_password_reset(username: str, method: str, success: bool = True, initiated_by: str = "user"):
        """Log password reset events"""
        return AuditService.log_action(
            action_type=AuditActionType.PASSWORD_RESET,
            action_description=f"Password reset for {username} via {method}",
            success=success,
            details={
                "username": username,
                "reset_method": method,  # email, admin, security_questions, etc.
                "initiated_by": initiated_by,
                "reset_time": datetime.datetime.now().isoformat(),
                "verification_required": method == "email"
            }
        )

    @staticmethod
    def log_api_access(endpoint: str, method: str, status_code: int, response_time_ms: int = None, api_key_used: bool = False):
        """Log API access for security monitoring"""
        return AuditService.log_action(
            action_type=AuditActionType.API_ACCESS,
            action_description=f"API access: {method} {endpoint} -> {status_code}",
            success=200 <= status_code < 400,
            details={
                "endpoint": endpoint,
                "http_method": method,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "api_key_used": api_key_used,
                "user_agent": request.headers.get('User-Agent') if request else None,
                "content_length": request.content_length if request else None
            }
        )

    @staticmethod
    def log_file_access(file_path: str, access_type: str, success: bool = True, file_size: int = None):
        """Log file access for security monitoring"""
        return AuditService.log_action(
            action_type=AuditActionType.FILE_ACCESS,
            action_description=f"File {access_type}: {file_path}",
            resource_type="file",
            resource_id=file_path,
            success=success,
            details={
                "file_path": file_path,
                "access_type": access_type,  # read, write, delete, download, upload
                "file_size": file_size,
                "access_time": datetime.datetime.now().isoformat()
            }
        )

    @staticmethod
    def log_data_breach_attempt(breach_type: str, target_data: str, blocked: bool = True, details: Optional[Dict[str, Any]] = None):
        """Log potential data breach attempts"""
        return AuditService.log_action(
            action_type=AuditActionType.DATA_BREACH_ATTEMPT,
            action_description=f"Data breach attempt: {breach_type} targeting {target_data}",
            success=False,
            details={
                "breach_type": breach_type,
                "target_data": target_data,
                "blocked": blocked,
                "severity": "CRITICAL",
                "requires_investigation": True,
                "alert_sent": True,
                **(details or {})
            }
        )

    @staticmethod
    def log_compliance_event(compliance_type: str, event_description: str, compliant: bool = True, regulation: str = None):
        """Log compliance-related events (GDPR, HIPAA, etc.)"""
        return AuditService.log_action(
            action_type=AuditActionType.COMPLIANCE_EVENT,
            action_description=f"Compliance event ({compliance_type}): {event_description}",
            success=compliant,
            details={
                "compliance_type": compliance_type,
                "regulation": regulation,
                "compliant": compliant,
                "event_time": datetime.datetime.now().isoformat(),
                "requires_review": not compliant
            }
        )

    @staticmethod
    def log_system_security(event_type: str, description: str, severity: str = "INFO", 
                           system_component: str = None, details: Optional[Dict[str, Any]] = None):
        """Log system-level security events"""
        audit_details = {
            "event_type": event_type,
            "severity": severity,
            "system_component": system_component,
            "event_time": datetime.datetime.now().isoformat(),
            "auto_generated": True
        }
        
        # Merge additional details if provided
        if details:
            audit_details.update(details)
        
        return AuditService.log_action(
            action_type=AuditActionType.SYSTEM_SECURITY,
            action_description=f"System security event: {description}",
            details=audit_details
        )

    @staticmethod
    def log_mfa_event(event_type: str, success: bool, method: str = None, details: Optional[Dict[str, Any]] = None):
        """Log multi-factor authentication events"""
        return AuditService.log_action(
            action_type=AuditActionType.MFA_EVENT,
            action_description=f"MFA {event_type}: {'Success' if success else 'Failed'}",
            success=success,
            details={
                "event_type": event_type,  # setup, verification, bypass, disable
                "method": method,  # sms, email, app, hardware_token
                "mfa_time": datetime.datetime.now().isoformat(),
                **(details or {})
            }
        )
    
    @staticmethod
    def _get_client_ip() -> str:
        """Get the client's IP address from the request"""
        if not request:
            return "unknown"
            
        # Check for forwarded headers (when behind proxy/load balancer)
        forwarded_ips = request.headers.get('X-Forwarded-For')
        if forwarded_ips:
            # Take the first IP in the chain
            return forwarded_ips.split(',')[0].strip()
        
        # Check other common headers
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fall back to remote address
        return request.remote_addr or "unknown"

class AuditContext:
    """Context manager for timing actions and automatic audit logging"""
    
    def __init__(self, action_type: AuditActionType, action_description: str, **kwargs):
        self.action_type = action_type
        self.action_description = action_description
        self.kwargs = kwargs
        self.start_time = None
        self.success = True
        self.error_message = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = int((time.time() - self.start_time) * 1000) if self.start_time else None
        
        if exc_type is not None:
            self.success = False
            self.error_message = str(exc_val)
        
        AuditService.log_action(
            action_type=self.action_type,
            action_description=self.action_description,
            success=self.success,
            error_message=self.error_message,
            duration_ms=duration_ms,
            **self.kwargs
        )
        
        # Don't suppress exceptions
        return False

def audit_action(action_type: AuditActionType, description: str, **kwargs):
    """Decorator for automatically auditing function calls"""
    def decorator(func):
        def wrapper(*args, **func_kwargs):
            with AuditContext(action_type, description, **kwargs):
                return func(*args, **func_kwargs)
        return wrapper
    return decorator
