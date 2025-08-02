# Timezone Support Implementation

This document describes the comprehensive timezone support system implemented in GenePanelCombine.

## Overview

The timezone support system allows users to view all timestamps in their preferred timezone throughout the application. The system automatically detects the user's timezone and allows manual override through user preferences.

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

#### User Model Updates (`app/models.py`)
- Added `timezone_preference` field to User model
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
- `user_datetime` - Format datetime in user timezone
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
- Override browser detection with manual selection
- Session-based timezone for guest users

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
All timestamps throughout the application display in user timezone:
- User registration/login times
- Audit log timestamps
- Session creation times
- Admin message timestamps
- File upload times

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
- Automatic detection: Enabled
- Session persistence: Yes
- Database persistence: Yes (for authenticated users)

## Usage

### For End Users

#### Automatic Setup
The system automatically detects and sets your timezone when you visit the site.

#### Manual Override
1. Navigate to your profile page to view your current timezone setting
2. Click "Edit Profile" to access timezone preferences
3. Select your preferred timezone from the dropdown in the timezone section
4. Click "Save Changes" to update your profile
5. Your timezone preference will be saved and used across all sessions

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

# Format datetime for display
formatted = TimezoneService.format_datetime(some_datetime, '%Y-%m-%d %H:%M:%S')
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
// Get current time in user timezone
const currentTime = window.getCurrentUserTime();

// Format any timestamp
const formatted = window.formatUserTimestamp('2025-08-02T10:30:00Z', 'datetime');

// Set timezone manually
window.timezoneManager.setTimezone('America/New_York');
```

## Database Migration

To add timezone support to existing installations:

```bash
python scripts/migrations/add_timezone_preference.py
```

This migration:
1. Adds `timezone_preference` column to User table
2. Sets default timezone to UTC for existing users
3. Verifies migration success

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

### Integration Opportunities
- Email notifications with timezone-aware timestamps
- Export files with timezone metadata
- API responses with timezone information
- Mobile app synchronization

## Conclusion

The timezone support system provides a comprehensive, user-friendly way to handle time display across the entire GenePanelCombine application. It balances automation with user control, ensuring timestamps are always meaningful and accessible to users regardless of their location.

---

*Last Updated: August 2, 2025*
*Implementation Status: Complete - Including profile integration and UI cleanup*
