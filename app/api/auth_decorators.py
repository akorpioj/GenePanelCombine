"""
Custom authentication decorators for API endpoints
"""

from functools import wraps
from flask import jsonify, current_app
from flask_login import current_user
from flask_restx import abort


def api_login_required(f):
    """
    Custom login required decorator for API endpoints that returns JSON errors
    instead of redirecting to login page
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            # Return JSON error instead of redirect
            abort(401, "Authentication required")
        
        # Check if user is active
        if hasattr(current_user, 'is_active') and not current_user.is_active:
            abort(401, "Account is deactivated")
        
        return f(*args, **kwargs)
    return decorated_function


def api_admin_required(f):
    """
    Decorator that requires the user to be authenticated and have admin privileges
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401, "Authentication required")
        
        if hasattr(current_user, 'is_active') and not current_user.is_active:
            abort(401, "Account is deactivated")
        
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin():
            abort(403, "Admin privileges required")
        
        return f(*args, **kwargs)
    return decorated_function
