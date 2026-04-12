"""
Genie Blueprint for PanelMerge
Handles Genie database search functionality
"""

from flask import Blueprint

genie_bp = Blueprint('genie', __name__, url_prefix='/genie')

# Import routes after blueprint creation to avoid circular imports
from . import routes
