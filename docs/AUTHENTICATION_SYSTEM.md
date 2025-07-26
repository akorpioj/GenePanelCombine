# User Authentication System

## Overview

The PanelMerge application now includes a comprehensive user authentication system with role-based access control. This system provides secure user registration, login, profile management, and administrative capabilities.

## Features

### 🔐 Authentication
- **User Registration**: New users can create accounts with email verification
- **Secure Login**: Username/email and password authentication
- **Password Security**: Strong password requirements with validation
- **Session Management**: Secure session handling with Flask-Login
- **Remember Me**: Optional persistent login sessions

### 👥 Role-Based Access Control
The system implements a hierarchical role system:

1. **VIEWER** (Level 1): Can view panels and download results
2. **USER** (Level 2): Can upload panels and view content
3. **EDITOR** (Level 3): Can moderate content and manage panels
4. **ADMIN** (Level 4): Full administrative access

Each role inherits permissions from lower levels.

### 📊 User Management
- **Profile Management**: Users can update their personal information
- **Password Changes**: Secure password update functionality
- **Admin Dashboard**: Comprehensive user management for administrators
- **User Statistics**: Activity tracking and usage metrics

## API Endpoints

### Authentication Routes (`/auth`)

#### Public Routes
- `GET /auth/register` - User registration form
- `POST /auth/register` - Process registration
- `GET /auth/login` - Login form
- `POST /auth/login` - Process login
- `GET /auth/logout` - User logout

#### Protected Routes (Requires Login)
- `GET /auth/profile` - User profile page
- `GET /auth/edit-profile` - Edit profile form
- `POST /auth/edit-profile` - Update profile
- `GET /auth/change-password` - Change password form
- `POST /auth/change-password` - Update password

#### Admin Routes (Admin Only)
- `GET /auth/admin/users` - User management dashboard
- `GET /auth/api/user/<id>` - Get user details (JSON)
- `PUT /auth/api/user/<id>` - Update user (JSON)
- `POST /auth/api/user/<id>/toggle-status` - Toggle user active status

#### API Routes
- `GET /auth/api/check-username?username=<username>` - Check username availability
- `GET /auth/api/check-email?email=<email>` - Check email availability

## Database Schema

### User Model

```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    organization = db.Column(db.String(100))
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.USER)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
```

### UserRole Enum

```python
class UserRole(Enum):
    VIEWER = "viewer"
    USER = "user"
    EDITOR = "editor"
    ADMIN = "admin"
```

## Installation & Setup

### 1. Install Dependencies

The authentication system requires additional Python packages:

```bash
pip install flask-login email-validator flask-limiter
```

### 2. Run Database Migration

Execute the migration script to set up the user authentication tables:

```bash
python scripts/migrate_auth.py
```

This will:
- Create the User table and related schema
- Set up a default admin user (username: `admin`, password: `Admin123!`)
- Display setup confirmation and statistics

### 3. Configuration

The system uses the existing Flask configuration. No additional configuration is required.

## Usage

### For End Users

1. **Registration**: Visit `/auth/register` to create a new account
2. **Login**: Visit `/auth/login` to sign in
3. **Profile**: Access your profile at `/auth/profile`
4. **Upload**: Authenticated users can upload gene panels (USER role and above)

### For Administrators

1. **User Management**: Access the admin dashboard at `/auth/admin/users`
2. **Role Management**: Change user roles and permissions
3. **User Status**: Activate/deactivate user accounts
4. **Statistics**: View user activity and system usage

## Security Features

### Password Security
- Minimum 8 characters
- Must contain uppercase and lowercase letters
- Must contain at least one number
- Must contain at least one special character
- Secure hashing with Werkzeug

### Rate Limiting
- Login attempts: 5 per minute
- Registration: 3 per minute
- Password changes: 3 per minute

### Session Security
- Secure session cookies
- CSRF protection
- Session timeout handling

## Role Permissions

| Permission | Viewer | User | Editor | Admin |
|------------|--------|------|--------|-------|
| View panels | ✅ | ✅ | ✅ | ✅ |
| Download results | ✅ | ✅ | ✅ | ✅ |
| Upload panels | ❌ | ✅ | ✅ | ✅ |
| Moderate content | ❌ | ❌ | ✅ | ✅ |
| User management | ❌ | ❌ | ❌ | ✅ |
| System administration | ❌ | ❌ | ❌ | ✅ |

## Integration with Existing Features

The authentication system integrates seamlessly with existing PanelMerge features:

### Panel Upload Protection
Panel upload functionality is now protected and requires USER role or higher.

### Download Tracking
User downloads are tracked and associated with user accounts.

### Version History
User actions in version history are linked to authenticated users.

## Templates

The authentication system includes responsive, accessible templates:

- `auth/base.html` - Base template with navigation
- `auth/login.html` - Login form with validation
- `auth/register.html` - Registration form with real-time validation
- `auth/profile.html` - User profile display
- `auth/edit_profile.html` - Profile editing form
- `auth/change_password.html` - Password change form
- `auth/admin_users.html` - Administrative user management

## Development Notes

### Adding New Permissions

To add new permission checks:

```python
# In your route
@login_required
def upload_panel():
    if not current_user.can_upload():
        flash('You do not have permission to upload panels.', 'error')
        return redirect(url_for('main.index'))
    # ... upload logic
```

### Custom Role Checks

```python
# Add new methods to User model
def can_export_data(self):
    return self.has_role(UserRole.EDITOR)

def can_manage_settings(self):
    return self.is_admin()
```

### API Authentication

For API endpoints, you can use the existing decorators:

```python
from flask_login import login_required
from app.auth.routes import admin_required

@app.route('/api/admin/data')
@login_required
@admin_required
def admin_api():
    return jsonify({'data': 'admin_only'})
```

## Troubleshooting

### Common Issues

1. **Migration Fails**
   - Ensure the database is accessible
   - Check for existing table conflicts
   - Run with `--force` flag if needed

2. **Login Issues**
   - Verify user account is active
   - Check password requirements
   - Clear browser cookies if needed

3. **Permission Errors**
   - Verify user role assignments
   - Check role hierarchy implementation
   - Ensure proper decorator usage

### Logs and Debugging

The system logs authentication events. Check your Flask logs for:
- Login attempts and failures
- Registration events
- Permission denials
- Rate limiting triggers

## Future Enhancements

Planned improvements include:
- Email verification for registration
- Password reset functionality
- Two-factor authentication
- OAuth integration (Google, GitHub)
- Audit logging for administrative actions
- User activity dashboards
