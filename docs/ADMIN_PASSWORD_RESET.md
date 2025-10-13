# Admin Password Reset System

## Overview

The Admin Password Reset System allows administrators to securely reset user passwords when needed. This feature implements industry-standard security practices including temporary passwords, forced password changes, session termination, and comprehensive audit logging.

## Features

- ✅ **Admin-Only Access**: Secured with `@admin_required` decorator
- ✅ **Temporary Password Generation**: Cryptographically secure random passwords
- ✅ **Forced Password Change**: Users must change password on next login
- ✅ **Session Termination**: All user sessions revoked immediately
- ✅ **Email Notification**: User receives email with temporary password
- ✅ **Audit Logging**: Complete logging of all admin reset activities
- ✅ **User Selection Interface**: Easy-to-use admin interface
- ✅ **Security Confirmations**: Multiple confirmation steps before reset
- ✅ **Password History Integration**: Temporary password not added to history

## Architecture

### Components

1. **Admin Decorator** (`app/auth/routes.py`)
   - `admin_required()` - Enforces admin role for sensitive routes
   - Checks authentication and admin status
   - Returns 403 Forbidden if not admin

2. **Database Field** (`app/models.py`)
   - `User.force_password_change` - Boolean flag
   - Set to `True` when admin resets password
   - Cleared when user completes password change

3. **Routes** (`app/auth/routes.py`)
   - `/auth/admin/reset-user-password` - Admin interface for resetting passwords
   - `/auth/forced-password-change` - User forced password change page
   - Updated `/auth/login` - Checks force_password_change flag

4. **Email Service** (`app/email_service.py`)
   - `send_admin_password_reset_email()` - Sends temporary password to user

5. **Templates**
   - `auth/admin_reset_password.html` - Admin interface
   - `auth/forced_password_change.html` - User password change form

## Configuration

### Database Migration

The `force_password_change` field was added via migration:

```bash
flask db migrate -m "Add force_password_change field to User"
flask db upgrade
```

**Migration Details**:
- Adds `force_password_change` column to `user` table
- Type: Boolean, NOT NULL, default: False
- Server default set to 'false' for existing rows

### Email Configuration

Uses existing email configuration from `.env`:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@panelmerge.com
```

### Password Configuration

Uses existing password configuration:

```env
PASSWORD_HISTORY_LENGTH=5  # Number of past passwords to check
```

## User Flow

### Admin Password Reset Flow

```
1. Admin logs in and navigates to admin reset page
   ↓
2. Admin selects user from dropdown list
   ↓
3. System shows user details preview
   ↓
4. Admin checks confirmation box
   ↓
5. Admin clicks "Reset Password"
   ↓
6. Browser shows JavaScript confirmation dialog
   ↓
7. System generates secure temporary password
   ↓
8. System sets force_password_change=True
   ↓
9. System revokes all user sessions
   ↓
10. System commits changes to database
    ↓
11. System logs action in audit trail
    ↓
12. System sends email to user with temp password
    ↓
13. Admin sees success message
```

### User Forced Password Change Flow

```
1. User logs in with temporary password
   ↓
2. System checks force_password_change flag
   ↓
3. If True, redirect to forced-password-change page
   ↓
4. User sees warning message
   ↓
5. User enters new password (twice)
   ↓
6. System validates password requirements
   ↓
7. System checks password history
   ↓
8. If valid:
   - Update password
   - Set force_password_change=False
   - Revoke other sessions (keep current)
   - Rotate session ID
   - Log action in audit trail
   - Show success message
   - Redirect to home page
   ↓
9. User can now use application normally
```

## API Endpoints

### GET/POST /auth/admin/reset-user-password

**Purpose**: Admin interface to reset user passwords

**Access**: Admin only (`@login_required` + `@admin_required`)

**Rate Limit**: Inherits from general auth rate limits

**Request (POST)**:
```json
{
  "user_id": "123"
}
```

**Success Response**:
- Status: 302 Redirect to same page
- Flash Message: "Password reset for {username}. Email sent with temporary password."

**With Email Failure**:
- Status: 302 Redirect to same page
- Flash Message: "Password reset for {username}. Temporary password: {temp_password} (Email delivery failed - please provide this to the user securely)"

**Error Responses**:

| Error | Message | Action |
|-------|---------|--------|
| No user_id | "User ID is required" | Redirect to form |
| User not found | "User not found" | Redirect to form |
| Self-reset attempt | "Cannot reset your own password. Use the change password feature instead." | Redirect to form |
| Database error | "Failed to reset password. Please try again." | Redirect to form |

**Security Features**:
- Prevents admin from resetting their own password
- Generates 16-character cryptographically secure password
- Ensures password meets all requirements
- Temporary password NOT added to password history
- Revokes all user sessions immediately

**Temporary Password Generation**:
```python
import secrets
import string
alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
temp_password = ''.join(secrets.choice(alphabet) for _ in range(16))

# Ensure requirements met
while not (any(c.isupper() for c in temp_password) and 
          any(c.islower() for c in temp_password) and 
          any(c.isdigit() for c in temp_password)):
    temp_password = ''.join(secrets.choice(alphabet) for _ in range(16))
```

**Audit Log**:
```python
{
  "action_type": "ADMIN_ACTION",
  "user_id": 1,  # Admin's ID
  "action": "Admin admin_username reset password for user target_username",
  "resource_type": "user",
  "resource_id": "123",  # Target user's ID
  "details": {
    "target_user": "target_username",
    "target_email": "user@example.com",
    "sessions_revoked": 3,
    "force_password_change": true,
    "admin_user": "admin_username",
    "admin_id": 1
  }
}
```

---

### GET/POST /auth/forced-password-change

**Purpose**: Force user to change password after admin reset

**Access**: Authenticated users only (`@login_required`)

**Auto-Redirect**: If `force_password_change` is False, redirects to home

**Request (POST)**:
```json
{
  "new_password": "NewSecurePass123!",
  "confirm_password": "NewSecurePass123!"
}
```

**Success Response**:
- Status: 302 Redirect to `/`
- Flash Message: "Password changed successfully! You can now use the application."
- Sets `force_password_change` to False

**Error Responses**:

| Error | Message | Action |
|-------|---------|--------|
| Weak password | Specific validation error | Stay on form |
| Passwords don't match | "Passwords do not match" | Stay on form |
| Password reused | "You cannot reuse any of your last N passwords" | Stay on form |

**Password Requirements**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- Not in last 5 passwords (configurable)

**Audit Log**:
```python
{
  "action_type": "PASSWORD_CHANGE",
  "user_id": 123,
  "action": "User completed forced password change after admin reset",
  "details": {
    "sessions_revoked": 2,
    "session_rotated": true,
    "forced_change": true
  }
}
```

## Email Template

### Admin Password Reset Email

**Subject**: "Your Password Has Been Reset - PanelMerge"

**HTML Features**:
- Red header indicating security action
- Large, prominent temporary password display
- Step-by-step login instructions
- Security notice about session termination
- Warning if action not requested
- Professional branding

**Plain Text Version**:
```
Hello [User Name],

An administrator ([Admin Name]) has reset your PanelMerge account password.

Your temporary password is: [TEMP_PASSWORD]

IMPORTANT: You will be required to change this password when you log in.

Security Notice:
- All your active sessions have been logged out
- This temporary password will work only once
- Please change it immediately after logging in
- If you did not request this reset, please contact an administrator immediately

To log in:
1. Go to the PanelMerge login page
2. Use your username and the temporary password above
3. You will be prompted to create a new password

Best regards,
The PanelMerge Team
```

**HTML Template Sections**:
1. **Red Warning Header**: "🔒 Password Reset by Administrator"
2. **Admin Name**: Shows who performed the reset
3. **Password Box**: Large, monospace display of temporary password
4. **Instructions Box**: Numbered steps for logging in
5. **Security Notice**: Red alert box with important security information
6. **Footer**: Standard branding

## Security Features

### Access Control

1. **Admin-Only Access**:
   ```python
   @login_required
   @admin_required
   def admin_reset_user_password():
       ...
   ```

2. **Self-Reset Prevention**:
   ```python
   if user.id == current_user.id:
       flash('Cannot reset your own password...', 'error')
       return redirect(...)
   ```

3. **Role Verification**:
   ```python
   def admin_required(f):
       @wraps(f)
       def decorated_function(*args, **kwargs):
           if not current_user.is_admin():
               abort(403)  # Forbidden
           return f(*args, **kwargs)
       return decorated_function
   ```

### Password Security

1. **Cryptographically Secure Generation**:
   - Uses `secrets` module (not `random`)
   - 16 characters minimum
   - Includes letters, numbers, and symbols
   - Guaranteed to meet all requirements

2. **Forced Password Change**:
   - User cannot access application until password changed
   - Checked on every login attempt
   - Flag cleared only after successful change

3. **Password History**:
   - Temporary password NOT added to history
   - Allows admin to potentially reuse same temp password pattern
   - New password must not be in last 5 passwords

### Session Security

1. **Immediate Session Termination**:
   - All user sessions revoked on password reset
   - Includes web sessions and any API sessions
   - Forces re-authentication with new password

2. **Session Rotation**:
   - Current session ID rotated after password change
   - Prevents session fixation attacks
   - Other sessions remain terminated

### Audit Trail

Complete logging of all actions:

1. **Admin Password Reset**:
   - Admin username and ID
   - Target username and ID
   - Target email address
   - Number of sessions revoked
   - Timestamp

2. **User Password Change**:
   - User ID
   - Indication it was a forced change
   - Session rotation status
   - Timestamp

3. **Failed Attempts**:
   - User selection errors
   - Validation failures
   - Database errors

## User Interface

### Admin Reset Password Page

**Design Features**:
- Red theme (serious security action)
- Lock icon in header
- User selection dropdown
- User details preview
- Warning boxes
- Confirmation checkbox
- JavaScript confirmations

**Form Elements**:
1. **User Selector**:
   - Dropdown with all users except current admin
   - Shows username, email, and role
   - Sorted alphabetically

2. **User Preview**:
   - Shows selected user's details
   - Username and email displayed
   - Hidden until user selected

3. **Confirmation Checkbox**:
   - Required before submit
   - Explains consequences

4. **Submit Button**:
   - Disabled until user selected and confirmed
   - Shows loading state during submission

**Warning Boxes**:
1. **Yellow Warning (Top)**:
   - Lists all consequences of action
   - Temporary password generation
   - Session termination
   - Forced password change
   - Audit logging

2. **Blue Info (Bottom)**:
   - Steps of what happens next
   - Email notification
   - User must change password

### Forced Password Change Page

**Design Features**:
- Orange theme (warning/required action)
- Alert triangle icon
- Red alert box at top
- Two password fields
- Requirements checklist
- Security tips
- Cannot be bypassed

**Form Elements**:
1. **New Password Field**:
   - Standard password input
   - Required field

2. **Confirm Password Field**:
   - Must match new password
   - Required field

**Information Boxes**:
1. **Red Alert (Top)**:
   - Explains why password change required
   - Cannot be dismissed

2. **Blue Requirements**:
   - Checklist of password requirements
   - All 4 basic requirements
   - Password history note

3. **Yellow Security Tips**:
   - Best practices for password creation
   - Password manager recommendation

## Testing

### Manual Testing Checklist

**Admin Reset Flow**:
- [ ] Login as admin
- [ ] Navigate to admin reset page
- [ ] Verify only other users listed (not self)
- [ ] Select a user
- [ ] Verify user details preview shows
- [ ] Check confirmation box
- [ ] Confirm JavaScript dialog
- [ ] Verify success message
- [ ] Check email sent to user
- [ ] Verify temporary password in email

**User Forced Change Flow**:
- [ ] Login as reset user with temp password
- [ ] Verify redirect to forced change page
- [ ] Try to access other pages (should redirect back)
- [ ] Enter new password
- [ ] Confirm password
- [ ] Submit form
- [ ] Verify success message
- [ ] Verify redirect to home
- [ ] Verify can now use application normally

**Error Scenarios**:
- [ ] Try to reset own password as admin (should fail)
- [ ] Try weak password during forced change
- [ ] Try non-matching passwords
- [ ] Try password from history
- [ ] Try to access admin page as non-admin (403)
- [ ] Try to bypass forced change (should redirect)

**Audit Logging**:
- [ ] Check audit log for admin reset action
- [ ] Verify admin details logged
- [ ] Verify target user details logged
- [ ] Check audit log for forced password change
- [ ] Verify forced_change flag in details

**Session Management**:
- [ ] Verify all user sessions terminated after reset
- [ ] Login with new password after forced change
- [ ] Verify can create new session
- [ ] Verify old sessions still invalid

### Development Testing

**With `MAIL_SUPPRESS_SEND=True`**:
- Emails not actually sent
- Temporary password shown in success flash message
- Full flow can be tested
- No SMTP configuration needed

**Console Output Example**:
```
[DEV MODE] Email suppressed - To: user@example.com
[DEV MODE] Subject: Your Password Has Been Reset - PanelMerge
[Temporary password: Abc123!@#XyzDEF]
```

### Automated Testing

```python
# test_admin_password_reset.py

def test_admin_can_reset_user_password(admin_client, test_user):
    """Test that admin can reset user password"""
    response = admin_client.post('/auth/admin/reset-user-password', data={
        'user_id': test_user.id
    })
    
    assert response.status_code == 302
    test_user = User.query.get(test_user.id)
    assert test_user.force_password_change == True

def test_non_admin_cannot_access_reset_page(user_client):
    """Test that non-admin gets 403"""
    response = user_client.get('/auth/admin/reset-user-password')
    assert response.status_code == 403

def test_admin_cannot_reset_own_password(admin_client, admin_user):
    """Test self-reset prevention"""
    response = admin_client.post('/auth/admin/reset-user-password', data={
        'user_id': admin_user.id
    })
    
    assert b'Cannot reset your own password' in response.data

def test_forced_password_change_redirects(client, test_user):
    """Test that user with force_password_change is redirected"""
    test_user.force_password_change = True
    db.session.commit()
    
    login_response = client.post('/auth/login', data={
        'username_or_email': test_user.username,
        'password': 'password123'
    })
    
    assert b'forced-password-change' in login_response.location

def test_forced_password_change_success(client, test_user):
    """Test successful forced password change"""
    test_user.force_password_change = True
    db.session.commit()
    
    # Login
    client.post('/auth/login', data={
        'username_or_email': test_user.username,
        'password': 'password123'
    })
    
    # Change password
    response = client.post('/auth/forced-password-change', data={
        'new_password': 'NewPassword123!',
        'confirm_password': 'NewPassword123!'
    })
    
    test_user = User.query.get(test_user.id)
    assert test_user.force_password_change == False
    assert test_user.check_password('NewPassword123!')

def test_password_history_enforced_on_forced_change(client, test_user):
    """Test password history is checked during forced change"""
    test_user.set_password('OldPassword123!')
    test_user.force_password_change = True
    db.session.commit()
    
    # Login
    client.post('/auth/login', data={
        'username_or_email': test_user.username,
        'password': 'OldPassword123!'
    })
    
    # Try to reuse password
    response = client.post('/auth/forced-password-change', data={
        'new_password': 'OldPassword123!',
        'confirm_password': 'OldPassword123!'
    })
    
    assert b'cannot reuse any of your last' in response.data
```

## Troubleshooting

### Admin Cannot Access Reset Page

**Issue**: 403 Forbidden error

**Possible Causes**:
1. User is not an admin
2. User role not set correctly in database

**Solution**:
```sql
-- Check user role
SELECT username, role FROM user WHERE username = 'admin_username';

-- Update user role to ADMIN
UPDATE user SET role = 'ADMIN' WHERE username = 'admin_username';
```

### Email Not Received

**Issue**: User doesn't receive temporary password email

**Checklist**:
1. Check `MAIL_SUPPRESS_SEND` setting
2. Verify SMTP configuration
3. Check user's email address
4. Review application logs
5. Check spam/junk folder

**Fallback**:
- Temporary password shown in flash message if email fails
- Admin can provide password to user securely (phone, in-person, etc.)

### User Cannot Login After Reset

**Issue**: Temporary password doesn't work

**Possible Causes**:
1. Password copied incorrectly (whitespace, etc.)
2. Database update failed
3. User account is locked or inactive

**Solution**:
1. Check `force_password_change` flag in database
2. Verify password_hash was updated
3. Reset again if necessary
4. Check user.is_active status

### Forced Change Page Not Showing

**Issue**: User not redirected to forced change page

**Possible Causes**:
1. `force_password_change` flag not set
2. Login logic not checking flag
3. Caching issue

**Solution**:
```python
# Check flag in database
user = User.query.filter_by(username='username').first()
print(f"force_password_change: {user.force_password_change}")

# Manually set flag for testing
user.force_password_change = True
db.session.commit()
```

### Cannot Bypass Forced Change

**Issue**: User wants to access app without changing password

**Solution**: This is intentional security feature
- User MUST change password to continue
- This is by design for security
- No bypass should exist
- Contact admin if issue with temporary password

## Best Practices

### For Administrators

1. **Use Sparingly**:
   - Only reset passwords when truly necessary
   - User should use self-service reset when possible
   - Document reason for each reset

2. **Secure Communication**:
   - Email is primary method (secure)
   - If email fails, use secure alternative (phone, in-person)
   - Never send temporary password via insecure channel

3. **Immediate Action**:
   - Advise user to change password immediately
   - Provide clear instructions
   - Be available for questions

4. **Monitor Logs**:
   - Review audit logs regularly
   - Watch for unusual patterns
   - Investigate any suspicious resets

### For Users

1. **Change Password Immediately**:
   - Don't delay changing the temporary password
   - Use a strong, unique password
   - Don't reuse old passwords

2. **Contact Admin if Suspicious**:
   - If you didn't request a reset
   - If you suspect unauthorized access
   - Report immediately

3. **Follow Requirements**:
   - Meet all password requirements
   - Don't try to bypass the change
   - Choose a strong, memorable password

## Integration with Existing Features

### Password History

Integrates with password history system:
- Temporary password NOT added to history
- New password must not be in history
- Uses same `PASSWORD_HISTORY_LENGTH` config
- Prevents reuse of compromised passwords

### Audit Trail

Full integration with audit system:
- Uses `AuditService.log_action()`
- Same `AuditActionType` enum
- Consistent with other actions
- Complete event history

### Session Management

Works with enhanced session service:
- Uses `session_service.revoke_user_sessions()`
- Terminates all sessions on reset
- Rotates session ID after change
- Maintains security integrity

### Email System

Reuses existing email infrastructure:
- Same `email_service` module
- Same SMTP configuration
- Consistent email templates
- Same error handling

## Security Considerations

### Potential Risks

1. **Admin Account Compromise**:
   - If admin account compromised, attacker can reset any password
   - **Mitigation**: Strong admin passwords, 2FA (future), regular monitoring

2. **Temporary Password Interception**:
   - Email could be intercepted
   - **Mitigation**: HTTPS only, TLS email, short validity period

3. **Social Engineering**:
   - Attacker convinces admin to reset password
   - **Mitigation**: Verify reset requests, audit logging, admin training

### Recommendations

1. **Multi-Factor Authentication** (Future):
   - Require 2FA for admin actions
   - Extra verification before reset
   - Reduces compromise risk

2. **Time-Limited Temporary Passwords** (Future):
   - Expire temporary password after X hours
   - Further reduces interception window
   - Requires additional implementation

3. **Reset Approval Workflow** (Future):
   - Require second admin to approve
   - Reduces single point of failure
   - More complex implementation

4. **Reset Reason Logging** (Future):
   - Admin must provide reason
   - Better audit trail
   - Accountability improvement

## Future Enhancements

1. **Reset Reason Field**:
   - Admin provides reason for reset
   - Stored in audit log
   - Better accountability

2. **Temporary Password Expiration** ✅ **IMPLEMENTED** 13/10/2025:
   - Set expiration time for temp password (default: 24 hours)
   - More secure than indefinite validity
   - Token-based system with database tracking
   - See [Temporary Password Expiration](#temporary-password-expiration) section below

3. **Bulk Password Resets**:
   - Reset multiple users at once
   - Useful after security incidents
   - Requires careful implementation

4. **Reset Notifications**:
   - Notify other admins of resets
   - Alert on unusual patterns
   - Enhanced monitoring

5. **Reset Statistics**:
   - Dashboard of reset activities
   - Identify frequent resetters
   - Security insights

## Temporary Password Expiration

The Temporary Password Expiration feature enhances security by setting a time limit on admin-reset temporary passwords. This prevents indefinite use of temporary passwords and reduces the window of opportunity for potential attacks.

### Features

- ✅ **Configurable Expiration**: Set expiration time via environment variable (default: 24 hours)
- ✅ **Token-Based System**: Unique token generated for each temporary password
- ✅ **Automatic Expiration Check**: Login flow validates expiration before allowing access
- ✅ **Database Tracking**: Expiration time and creator tracked in database
- ✅ **User Notifications**: Email includes expiration time
- ✅ **Time Remaining Display**: Shows remaining time during password change
- ✅ **Audit Logging**: Expiration information logged in audit trail
- ✅ **Secure Cleanup**: Temporary password fields cleared after successful change

### How It Works

#### When Admin Resets Password

1. Admin initiates password reset for user
2. System generates:
   - Secure 16-character temporary password
   - Unique token (32-byte URL-safe string)
   - Expiration timestamp (current time + configured hours)
3. System stores in database:
   - `temp_password_token` - Unique identifier for this temp password
   - `temp_password_expires_at` - Timestamp when password expires
   - `temp_password_created_by` - Admin ID who created the password
4. Email sent to user includes expiration time
5. Audit log records expiration details

#### When User Attempts Login

1. User enters temporary password
2. System validates credentials
3. **NEW**: System checks if temporary password is expired:
   - If `temp_password_expires_at` < current time → Login denied
   - User sees error: "Your temporary password has expired"
   - User must contact admin for new reset
4. If not expired:
   - Login succeeds
   - User redirected to forced password change page
   - Time remaining displayed in flash message

#### When User Changes Password

1. User enters new password
2. System validates new password
3. Password updated in database
4. **NEW**: Temporary password fields cleared:
   - `temp_password_token` → NULL
   - `temp_password_expires_at` → NULL
   - `temp_password_created_by` → NULL
5. `force_password_change` flag cleared
6. User gains full access to application

### Database Schema

#### User Model Changes

```python
class User(UserMixin, db.Model):
    # ... existing fields ...
    
    # Temporary password expiration fields
    temp_password_token = db.Column(db.String(255))  # Token for temp password validation
    temp_password_expires_at = db.Column(db.DateTime)  # Expiration timestamp
    temp_password_created_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Admin ID
    
    # Helper methods
    def set_temp_password(self, password: str, token: str, admin_id: int, expiration_hours: int = 24):
        """Set temporary password with expiration"""
        
    def is_temp_password_expired(self) -> bool:
        """Check if temporary password has expired"""
        
    def has_temp_password(self) -> bool:
        """Check if user has a temporary password set"""
        
    def clear_temp_password(self):
        """Clear temporary password fields after successful password change"""
        
    def get_temp_password_time_remaining(self) -> str:
        """Get human-readable time remaining for temp password"""
```

**Migration**: Run the migration to add these fields:

```bash
# Apply migration
flask db upgrade

# Or run specific migration
python migrations/versions/add_temp_password_expiration.py
```

**Foreign Key**: `temp_password_created_by` references `user.id` (admin who created the password)

### Configuration

Add to `.env` file:

```env
# Temporary password expiration (in hours)
TEMP_PASSWORD_EXPIRATION_HOURS=24  # Default: 24 hours

# Other related settings
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

**Configuration Options**:
- `TEMP_PASSWORD_EXPIRATION_HOURS`: Hours until temporary password expires
  - Default: 24 (1 day)
  - Minimum recommended: 1 hour
  - Maximum recommended: 168 hours (7 days)

### User Experience

#### Admin Workflow

```
1. Admin resets user password
   ↓
2. System generates temp password with 24-hour expiration
   ↓
3. Admin sees success message (email sent)
   ↓
4. Audit log records expiration timestamp
```

#### User Workflow - Success Case

```
1. User receives email with temp password
   Email shows: "This password expires in 24 hours"
   ↓
2. User logs in within 24 hours
   Flash message: "You must change password. Time remaining: 23 hours 15 min"
   ↓
3. User changes password successfully
   ↓
4. Temp password fields cleared
   ↓
5. User gains full access
```

#### User Workflow - Expired Password

```
1. User attempts login after 24+ hours
   ↓
2. System checks expiration
   ↓
3. Login denied immediately
   ↓
4. User sees error: "Your temporary password has expired"
   ↓
5. User must contact administrator
   ↓
6. Admin creates new temp password reset
```

### Email Template Updates

The admin password reset email now includes expiration information:

**Text Version**:
```
Your temporary password is: [PASSWORD]

IMPORTANT: You will be required to change this password when you log in.

⏰ EXPIRATION: This temporary password will expire in 24 hours.

Security Notice:
- All your active sessions have been logged out
- This temporary password will work only until it expires
- Please change it immediately after logging in
```

**HTML Version**:
Includes:
- Yellow warning box with expiration time
- Orange danger box listing expiration in security notices
- Clear "expires in X hours" messaging

### Security Benefits

1. **Reduced Attack Window**:
   - Temporary passwords only valid for limited time
   - If password intercepted, attacker has limited window
   - Expired passwords cannot be used, even if compromised

2. **Encourages Prompt Action**:
   - Users motivated to change password quickly
   - Reduces likelihood of forgetting/losing temp password
   - Promotes better security hygiene

3. **Prevents Indefinite Access**:
   - No risk of forgotten temp passwords remaining active
   - Admin can't accidentally leave account vulnerable
   - Automatic security enforcement

4. **Audit Trail**:
   - Expiration time logged for each reset
   - Can track if users changed password before expiration
   - Identify patterns of expired password attempts

### Audit Logging

Temporary password expiration is fully integrated with audit system:

#### Admin Reset Action

```json
{
  "action_type": "ADMIN_ACTION",
  "user_id": 1,
  "action": "Admin admin_username reset password for user target_username",
  "resource_type": "user",
  "resource_id": "123",
  "details": {
    "target_user": "target_username",
    "target_email": "user@example.com",
    "sessions_revoked": 3,
    "force_password_change": true,
    "admin_user": "admin_username",
    "admin_id": 1,
    "temp_password_expires_at": "2025-10-14T15:30:00",
    "expiration_hours": 24
  },
  "timestamp": "2025-10-13T15:30:00"
}
```

#### Expired Password Login Attempt

```json
{
  "action_type": "LOGIN",
  "username_or_email": "user@example.com",
  "success": false,
  "error_message": "Temporary password expired",
  "timestamp": "2025-10-15T16:00:00"
}
```

#### Successful Password Change

```json
{
  "action_type": "PASSWORD_CHANGE",
  "user_id": 123,
  "action": "User completed forced password change after admin reset",
  "details": {
    "sessions_revoked": 2,
    "session_rotated": true,
    "forced_change": true,
    "temp_password_cleared": true
  },
  "timestamp": "2025-10-13T16:00:00"
}
```

### Error Handling

#### Expired Password Error

**User Experience**:
```
Flash Message (Red):
"Your temporary password has expired. Please contact an administrator for a new password reset."

Action: Login form displayed, user logged out immediately
```

**Backend Behavior**:
- User logged out immediately (even if credentials valid)
- Session destroyed
- Audit log records failed attempt with "Temporary password expired" error
- No access granted to any part of application

#### No Expiration Set (Legacy)

If `temp_password_expires_at` is NULL:
- System treats as no expiration (backward compatible)
- User can still login and change password
- Recommended: Admin should reset password again to set expiration

### Administration

#### Checking Temp Password Status

```python
# Flask shell or admin script
from app.models import User

user = User.query.filter_by(username='username').first()

# Check if user has temp password
if user.has_temp_password():
    print(f"Temp password set: Yes")
    print(f"Expires at: {user.temp_password_expires_at}")
    print(f"Time remaining: {user.get_temp_password_time_remaining()}")
    print(f"Is expired: {user.is_temp_password_expired()}")
    
    # Get admin who created it
    admin = User.query.get(user.temp_password_created_by)
    print(f"Created by: {admin.username}")
else:
    print("No temporary password set")
```

#### Manually Clearing Expired Passwords

```python
# Find all users with expired temp passwords
from datetime import datetime
from app import db

users_with_expired = User.query.filter(
    User.temp_password_expires_at < datetime.now(),
    User.temp_password_expires_at.isnot(None)
).all()

print(f"Found {len(users_with_expired)} users with expired temp passwords")

# Clear expired passwords
for user in users_with_expired:
    user.clear_temp_password()
    user.force_password_change = False
    print(f"Cleared expired temp password for {user.username}")

db.session.commit()
```

#### Extending Expiration Time

If a user needs more time:

```python
from datetime import datetime, timedelta
from app import db

user = User.query.filter_by(username='username').first()

# Extend by 24 hours from now
user.temp_password_expires_at = datetime.now() + timedelta(hours=24)
db.session.commit()

print(f"Extended temp password expiration for {user.username}")
print(f"New expiration: {user.temp_password_expires_at}")
```

### Testing

#### Manual Testing Checklist

- [ ] Admin resets user password
- [ ] Check email includes expiration time
- [ ] Login with temp password within expiration period
- [ ] Verify time remaining shown in flash message
- [ ] Change password successfully
- [ ] Verify temp password fields cleared in database
- [ ] Create new temp password with short expiration (1 hour)
- [ ] Wait for expiration
- [ ] Attempt login with expired password
- [ ] Verify login denied with appropriate error message
- [ ] Check audit logs for expiration information
- [ ] Verify foreign key to admin user working

#### Configuration Testing

```bash
# Test with 1-hour expiration
export TEMP_PASSWORD_EXPIRATION_HOURS=1

# Test with 48-hour expiration
export TEMP_PASSWORD_EXPIRATION_HOURS=48

# Test without expiration set (should use default)
unset TEMP_PASSWORD_EXPIRATION_HOURS
```

#### Automated Testing

```python
def test_temp_password_expiration(client, admin_user, test_user):
    """Test temporary password expiration"""
    # Admin resets password
    login(client, admin_user)
    response = client.post('/auth/admin/reset-user-password', data={
        'user_id': test_user.id
    })
    
    # Check temp password fields set
    test_user = User.query.get(test_user.id)
    assert test_user.has_temp_password()
    assert test_user.temp_password_expires_at is not None
    assert test_user.temp_password_created_by == admin_user.id
    
def test_expired_temp_password_denied(client, test_user):
    """Test login denied with expired temp password"""
    from datetime import datetime, timedelta
    
    # Set expired temp password
    test_user.temp_password_expires_at = datetime.now() - timedelta(hours=1)
    test_user.force_password_change = True
    db.session.commit()
    
    # Attempt login
    response = client.post('/auth/login', data={
        'username_or_email': test_user.username,
        'password': 'temp_password'
    })
    
    assert b'temporary password has expired' in response.data
    
def test_temp_password_cleared_after_change(client, test_user):
    """Test temp password fields cleared after password change"""
    # Setup temp password
    test_user.set_temp_password('TempPass123!', 'token123', 1, 24)
    test_user.force_password_change = True
    db.session.commit()
    
    # Login and change password
    login(client, test_user, password='TempPass123!')
    client.post('/auth/forced-password-change', data={
        'new_password': 'NewPassword123!',
        'confirm_password': 'NewPassword123!'
    })
    
    # Verify cleared
    test_user = User.query.get(test_user.id)
    assert not test_user.has_temp_password()
    assert test_user.temp_password_token is None
    assert test_user.temp_password_expires_at is None
```

### Troubleshooting

#### Temp Password Not Expiring

**Issue**: User can login even after expiration time

**Possible Causes**:
1. System time incorrect on server
2. Expiration not set properly
3. Login logic not checking expiration

**Solution**:
```python
# Check user's temp password status
user = User.query.filter_by(username='username').first()
print(f"Current time: {datetime.now()}")
print(f"Expires at: {user.temp_password_expires_at}")
print(f"Is expired: {user.is_temp_password_expired()}")
```

#### User Locked Out Immediately

**Issue**: Temp password expires too quickly

**Causes**:
- `TEMP_PASSWORD_EXPIRATION_HOURS` set too low
- System timezone misconfigured

**Solution**:
```bash
# Check configuration
echo $TEMP_PASSWORD_EXPIRATION_HOURS

# Extend user's expiration
python
>>> from app import db
>>> from app.models import User
>>> from datetime import datetime, timedelta
>>> user = User.query.filter_by(username='username').first()
>>> user.temp_password_expires_at = datetime.now() + timedelta(hours=24)
>>> db.session.commit()
```

#### Migration Errors

**Issue**: Foreign key constraint fails

**Solution**:
```sql
-- Check for orphaned references
SELECT id, temp_password_created_by FROM user 
WHERE temp_password_created_by IS NOT NULL 
AND temp_password_created_by NOT IN (SELECT id FROM user);

-- Fix orphaned references
UPDATE user SET temp_password_created_by = NULL 
WHERE temp_password_created_by IS NOT NULL 
AND temp_password_created_by NOT IN (SELECT id FROM user);
```

### Best Practices

#### For Administrators

1. **Choose Appropriate Expiration Time**:
   - Standard users: 24 hours (default)
   - Executive/critical accounts: 4-8 hours
   - External contractors: 1-2 hours
   - Adjust based on organization policy

2. **Communicate Expiration**:
   - Inform user when resetting password
   - Mention expiration time in any verbal communication
   - Ensure user has access to email

3. **Monitor Expired Passwords**:
   - Review audit logs for expired password attempts
   - May indicate phishing or social engineering
   - Contact user if multiple expired attempts

4. **Plan for After-Hours**:
   - Consider longer expiration for resets done outside business hours
   - Have procedure for emergency extensions
   - Document who can extend expirations

#### For Security Teams

1. **Set Policy-Based Expiration**:
   - Define different expiration times for different user types
   - Document rationale for each setting
   - Review and adjust based on security incidents

2. **Audit Regular Reviews**:
   - Monthly review of temp password usage
   - Identify users with frequent resets
   - Look for patterns indicating issues

3. **Automated Cleanup**:
   - Implement scheduled job to clear expired passwords
   - Alert on accounts with very old temp passwords
   - Monitor for accounts stuck in forced-change state

### Configuration Examples

#### High Security Environment

```env
# Very short expiration for maximum security
TEMP_PASSWORD_EXPIRATION_HOURS=4

# Shorter session timeout
SESSION_TIMEOUT=1800  # 30 minutes

# Stricter password requirements
PASSWORD_HISTORY_LENGTH=10
```

#### Standard Environment

```env
# Default balanced settings
TEMP_PASSWORD_EXPIRATION_HOURS=24

# Normal session timeout
SESSION_TIMEOUT=3600  # 1 hour

# Standard password requirements
PASSWORD_HISTORY_LENGTH=5
```

#### Development/Testing

```env
# Longer expiration for testing
TEMP_PASSWORD_EXPIRATION_HOURS=168  # 7 days

# Extended session for development
SESSION_TIMEOUT=28800  # 8 hours

# Minimal password history
PASSWORD_HISTORY_LENGTH=3
```

### Performance Considerations

The temporary password expiration feature has minimal performance impact:

1. **Database Queries**:
   - One additional check during login (< 1ms)
   - Index on `temp_password_expires_at` recommended for large databases

2. **Memory Usage**:
   - Three additional columns per user (negligible)
   - No additional caching required

3. **Email Delivery**:
   - No additional email overhead
   - Same email template, just includes expiration time

**Optimization Tips**:
- Create index for faster expiration queries:
  ```sql
  CREATE INDEX idx_temp_password_expires ON user(temp_password_expires_at);
  ```
- Periodic cleanup of old temp password data (optional)

## Related Documentation

- [PASSWORD_RESET_SYSTEM.md](PASSWORD_RESET_SYSTEM.md) - Self-service password reset
- [PASSWORD_HISTORY_IMPLEMENTATION.md](PASSWORD_HISTORY_IMPLEMENTATION.md) - Password history feature
- [AUTHENTICATION_SYSTEM.md](AUTHENTICATION_SYSTEM.md) - Overall authentication
- [AUDIT_TRAIL_SYSTEM.md](AUDIT_TRAIL_SYSTEM.md) - Audit logging details
- [SESSION_SECURITY_SYSTEM.md](SESSION_SECURITY_SYSTEM.md) - Session management

## Support

For issues or questions:
- **Documentation**: This file and related docs
- **Admin Route**: `/auth/admin/reset-user-password`
- **Forced Change Route**: `/auth/forced-password-change`
- **Logs**: Review application logs and audit trail
- **Contact**: Support via admin channels

---

**Version**: 1.0.0  
**Implemented**: October 13, 2025  
**Author**: PanelMerge Development Team
