from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import current_user, login_required
import datetime
from app.extensions import limiter, cache
from . import main_bp # Import the Blueprint object defined in __init__.py
from ..models import PanelDownload, SavedPanel, PanelVersion, PanelGene, PanelStatus, PanelVisibility, db, AuditActionType
from .excel import generate_excel_file
from .utils import filter_genes_from_panel_data
from .utils import list_type_options, MAX_PANELS
from .utils import logger
from .cache_utils import (
    get_cached_all_panels, get_cached_panel_genes, get_cached_gene_suggestions,
    get_cached_combined_panels, clear_panel_cache, get_cache_stats
)
from .panel_downloader import PanelDownloader
from ..audit_service import AuditService
from werkzeug.utils import secure_filename

# --- Flask Routes ---

@main_bp.route('/')
@limiter.limit("30 per minute")
def index():
    logger.info("index")
    
    # Get active admin messages
    from ..models import AdminMessage
    admin_messages = AdminMessage.get_active_messages()
    
    # No more server-side filtering
    return render_template('index.html', 
                           max_panels=MAX_PANELS,
                           list_type_options=list_type_options,
                           admin_messages=admin_messages)

@main_bp.route('/version-history')
@limiter.limit("30 per minute")
def version_history():
    """Display the version history page."""
    return render_template('version_history.html')

@main_bp.route('/my-panels')
@login_required
@limiter.limit("30 per minute")
def panel_library():
    """Display the enhanced panel library management interface."""
    return render_template('panel_library.html')

@main_bp.route('/generate', methods=['POST'])
@limiter.limit("30 per hour")  # More strict limit for resource-intensive operation
def generate():
    """
    Handles form submission, processes selected panels, filters genes,
    and returns an Excel file.
    """
    panel_downloader = PanelDownloader(request)
    return panel_downloader.generate_combined_gene_list()

@main_bp.route('/check_saved_panel_notification', methods=['GET'])
def check_saved_panel_notification():
    """
    Check if there's a saved panel notification in the session and return it
    """
    from flask import session
    if current_user.is_authenticated:
        saved_panel_info = session.pop('last_saved_panel', None)
        if saved_panel_info:
            session.modified = True
            return jsonify({
                'success': True,
                'panel': saved_panel_info
            })
    
    return jsonify({'success': False})

@main_bp.route('/api/version')
@limiter.limit("10 per minute")
def api_version():
    """API endpoint to get application version information"""
    from app.version import get_version_info
    return jsonify(get_version_info())


@main_bp.route('/version')
def version():
    """Simple version display page"""
    from app.version import get_version_info
    version_info = get_version_info()
    return render_template('main/version.html', version_info=version_info)
