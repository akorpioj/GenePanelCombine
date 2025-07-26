"""
Authentication Blueprint for PanelMerge
Handles user registration, login, logout, and role-based access control
"""

from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Import routes after blueprint creation to avoid circular imports
from . import routes
