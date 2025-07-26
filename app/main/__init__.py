# In my_app/admin/__init__.py
from flask import Blueprint

# Define the Blueprint object
# 'main' is the name of the Blueprint, used for namespacing in url_for() (e.g., url_for('main.generate'))
# __name__ is the import name, helping Flask locate resources relative to this package.
# template_folder='templates' means this Blueprint will look for its templates in a 'templates'
# subdirectory within the 'main' package (i.e., my_app/templates/main).
# url_prefix='/main' means all routes in this blueprint will be prefixed with '/main'.
main_bp = Blueprint('main', __name__, template_folder='../templates/main', url_prefix='/')

# Import routes after Blueprint definition to avoid circular import issues
# This line makes the routes defined in routes.py part of the auth_bp
from . import routes

# Add context processor for permission utilities
@main_bp.app_context_processor
def inject_permission_utils():
    """Make permission utility functions available in templates"""
    from .utils import user_can_upload, user_can_moderate, user_is_admin, get_user_display_name, get_user_role_display
    return {
        'user_can_upload': user_can_upload,
        'user_can_moderate': user_can_moderate, 
        'user_is_admin': user_is_admin,
        'get_user_display_name': get_user_display_name,
        'get_user_role_display': get_user_role_display
    }