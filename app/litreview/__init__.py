"""
LitReview Blueprint for PanelMerge
Handles literature review functionality
"""

from flask import Blueprint

litreview_bp = Blueprint('litreview', __name__, url_prefix='/litreview')

# Import routes after blueprint creation to avoid circular imports
from . import routes
from . import api  # registers the Flask-RESTX namespace with app.api
