"""
Cache API endpoints
"""

from flask_restx import Namespace, Resource
from flask_login import login_required, current_user
from ..extensions import limiter
from ..main.cache_utils import get_cache_stats, clear_panel_cache
from ..main.utils import logger
from ..audit_service import AuditService
from .models import (
    cache_stats_model, success_response_model, error_response_model,
    version_info_model
)

ns = Namespace('cache', description='Cache management operations')

@ns.route('/stats')
class CacheStats(Resource):
    @ns.doc('get_cache_stats')
    @ns.marshal_with(cache_stats_model)
    @ns.response(200, 'Success')
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @login_required
    @limiter.limit("10 per minute")
    def get(self):
        """Get cache statistics (Admin only)"""
        try:
            if not current_user.is_admin():
                ns.abort(403, "Admin privileges required")
            
            stats = get_cache_stats()
            
            # Log cache stats access
            AuditService.log_admin_action(
                action_description="Retrieved cache statistics via API",
                details=stats
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            ns.abort(500, f"Failed to get cache stats: {str(e)}")

@ns.route('/clear')
class CacheClear(Resource):
    @ns.doc('clear_cache')
    @ns.marshal_with(success_response_model)
    @ns.response(200, 'Cache cleared successfully')
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @login_required
    @limiter.limit("5 per minute")
    def post(self):
        """Clear panel cache (Admin only)"""
        try:
            if not current_user.is_admin():
                ns.abort(403, "Admin privileges required")
            
            clear_panel_cache()
            
            # Log cache clear action
            AuditService.log_admin_action(
                action_description="Cleared panel cache via API",
                details={"cache_type": "panel_cache"}
            )
            
            return {
                'success': True,
                'message': 'Panel cache cleared successfully'
            }
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            ns.abort(500, f"Failed to clear cache: {str(e)}")

@ns.route('/version')
class Version(Resource):
    @ns.doc('get_version')
    @ns.marshal_with(version_info_model)
    @ns.response(200, 'Success')
    @ns.response(500, 'Internal server error', error_response_model)
    @limiter.limit("10 per minute")
    def get(self):
        """Get application version information"""
        try:
            from app.version import get_version_info
            version_info = get_version_info()
            
            # Log version access
            AuditService.log_view(
                resource_type="version",
                resource_id="app_version",
                description="Retrieved application version via API",
                details=version_info
            )
            
            return version_info
            
        except Exception as e:
            logger.error(f"Error getting version info: {e}")
            ns.abort(500, f"Failed to get version info: {str(e)}")
