# In my_app/admin/__init__.py
from flask import Blueprint

# Define the Blueprint object
# 'admin' is the name of the Blueprint, used for namespacing in url_for() (e.g., url_for('admin.login'))
# __name__ is the import name, helping Flask locate resources relative to this package.
# template_folder='templates' means this Blueprint will look for its templates in a 'templates'
# subdirectory within the 'admin' package (i.e., my_app/admin/templates/).
# url_prefix='/auth' means all routes in this blueprint will be prefixed with '/auth'.
admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin/', url_prefix='/')

# Import routes after Blueprint definition to avoid circular import issues
# This line makes the routes defined in routes.py part of the auth_bp
from . import routes
