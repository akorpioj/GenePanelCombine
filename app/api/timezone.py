"""
API endpoints for timezone management.
"""

from flask import Blueprint, request, jsonify, session
from app.timezone_service import TimezoneService
import pytz

timezone_bp = Blueprint('timezone', __name__, url_prefix='/api/timezone')


@timezone_bp.route('/set', methods=['POST'])
def set_timezone():
    """
    Set user's timezone preference.
    
    Expected JSON payload:
    {
        "timezone": "America/New_York"
    }
    """
    try:
        data = request.get_json()
        if not data or 'timezone' not in data:
            return jsonify({
                'success': False,
                'error': 'Timezone is required'
            }), 400
        
        timezone_name = data['timezone']
        
        if TimezoneService.set_user_timezone(timezone_name):
            # Also save to user profile if authenticated
            try:
                from flask_login import current_user
                from app.models import db
                
                if current_user.is_authenticated:
                    if current_user.set_timezone(timezone_name):
                        db.session.commit()
            except Exception as e:
                # Don't fail the request if user profile update fails
                print(f"Warning: Failed to update user timezone preference: {e}")
            
            return jsonify({
                'success': True,
                'timezone': timezone_name,
                'message': f'Timezone set to {timezone_name}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid timezone'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@timezone_bp.route('/detect', methods=['POST'])
def detect_timezone():
    """
    Set browser-detected timezone.
    
    Expected JSON payload:
    {
        "timezone": "America/New_York"
    }
    """
    try:
        data = request.get_json()
        if not data or 'timezone' not in data:
            return jsonify({
                'success': False,
                'error': 'Timezone is required'
            }), 400
        
        timezone_name = data['timezone']
        
        if TimezoneService.set_browser_timezone(timezone_name):
            return jsonify({
                'success': True,
                'timezone': timezone_name,
                'message': f'Browser timezone detected: {timezone_name}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid timezone'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@timezone_bp.route('/current', methods=['GET'])
def get_current_timezone():
    """
    Get user's current timezone.
    """
    try:
        user_tz = TimezoneService.get_user_timezone()
        current_time = TimezoneService.now_in_user_timezone()
        
        return jsonify({
            'success': True,
            'timezone': str(user_tz),
            'current_time': current_time.isoformat(),
            'formatted_time': TimezoneService.format_datetime(current_time),
            'utc_offset': current_time.strftime('%z')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@timezone_bp.route('/available', methods=['GET'])
def get_available_timezones():
    """
    Get list of available timezones for user selection.
    """
    try:
        timezones = TimezoneService.get_available_timezones()
        
        # Add current time in each timezone for better UX
        timezone_list = []
        for tz_name, display_name in timezones:
            tz = pytz.timezone(tz_name)
            current_time = TimezoneService.utc_now().astimezone(tz)
            
            timezone_list.append({
                'name': tz_name,
                'display_name': display_name,
                'current_time': current_time.strftime('%H:%M'),
                'utc_offset': current_time.strftime('%z'),
                'formatted_offset': current_time.strftime('UTC%z')
            })
        
        return jsonify({
            'success': True,
            'timezones': timezone_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
