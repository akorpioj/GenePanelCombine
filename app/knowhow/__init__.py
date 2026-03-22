"""
Knowhow Blueprint for PanelMerge
Handles knowledge base and how-to functionality
"""

from flask import Blueprint

knowhow_bp = Blueprint('knowhow', __name__, url_prefix='/knowhow')

# Import routes after blueprint creation to avoid circular imports
from . import routes
