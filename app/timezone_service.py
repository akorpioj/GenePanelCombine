"""
Timezone utilities for PanelMerge application.
Provides timezone-aware datetime handling and user timezone preferences.
"""

import pytz
from datetime import datetime, timezone
from flask import session, request
from typing import Optional, Union
import re


class TimezoneService:
    """Service for handling timezone operations and user preferences."""
    
    # Default timezone if no user preference is set
    DEFAULT_TIMEZONE = 'UTC'
    
    # Common timezone mapping for better UX
    TIMEZONE_DISPLAY_NAMES = {
        'UTC': 'UTC (Coordinated Universal Time)',
        'US/Eastern': 'Eastern Time (US & Canada)',
        'US/Central': 'Central Time (US & Canada)',
        'US/Mountain': 'Mountain Time (US & Canada)',
        'US/Pacific': 'Pacific Time (US & Canada)',
        'Europe/London': 'London (GMT/BST)',
        'Europe/Paris': 'Paris (CET/CEST)',
        'Europe/Berlin': 'Berlin (CET/CEST)',
        'Europe/Helsinki': 'Helsinki (EET/EEST)',
        'Europe/Stockholm': 'Stockholm (CET/CEST)',
        'Asia/Tokyo': 'Tokyo (JST)',
        'Asia/Shanghai': 'Shanghai (CST)',
        'Asia/Kolkata': 'Mumbai/Kolkata (IST)',
        'Australia/Sydney': 'Sydney (AEST/AEDT)',
        'Australia/Melbourne': 'Melbourne (AEST/AEDT)',
    }
    
    @classmethod
    def get_user_timezone(cls) -> pytz.BaseTzInfo:
        """
        Get the user's preferred timezone.
        
        Priority order:
        1. Authenticated user's saved timezone preference
        2. Session timezone (if set)
        3. Browser timezone (if detected)
        4. Default timezone (UTC)
        
        Returns:
            pytz timezone object
        """
        # Check authenticated user's preference first
        try:
            from flask_login import current_user
            if current_user.is_authenticated and hasattr(current_user, 'timezone_preference'):
                if current_user.timezone_preference:
                    try:
                        return pytz.timezone(current_user.timezone_preference)
                    except pytz.UnknownTimeZoneError:
                        pass
        except ImportError:
            # Flask-Login not available
            pass
        
        # Check session for saved timezone preference
        timezone_name = session.get('user_timezone')
        
        if timezone_name:
            try:
                return pytz.timezone(timezone_name)
            except pytz.UnknownTimeZoneError:
                pass
        
        # Check for browser-detected timezone from JavaScript
        browser_timezone = session.get('browser_timezone')
        if browser_timezone:
            try:
                return pytz.timezone(browser_timezone)
            except pytz.UnknownTimeZoneError:
                pass
        
        # Fallback to default
        return pytz.timezone(cls.DEFAULT_TIMEZONE)
    
    @classmethod
    def set_user_timezone(cls, timezone_name: str) -> bool:
        """
        Set the user's timezone preference in session.
        
        Args:
            timezone_name: IANA timezone name (e.g., 'America/New_York')
            
        Returns:
            True if timezone was set successfully, False otherwise
        """
        try:
            # Validate timezone
            pytz.timezone(timezone_name)
            session['user_timezone'] = timezone_name
            return True
        except pytz.UnknownTimeZoneError:
            return False
    
    @classmethod
    def set_browser_timezone(cls, timezone_name: str) -> bool:
        """
        Set the browser-detected timezone in session.
        
        Args:
            timezone_name: IANA timezone name detected by browser
            
        Returns:
            True if timezone was set successfully, False otherwise
        """
        try:
            # Validate timezone
            pytz.timezone(timezone_name)
            session['browser_timezone'] = timezone_name
            return True
        except pytz.UnknownTimeZoneError:
            return False
    
    @classmethod
    def convert_to_user_timezone(cls, dt: datetime) -> datetime:
        """
        Convert a datetime to the user's timezone.
        
        Args:
            dt: datetime object (can be naive or timezone-aware)
            
        Returns:
            datetime in user's timezone
        """
        user_tz = cls.get_user_timezone()
        
        # If datetime is naive, assume it's UTC
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        
        # Convert to user timezone
        return dt.astimezone(user_tz)
    
    @classmethod
    def format_datetime(cls, dt: datetime, format_string: str = '%Y-%m-%d %H:%M:%S') -> str:
        """
        Format a datetime in the user's timezone.
        
        Args:
            dt: datetime object
            format_string: strftime format string
            
        Returns:
            Formatted datetime string with timezone abbreviation
        """
        if dt is None:
            return 'N/A'
        
        user_dt = cls.convert_to_user_timezone(dt)
        formatted = user_dt.strftime(format_string)
        
        # Add timezone abbreviation
        tz_abbrev = user_dt.strftime('%Z')
        if tz_abbrev:
            formatted += f' {tz_abbrev}'
        
        return formatted
    
    @classmethod
    def format_datetime_relative(cls, dt: datetime) -> str:
        """
        Format a datetime as a relative time (e.g., "2 hours ago").
        
        Args:
            dt: datetime object
            
        Returns:
            Relative time string
        """
        if dt is None:
            return 'N/A'
        
        user_tz = cls.get_user_timezone()
        now = datetime.now(user_tz)
        user_dt = cls.convert_to_user_timezone(dt)
        
        delta = now - user_dt
        
        if delta.days > 0:
            if delta.days == 1:
                return "1 day ago"
            elif delta.days < 7:
                return f"{delta.days} days ago"
            elif delta.days < 30:
                weeks = delta.days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            elif delta.days < 365:
                months = delta.days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
            else:
                years = delta.days // 365
                return f"{years} year{'s' if years > 1 else ''} ago"
        
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        
        else:
            return "Just now"
    
    @classmethod
    def get_available_timezones(cls) -> list:
        """
        Get a list of commonly used timezones for user selection.
        
        Returns:
            List of tuples (timezone_name, display_name)
        """
        timezones = []
        
        for tz_name, display_name in cls.TIMEZONE_DISPLAY_NAMES.items():
            timezones.append((tz_name, display_name))
        
        # Sort by display name
        timezones.sort(key=lambda x: x[1])
        
        return timezones
    
    @classmethod
    def now_in_user_timezone(cls) -> datetime:
        """
        Get current datetime in user's timezone.
        
        Returns:
            Current datetime in user's timezone
        """
        user_tz = cls.get_user_timezone()
        return datetime.now(user_tz)
    
    @classmethod
    def utc_now(cls) -> datetime:
        """
        Get current datetime in UTC.
        
        Returns:
            Current datetime in UTC
        """
        return datetime.now(pytz.UTC)


def format_datetime_filter(dt: datetime, format_string: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Jinja2 filter for formatting datetime in user's timezone.
    
    Args:
        dt: datetime object
        format_string: strftime format string
        
    Returns:
        Formatted datetime string
    """
    return TimezoneService.format_datetime(dt, format_string)


def format_datetime_relative_filter(dt: datetime) -> str:
    """
    Jinja2 filter for relative datetime formatting.
    
    Args:
        dt: datetime object
        
    Returns:
        Relative time string
    """
    return TimezoneService.format_datetime_relative(dt)


def register_timezone_filters(app):
    """
    Register timezone-related Jinja2 filters with the Flask app.
    
    Args:
        app: Flask application instance
    """
    app.jinja_env.filters['user_datetime'] = format_datetime_filter
    app.jinja_env.filters['relative_time'] = format_datetime_relative_filter
    
    # Make TimezoneService available in templates
    app.jinja_env.globals['TimezoneService'] = TimezoneService
