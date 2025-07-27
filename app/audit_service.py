"""
Audit Trail Service for PanelMerge
Provides comprehensive logging of user actions and system changes
"""

import json
import time
from datetime import datetime
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
                timestamp=datetime.utcnow(),
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
