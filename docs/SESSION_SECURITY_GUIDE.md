# Session Security Implementation Guide

## Quick Implementation Guide

This guide provides step-by-step instructions for implementing and using the Enhanced Session Security System in PanelMerge.

## Prerequisites

- Flask application with Redis available
- User authentication system in place
- Audit logging system configured

## Implementation Steps

### 1. Service Integration

The session service is automatically initialized in the app factory:

```python
# app/__init__.py
from .session_service import init_session_service

def create_app(config_name=None):
    app = Flask(__name__)
    
    # ... other initialization
    
    # Initialize enhanced session management
    init_session_service(app)
    
    return app
```

### 2. Authentication Integration

Update your login route to use enhanced sessions:

```python
# app/auth/routes.py
from ..session_service import session_service

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if user and user.check_password(password):
        # Standard Flask-Login
        login_user(user, remember=remember_me)
        
        # Enhanced session creation
        session_token = session_service.create_session(
            user_id=user.id,
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr,
            remember_me=remember_me
        )
        
        return redirect(url_for('main.index'))
```

Update your logout route:

```python
@auth_bp.route('/logout')
@login_required
def logout():
    # Enhanced session destruction
    session_service.destroy_session()
    
    # Standard Flask-Login logout
    logout_user()
    
    return redirect(url_for('main.index'))
```

### 3. Session Management Routes

Add session management routes to your authentication blueprint:

```python
@auth_bp.route('/profile/sessions')
@login_required
def view_sessions():
    """View active sessions for current user"""
    try:
        sessions = session_service.get_user_sessions(current_user.id)
        return render_template('auth/sessions.html', sessions=sessions)
    except Exception as e:
        flash('Unable to retrieve session information.', 'error')
        return redirect(url_for('auth.profile'))

@auth_bp.route('/profile/sessions/revoke', methods=['POST'])
@login_required
def revoke_sessions():
    """Revoke all other sessions for current user"""
    try:
        revoked_count = session_service.revoke_user_sessions(
            current_user.id, 
            except_current=True
        )
        flash(f'Successfully revoked {revoked_count} other sessions.', 'success')
    except Exception as e:
        flash('Failed to revoke sessions. Please try again.', 'error')
    
    return redirect(url_for('auth.view_sessions'))

@auth_bp.route('/profile/sessions/revoke/<session_id>', methods=['POST'])
@login_required
def revoke_individual_session(session_id):
    """Revoke a specific session for current user"""
    try:
        # Get user's current sessions to validate the session belongs to them
        user_sessions = session_service.get_user_sessions(current_user.id)
        session_to_revoke = None
        
        # Find the session by partial ID
        for sess in user_sessions:
            if sess['session_id'].startswith(session_id.replace('...', '')):
                session_to_revoke = sess
                break
        
        if not session_to_revoke:
            flash('Session not found or does not belong to you.', 'error')
            return redirect(url_for('auth.view_sessions'))
        
        # Prevent user from revoking their current session
        if session_to_revoke['is_current']:
            flash('Cannot revoke your current session. Use logout instead.', 'error')
            return redirect(url_for('auth.view_sessions'))
        
        # Get the full session token from Redis
        user_sessions_key = f"user_sessions:{current_user.id}"
        session_tokens = session_service.redis_client.smembers(user_sessions_key)
        
        full_token = None
        for token in session_tokens:
            if token.startswith(session_id.replace('...', '')):
                full_token = token
                break
        
        if full_token:
            # Revoke the specific session
            session_service.redis_client.delete(f"session:{full_token}")
            session_service.redis_client.srem(user_sessions_key, full_token)
            
            flash(f'Session {session_id} has been revoked successfully.', 'success')
            
            # Log session revocation
            AuditService.log_action(
                action_type=AuditActionType.SESSION_MANAGEMENT,
                user_id=current_user.id,
                action_description=f'User revoked individual session {session_id}',
                details={'revoked_session_id': session_id}
            )
        else:
            flash('Session not found in storage.', 'error')
            
    except Exception as e:
        flash('Failed to revoke session. Please try again.', 'error')
    
    return redirect(url_for('auth.view_sessions'))
```

### 4. Individual Session Revocation

Add support for revoking specific sessions:

```python
@auth_bp.route('/profile/sessions/revoke/<session_id>', methods=['POST'])
@login_required
def revoke_individual_session(session_id):
    """Revoke a specific session for current user"""
    try:
        # Get user's current sessions to validate the session belongs to them
        user_sessions = session_service.get_user_sessions(current_user.id)
        session_to_revoke = None
        
        # Find the session by partial ID
        for sess in user_sessions:
            if sess['session_id'].startswith(session_id.replace('...', '')):
                session_to_revoke = sess
                break
        
        if not session_to_revoke:
            flash('Session not found or does not belong to you.', 'error')
            return redirect(url_for('auth.view_sessions'))
        
        # Prevent user from revoking their current session
        if session_to_revoke['is_current']:
            flash('Cannot revoke your current session. Use logout instead.', 'error')
            return redirect(url_for('auth.view_sessions'))
        
        # Get the full session token from Redis
        user_sessions_key = f"user_sessions:{current_user.id}"
        session_tokens = session_service.redis_client.smembers(user_sessions_key)
        
        full_token = None
        for token in session_tokens:
            if token.startswith(session_id.replace('...', '')):
                full_token = token
                break
        
        if full_token:
            # Revoke the specific session
            session_service.redis_client.delete(f"session:{full_token}")
            session_service.redis_client.srem(user_sessions_key, full_token)
            
            flash(f'Session {session_id} has been revoked successfully.', 'success')
            
            # Log session revocation
            AuditService.log_action(
                action_type=AuditActionType.SESSION_MANAGEMENT,
                user_id=current_user.id,
                action_description=f'User revoked individual session {session_id}',
                details={'revoked_session_id': session_id}
            )
        else:
            flash('Session not found in storage.', 'error')
            
    except Exception as e:
        flash('Failed to revoke session. Please try again.', 'error')
    
    return redirect(url_for('auth.view_sessions'))
```

### 5. Enhanced Password Change

Implement secure password change with session management:

```python
@auth_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        # ... password validation logic
        
        try:
            # Update password
            current_user.set_password(new_password)
            db.session.commit()
            
            # Revoke all other sessions for security
            revoked_count = session_service.revoke_user_sessions(
                current_user.id, 
                except_current=True
            )
            
            # Rotate current session
            session_service._rotate_session_id()
            
            flash('Password changed successfully! Other sessions have been logged out for security.', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            flash('Failed to change password. Please try again.', 'error')
    
    return render_template('auth/change_password.html')
```

### 6. Privilege Escalation

Handle privilege escalation securely:

```python
@auth_bp.route('/admin/users')
@login_required
def admin_users():
    """Admin view of users (requires admin role)"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    # Escalate privileges for this session
    session_service.escalate_privileges('admin')
    
    users = User.query.all()
    return render_template('auth/admin_users.html', users=users)
```

## Configuration

### Environment Variables

Set these environment variables for session security:

```bash
# Session timeout in seconds
SESSION_TIMEOUT=3600

# Maximum concurrent sessions per user
MAX_CONCURRENT_SESSIONS=5

# Session rotation interval in seconds
SESSION_ROTATION_INTERVAL=1800

# Enable session analytics
ENABLE_SESSION_ANALYTICS=true

# Redis URL for session storage
REDIS_URL=redis://localhost:6379
```

### Development vs Production Settings

#### Development Configuration
```python
class DevelopmentConfig(Config):
    SESSION_TIMEOUT = 3600                    # 1 hour
    MAX_CONCURRENT_SESSIONS = 5               # 5 sessions
    SESSION_ROTATION_INTERVAL = 1800          # 30 minutes
    ENABLE_SESSION_ANALYTICS = True
```

#### Production Configuration
```python
class ProductionConfig(Config):
    SESSION_TIMEOUT = 1800                    # 30 minutes (stricter)
    MAX_CONCURRENT_SESSIONS = 3               # 3 sessions (stricter)  
    SESSION_ROTATION_INTERVAL = 900           # 15 minutes (more frequent)
    ENABLE_SESSION_ANALYTICS = True
```

## Frontend Templates

### Session Management Dashboard

Create `templates/auth/sessions.html`:

```html
{% extends "main/base.html" %}

{% block title %}Active Sessions - PanelMerge{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="max-w-4xl mx-auto">
        <div class="bg-white rounded-lg shadow-md p-6">
            <h1 class="text-2xl font-bold text-gray-800 mb-6">Active Sessions</h1>
            
            {% if sessions|length > 1 %}
            <form method="POST" action="{{ url_for('auth.revoke_sessions') }}" class="mb-6">
                <button type="submit" 
                        class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded"
                        onclick="return confirm('Revoke all other sessions?')">
                    Revoke All Other Sessions
                </button>
            </form>
            {% endif %}

            {% for session in sessions %}
            <div class="border rounded-lg p-4 mb-4 {% if session.is_current %}bg-green-50{% else %}bg-gray-50{% endif %}">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        {% if session.is_current %}
                        <span class="bg-green-100 text-green-800 px-2 py-1 rounded text-xs mb-2 inline-block">
                            Current Session
                        </span>
                        {% endif %}
                        
                        <div class="grid grid-cols-2 gap-4 text-sm">
                            <div><strong>IP:</strong> {{ session.ip_address }}</div>
                            <div><strong>Created:</strong> {{ session.created_at.strftime('%Y-%m-%d %H:%M') }}</div>
                            <div><strong>Last Active:</strong> {{ session.last_activity.strftime('%Y-%m-%d %H:%M') }}</div>
                            <div><strong>Browser:</strong> {{ session.user_agent[:50] }}...</div>
                        </div>
                    </div>
                    
                    {% if not session.is_current %}
                    <div class="ml-4">
                        <form method="POST" action="{{ url_for('auth.revoke_individual_session', session_id=session.session_id.replace('...', '')) }}" class="inline">
                            <button type="submit" 
                                    class="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm"
                                    onclick="return confirm('Revoke this session?')">
                                Revoke
                            </button>
                        </form>
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
{% endblock %}
```

### Profile Page Integration

Add session management link to your profile page:

```html
<!-- In templates/auth/profile.html -->
<div class="mt-8">
    <a href="{{ url_for('auth.edit_profile') }}" 
       class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mr-3">
        Edit Profile
    </a>
    <a href="{{ url_for('auth.change_password') }}" 
       class="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded mr-3">
        Change Password
    </a>
    <a href="{{ url_for('auth.view_sessions') }}" 
       class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">
        Manage Sessions
    </a>
</div>
```

## Testing

### Test Session Security

Run the comprehensive test suite:

```bash
python scripts/test_session_security.py
```

### Manual Testing

1. **Login and check session creation**:
   - Login with valid credentials
   - Verify session appears in Redis
   - Check audit log for session creation event

2. **Test session rotation**:
   - Wait for rotation interval
   - Verify session token changes
   - Confirm old token is invalidated

3. **Test hijacking detection**:
   - Change User-Agent manually
   - Verify session is invalidated
   - Check security event logging

4. **Test concurrent sessions**:
   - Login from multiple browsers
   - Verify session limit enforcement
   - Test oldest session cleanup

5. **Test privilege escalation**:
   - Access admin area
   - Verify session rotation occurs
   - Check privilege level updates

## Monitoring

### View Session Analytics

Check Redis for analytics data:

```bash
# Connect to Redis
redis-cli

# View daily active sessions
SMEMBERS daily_active_sessions:2025-07-27

# View user sessions
SMEMBERS user_sessions:123

# View session data
HGETALL session:abc123...
```

### Check Audit Logs

Query audit logs for session events:

```sql
-- View recent session events
SELECT * FROM audit_log 
WHERE action_type = 'SESSION_MANAGEMENT' 
ORDER BY timestamp DESC 
LIMIT 20;

-- View session events for specific user
SELECT * FROM audit_log 
WHERE action_type = 'SESSION_MANAGEMENT' 
AND user_id = 123 
ORDER BY timestamp DESC;
```

## Troubleshooting

### Common Issues

1. **Redis Connection Errors**:
   - Check Redis server is running
   - Verify REDIS_URL configuration
   - Test Redis connectivity: `redis-cli ping`

2. **Session Validation Failures**:
   - Check User-Agent consistency
   - Verify IP address handling
   - Review session timeout settings

3. **Audit Logging Issues**:
   - Ensure SESSION_MANAGEMENT enum exists
   - Check database permissions
   - Verify encryption service is working

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger('app.session_service').setLevel(logging.DEBUG)
logging.getLogger('app.audit_service').setLevel(logging.DEBUG)
```

## Security Best Practices

### 1. Configuration Security

- Use strong Redis passwords
- Configure Redis to bind to localhost only
- Set appropriate session timeouts
- Limit concurrent sessions reasonably

### 2. Network Security

- Use HTTPS in production
- Consider IP allowlisting for admin accounts
- Monitor for unusual session patterns
- Implement rate limiting on login attempts

### 3. Monitoring

- Monitor Redis memory usage
- Set up alerts for security events
- Regular audit log reviews
- Track session analytics trends

## API Reference

### Key Methods

```python
# Create session
session_service.create_session(user_id, user_agent, ip_address, remember_me)

# Destroy session  
session_service.destroy_session(session_token)

# Get user sessions
session_service.get_user_sessions(user_id)

# Revoke sessions
session_service.revoke_user_sessions(user_id, except_current=True)

# Escalate privileges
session_service.escalate_privileges('admin')
```

This implementation guide provides everything needed to integrate and use the Enhanced Session Security System effectively in your application.
