# Guest Access and Permission System

## Overview

PanelMerge now implements a flexible permission system that allows all users (both guests and authenticated users) to have full USER-level access to the core application features.

## Permission Levels

### 🌐 Guest Users (Unauthenticated)
- **Access Level**: USER-level (full core functionality)
- **Can Do**:
  - Upload gene panels
  - Select and filter panels from UK/Australian PanelApp
  - Download combined gene lists
  - Use all panel comparison features
  - Access the main application functionality

- **Cannot Do**:
  - Access user profile management
  - View personal download history
  - Access administrative features
  - Moderate content

### 👤 Authenticated Users

#### USER Role
- All guest capabilities plus:
- Profile management
- Personal download tracking
- Account settings

#### EDITOR Role  
- All USER capabilities plus:
- Content moderation abilities
- Advanced panel management

#### ADMIN Role
- All EDITOR capabilities plus:
- User management dashboard
- System administration
- Role assignment and user account control

## Implementation Details

### Permission Utility Functions

The system provides utility functions that can be used throughout the application:

```python
from app.main.utils import user_can_upload, user_can_moderate, user_is_admin

# Check if current user (guest or authenticated) can upload
if user_can_upload():
    # Allow upload functionality

# Check if current user can moderate (authenticated users only)
if user_can_moderate():
    # Show moderation options

# Check if current user is admin (authenticated users only)
if user_is_admin():
    # Show admin panel
```

### Template Context

These permission functions are automatically available in all templates:

```html
{% if user_can_upload() %}
    <button>Upload Panel</button>
{% endif %}

{% if user_can_moderate() %}
    <a href="/moderate">Moderate Content</a>
{% endif %}

{% if user_is_admin() %}
    <a href="/admin">Admin Panel</a>
{% endif %}
```

### Download Tracking

Downloads are now tracked with user association:
- **Authenticated users**: Downloads linked to user account
- **Guest users**: Downloads tracked by IP address only

### User Interface Updates

1. **Main Navigation**: Shows user status and role for both guests and authenticated users
2. **Guest Welcome**: Clear indication of guest status with "User-level access" badge
3. **Authentication Pages**: Inform users that account creation is optional
4. **Home Page**: Info banner explaining guest access capabilities

## Benefits

### For Users
- **Immediate Access**: No registration barrier to use core features
- **Privacy Option**: Can use the application without creating an account
- **Seamless Upgrade**: Can register later to access additional features

### For Administrators
- **Lower Barrier to Entry**: More users can access and try the application
- **Flexible Security**: Can still control advanced features through authentication
- **Analytics**: Can track usage patterns for both authenticated and guest users

## Security Considerations

- Guest users have the same functional access as registered USER-level accounts
- Administrative and moderation features remain protected behind authentication
- Download tracking still occurs for audit purposes
- Rate limiting applies equally to guests and authenticated users

## Configuration

The guest access policy is centralized in the utility functions and can be easily modified:

```python
# In app/main/utils.py
def user_can_upload():
    """Currently allows all users (guests and authenticated) to upload"""
    if current_user.is_authenticated:
        return current_user.can_upload()
    else:
        return True  # Change to False to require authentication
```

## Future Enhancements

This system provides a foundation for more sophisticated access control:
- Organization-based access restrictions
- Feature-specific permissions
- Time-limited guest sessions
- Enhanced analytics and tracking
- API rate limiting based on authentication status

The permission system is designed to be easily extensible while maintaining the current open-access philosophy for core features.
