# Timezone Support Implementation

This document describes the comprehensive timezone support system implemented in GenePanelCombine.

## Overview

The timezone support system allows users to view all timestamps in their preferred timezone and time format throughout the application. The system automatically detects the user's timezone and allows manual override through user preferences. Users can also choose between 12-hour (AM/PM) and 24-hour clock display formats.

## Components

### 1. Backend Components

#### TimezoneService (`app/timezone_service.py`)
Core service class that handles all timezone operations:
- Timezone detection and preference management
- Datetime conversion to user timezone
- Formatting timestamps in user-friendly formats
- Relative time formatting ("2 hours ago")

#### Timezone API (`app/api/timezone.py`)
REST API endpoints for timezone management:
- `POST /api/timezone/set` - Set user timezone preference
- `POST /api/timezone/detect` - Set browser-detected timezone
- `GET /api/timezone/current` - Get current timezone info
- `GET /api/timezone/available` - Get list of available timezones
- `GET /api/timezone/preferences` - Get user's timezone and time format preferences

#### User Model Updates (`app/models.py`)
- Added `timezone_preference` field to User model
- Added `time_format_preference` field to User model (12h/24h)
- Added `get_timezone()` and `set_timezone()` methods
- Database migration support

### 2. Frontend Components

#### JavaScript Client (`app/static/js/timezone.js`)
Comprehensive timezone management client:
- Automatic timezone detection using Intl API
- Dynamic timestamp updates on page
- Current time display updates every minute
- Timezone selector widgets in edit profile
- DOM-ready initialization for proper element targeting
- Debug logging for troubleshooting

#### CSS Styling (`app/static/css/timezone.css`)
Responsive styling for timezone components:
- Timezone selector dropdowns
- Timestamp display elements
- Dark mode support
- Mobile-responsive design

### 3. Template Integration

#### Jinja2 Filters
- `user_datetime` - Format datetime in user timezone with automatic 12h/24h format adjustment
- `relative_time` - Format relative time ("2 hours ago")

#### Template Updates
Updated templates for timezone-aware datetime display:
- Profile page shows timezone preference and current time
- Edit profile page has timezone selector
- Audit logs display in user timezone
- Admin interfaces use timezone-aware timestamps
- Session management shows timezone-aware times
- Removed timezone display from main navigation for cleaner UI

## Features

### 1. Automatic Detection
- Browser timezone detection using JavaScript Intl API
- Fallback to UTC if detection fails
- Seamless integration with existing authentication

### 2. User Preferences
- Per-user timezone preferences stored in database
- Per-user time format preference (12h or 24h)
- Override browser detection with manual selection
- Session-based timezone for guest users
- Preferences persist across sessions

### 3. Priority System
Timezone selection follows this priority order:
1. Authenticated user's saved preference
2. Session timezone (manually set)
3. Browser-detected timezone
4. Default (UTC)

### 4. Real-time Updates
- Automatic timestamp updates every minute on profile page
- Current time display in user's timezone on profile page  
- Dynamic timezone preview in edit profile settings
- Immediate updates when timezone changes
- Removed timezone display from main interface for cleaner UI

### 5. Comprehensive Coverage
All timestamps throughout the application display in user timezone and preferred time format:
- User registration/login times
- Audit log timestamps
- Session creation times
- Admin message timestamps
- File upload times
- Profile page current time display
- All dynamic JavaScript-rendered timestamps

### 6. Time Format Preference (Added October 2025)
- User-selectable 12-hour (AM/PM) or 24-hour clock format
- Backend automatic format string conversion
- JavaScript dynamic format rendering
- Default: 24-hour format for new users
- Preference saved in user profile
- Applied across all timestamp displays

## Configuration

### Available Timezones
The system includes commonly used timezones:
- UTC (default)
- US timezones (Eastern, Central, Mountain, Pacific)
- European timezones (London, Paris, Berlin, Helsinki, Stockholm)
- Asian timezones (Tokyo, Shanghai, Mumbai)
- Australian timezones (Sydney, Melbourne)

### Default Settings
- Default timezone: UTC
- Default time format: 24-hour (24h)
- Automatic detection: Enabled
- Session persistence: Yes
- Database persistence: Yes (for authenticated users)
- Time format options: '12h' (AM/PM) or '24h' (military time)

## Usage

### For End Users

#### Automatic Setup
The system automatically detects and sets your timezone when you visit the site.

#### Manual Override
1. Navigate to your profile page to view your current timezone and time format settings
2. Click "Edit Profile" to access timezone and time format preferences
3. Select your preferred timezone from the "Timezone Preference" dropdown
4. Select your preferred time format from the "Time Format" dropdown:
   - **24-hour (18:53)** - Military time format
   - **12-hour (6:53 PM)** - AM/PM format
5. Click "Save Changes" to update your profile
6. Your preferences will be saved and used across all sessions

#### Timezone Display
- Profile page shows your current timezone preference and local time
- All timestamps throughout the application show in your local timezone
- Times include timezone abbreviation (EST, PST, etc.) where applicable
- Relative times ("2 hours ago") are also timezone-aware
- Timezone selector removed from main pages for cleaner interface

### For Developers

#### Using TimezoneService
```python
from app.timezone_service import TimezoneService

# Get user's current timezone
user_tz = TimezoneService.get_user_timezone()

# Convert datetime to user timezone
user_time = TimezoneService.convert_to_user_timezone(some_datetime)

# Format datetime for display (automatically uses user's time format preference)
formatted = TimezoneService.format_datetime(some_datetime, '%Y-%m-%d %H:%M:%S')

# Note: The format_datetime_filter in templates automatically converts
# 12h/24h format codes based on user's time_format_preference:
# - %I (12-hour) <-> %H (24-hour)
# - %p (AM/PM) is added/removed automatically
```

#### Using in Templates
```html
<!-- Basic timezone-aware formatting -->
{{ timestamp | user_datetime }}

<!-- Custom format -->
{{ timestamp | user_datetime('%B %d, %Y at %I:%M %p') }}

<!-- Relative time -->
{{ timestamp | relative_time }}

<!-- With JavaScript updates -->
<span data-timestamp="{{ timestamp.isoformat() }}" data-format="relative">
    {{ timestamp | relative_time }}
</span>
```

#### JavaScript Integration
```javascript
// Get current time in user timezone and format
const currentTime = window.getCurrentUserTime();

// Format any timestamp (automatically uses user's time format preference)
const formatted = window.formatUserTimestamp('2025-08-02T10:30:00Z', 'datetime');

// Set timezone manually
window.timezoneManager.setTimezone('America/New_York');

// User preferences are automatically loaded on page load
// The TimezoneManager loads time format preference from /api/timezone/preferences
// All timestamp formatting respects the user's 12h/24h preference
```

## Database Migration

### Timezone Preference Migration (v1.4.1)

To add timezone support to existing installations:

```bash
python scripts/migrations/add_timezone_preference.py
```

This migration:
1. Adds `timezone_preference` column to User table
2. Sets default timezone to UTC for existing users
3. Verifies migration success

### Time Format Preference Migration (v1.5.0)

To add time format preference support:

```bash
flask db migrate -m "Add time format preference to users"
flask db upgrade
```

This migration:
1. Adds `time_format_preference` column to User table (VARCHAR(10))
2. Sets default value to '24h' for existing users
3. Supports values: '12h' or '24h'

**Migration file**: `3d43d3ddbfa5_add_time_format_preference_to_users.py`

**Manual SQL equivalent**:
```sql
ALTER TABLE "user" ADD COLUMN time_format_preference VARCHAR(10);
UPDATE "user" SET time_format_preference = '24h' WHERE time_format_preference IS NULL;
```

## Security Considerations

### Data Protection
- Timezone preferences are stored as plain text (non-sensitive)
- No personal information is exposed through timezone data
- IANA timezone names are validated on input

### Privacy
- Browser timezone detection is optional
- Users can opt out by manually setting timezone
- No timezone tracking or analytics

## Performance

### Optimization Strategies
- Timezone conversions cached per request
- JavaScript timestamp updates throttled
- Database queries optimized for timezone lookups

### Scalability
- Timezone data cached in memory
- Minimal database impact (single column)
- Client-side timestamp formatting reduces server load

## Testing

### Automated Tests
- Unit tests for TimezoneService methods
- API endpoint testing
- Database migration testing
- JavaScript functionality testing

### Manual Testing Scenarios
- Cross-timezone user interactions
- Daylight saving time transitions
- Browser compatibility testing
- Mobile device testing

## Browser Support

### Requirements
- Modern browsers with Intl API support
- JavaScript enabled
- Cookies enabled (for session storage)

### Fallbacks
- Graceful degradation to UTC for older browsers
- Server-side timezone formatting as backup
- Progressive enhancement approach

## Troubleshooting

### Common Issues

#### Timezone Selector Not Showing
- Verify timezone JavaScript is loaded (`/static/js/timezone.js`)
- Check browser console for JavaScript errors
- Ensure API endpoints are accessible (`/api/timezone/available`)

#### Timezone Not Detected
- Check browser Intl API support
- Verify JavaScript is enabled
- Clear browser cache and cookies

#### Current Time Display Issues
- Check if TimezoneManager is properly initialized
- Verify DOM elements with id 'current-user-time' exist
- Ensure JavaScript runs after DOM is loaded
- Check browser console for initialization errors
- Verify timezone.js is included in page templates

#### API Errors
- Validate timezone names against IANA database
- Check network connectivity
- Verify authentication status

### Debug Information
Enable debug logging to see:
- Timezone detection results
- API request/response data
- Database query results
- JavaScript console logs

## Future Enhancements

### Planned Features
- Bulk timezone updates for admins
- Timezone analytics and reporting
- More granular timezone controls
- Calendar integration
- Time zone change notifications
- Custom date/time format templates
- Locale-based formatting options

### Integration Opportunities
- Email notifications with timezone-aware timestamps
- Export files with timezone metadata
- API responses with timezone information
- Mobile app synchronization

## Conclusion

The timezone support system provides a comprehensive, user-friendly way to handle time display across the entire GenePanelCombine application. It balances automation with user control, ensuring timestamps are always meaningful and accessible to users regardless of their location.

### Key Features Summary:
- ✅ Automatic timezone detection
- ✅ Manual timezone selection
- ✅ User-configurable 12h/24h time format
- ✅ Real-time clock display
- ✅ Dynamic timestamp updates
- ✅ Backend and frontend format conversion
- ✅ Comprehensive coverage across all pages
- ✅ Persistent user preferences
- ✅ API-driven preference management

### Recent Updates (October 2025):
- **Time Format Preference**: Added user-selectable 12h/24h clock format
- **Enhanced API**: New `/api/timezone/preferences` endpoint
- **Smart Format Conversion**: Backend automatically converts format strings
- **JavaScript Integration**: Dynamic loading and application of user preferences
- **Profile Enhancement**: Time format selector in edit profile page
- **Backward Compatibility**: Default 24h format for existing users

---

*Last Updated: October 12, 2025*
*Implementation Status: Complete - Including time format preference feature*
