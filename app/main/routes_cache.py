from flask import jsonify, request
from flask_login import current_user, login_required
from app.extensions import limiter, cache
from . import main_bp # Import the Blueprint object defined in __init__.py
from .utils import logger
from .cache_utils import (
    get_cached_all_panels, get_cached_panel_genes, get_cached_gene_suggestions,
    get_cached_combined_panels, clear_panel_cache, get_cache_stats
)
from ..audit_service import AuditService
from sqlalchemy import desc

@main_bp.route('/api/cache/stats')
@limiter.limit("10 per minute")
def api_cache_stats():
    """
    Get cache statistics (for debugging/monitoring)
    """
    try:
        stats = get_cache_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return jsonify({"error": "Failed to get cache stats"}), 500


@main_bp.route('/api/cache/clear')
@limiter.limit("5 per minute")
def api_cache_clear():
    """
    Clear panel cache (for admin use or debugging)
    """
    try:
        clear_panel_cache()
        
        # Log cache clear action
        AuditService.log_cache_clear("panel_cache")
        
        return jsonify({"success": True, "message": "Panel cache cleared"})
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({"error": "Failed to clear cache"}), 500
