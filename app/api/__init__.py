"""
API Blueprint for PanelMerge
Provides documented REST API endpoints with Swagger/OpenAPI documentation
"""

from flask import Blueprint
from flask_restx import Api

# Create the API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Create the Flask-RESTX API instance
api = Api(
    api_bp,
    version='1.0',
    title='PanelMerge API',
    description='Interactive API for PanelMerge - Gene Panel Combination Tool',
    doc='/docs/',  # Swagger UI will be available at /api/v1/docs/
    contact='PanelMerge Development Team',
    contact_email='admin@panelmerge.com',
    license='MIT',
    license_url='https://opensource.org/licenses/MIT',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Type in the *\'Value\'* input box below: **\'Bearer &lt;JWT&gt;\'**, where JWT is the token'
        }
    },
    security='Bearer'
)

# Import namespaces after API creation to avoid circular imports
from . import panels
from . import genes
from . import users
from . import admin
from . import cache

# Add namespaces
api.add_namespace(panels.ns)
api.add_namespace(genes.ns)
api.add_namespace(users.ns)
api.add_namespace(admin.ns)
api.add_namespace(cache.ns)
