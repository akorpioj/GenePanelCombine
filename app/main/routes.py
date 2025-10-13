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
from ..timezone_service import TimezoneService
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


@main_bp.route('/privacy')
@limiter.limit("30 per minute")
def privacy():
    """Display the privacy policy page"""
    return render_template('main/privacy.html')


# ===========================
# TIMEZONE API ENDPOINTS
# ===========================

@main_bp.route('/api/timezone/preferences', methods=['GET'])
@limiter.limit("30 per minute")
def api_timezone_preferences():
    """Get user's timezone and time format preferences"""
    try:
        preferences = {
            'success': True,
            'timezone': None,
            'time_format': '24h'
        }
        
        if current_user.is_authenticated:
            preferences['timezone'] = current_user.timezone_preference
            preferences['time_format'] = getattr(current_user, 'time_format_preference', '24h') or '24h'
        else:
            # For anonymous users, check session
            from flask import session
            preferences['timezone'] = session.get('user_timezone') or session.get('browser_timezone')
        
        return jsonify(preferences), 200
    except Exception as e:
        logger.error(f"Error getting timezone preferences: {e}")
        return jsonify({'success': False, 'error': 'Failed to get preferences'}), 500


@main_bp.route('/api/timezone/detect', methods=['POST'])
@limiter.limit("30 per minute")
def api_timezone_detect():
    """Receive browser-detected timezone"""
    try:
        data = request.get_json()
        timezone_name = data.get('timezone')
        
        if not timezone_name:
            return jsonify({'success': False, 'error': 'Timezone not provided'}), 400
        
        # Set browser timezone in session
        if TimezoneService.set_browser_timezone(timezone_name):
            logger.info(f"Browser timezone detected: {timezone_name}")
            
            # If user is authenticated and doesn't have a preference, could auto-set
            # But we'll leave it as detected only for now
            
            return jsonify({
                'success': True,
                'message': f'Timezone detected: {timezone_name}',
                'timezone': timezone_name
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid timezone'
            }), 400
            
    except Exception as e:
        logger.error(f"Error detecting timezone: {e}")
        return jsonify({'success': False, 'error': 'Failed to detect timezone'}), 500


@main_bp.route('/api/timezone/set', methods=['POST'])
@limiter.limit("30 per minute")
def api_timezone_set():
    """Set user's timezone preference"""
    try:
        data = request.get_json()
        timezone_name = data.get('timezone')
        
        if not timezone_name:
            return jsonify({'success': False, 'error': 'Timezone not provided'}), 400
        
        # Validate timezone
        if not TimezoneService.set_user_timezone(timezone_name):
            return jsonify({
                'success': False,
                'error': 'Invalid timezone'
            }), 400
        
        # If user is authenticated, update their preference
        if current_user.is_authenticated:
            if current_user.set_timezone(timezone_name):
                db.session.commit()
                
                # Log audit action
                AuditService.log_action(
                    action_type=AuditActionType.USER_UPDATED,
                    action_description=f"Updated timezone preference to {timezone_name}",
                    user_id=current_user.id,
                    resource_type='user',
                    resource_id=current_user.id
                )
                
                logger.info(f"User {current_user.id} set timezone to {timezone_name}")
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to set timezone preference'
                }), 500
        
        return jsonify({
            'success': True,
            'message': f'Timezone set to {timezone_name}',
            'timezone': timezone_name
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error setting timezone: {e}")
        return jsonify({'success': False, 'error': 'Failed to set timezone'}), 500


@main_bp.route('/api/timezone/current', methods=['GET'])
@limiter.limit("30 per minute")
def api_timezone_current():
    """Get current active timezone"""
    try:
        user_tz = TimezoneService.get_user_timezone()
        current_time = TimezoneService.now_in_user_timezone()
        
        return jsonify({
            'success': True,
            'timezone': user_tz.zone,
            'current_time': current_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'utc_offset': current_time.strftime('%z')
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting current timezone: {e}")
        return jsonify({'success': False, 'error': 'Failed to get current timezone'}), 500


@main_bp.route('/api/timezone/available', methods=['GET'])
@limiter.limit("30 per minute")
def api_timezone_available():
    """Get list of available timezones"""
    try:
        timezones = []
        for tz_name, display_name in TimezoneService.get_available_timezones():
            try:
                tz = TimezoneService.convert_to_user_timezone(TimezoneService.utc_now())
                # Get timezone object for current time
                import pytz
                tz_obj = pytz.timezone(tz_name)
                current_time_in_tz = datetime.now(tz_obj)
                
                timezones.append({
                    'name': tz_name,
                    'display_name': display_name,
                    'current_time': current_time_in_tz.strftime('%H:%M'),
                    'utc_offset': current_time_in_tz.strftime('%z')
                })
            except Exception as e:
                logger.warning(f"Error processing timezone {tz_name}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'timezones': timezones
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting available timezones: {e}")
        return jsonify({'success': False, 'error': 'Failed to get available timezones'}), 500
