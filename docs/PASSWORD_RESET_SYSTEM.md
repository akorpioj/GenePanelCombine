# Password Reset System

## Overview

The Password Reset System provides a secure, self-service password recovery mechanism for users who have forgotten their passwords. This feature implements industry-standard security practices including time-limited tokens, rate limiting, and comprehensive audit logging.

## Features

- ✅ **Self-Service Reset**: Users can reset passwords without admin intervention
- ✅ **Secure Token Generation**: Cryptographically signed, time-limited tokens
- ✅ **Email Delivery**: Professional email templates with reset links
- ✅ **Token Expiration**: Reset links expire after 1 hour (configurable)
- ✅ **Rate Limiting**: Protection against abuse and brute-force attacks
- ✅ **Audit Logging**: Complete logging of all password reset activities
- ✅ **Password Validation**: Enforces strong password requirements
- ✅ **Privacy Protection**: Doesn't reveal if email exists in system
- ✅ **User-Friendly UI**: Clear instructions and helpful feedback

## Architecture

### Components

1. **Email Service** (`app/email_service.py`)
   - Token generation with `itsdangerous`
   - Password reset email sending
   - Token validation and expiration

2. **Authentication Routes** (`app/auth/routes.py`)
   - `/auth/forgot-password` - Request reset link
   - `/auth/reset-password/<token>` - Reset password with token

3. **Templates**
   - `auth/forgot_password.html` - Email request form
   - `auth/reset_password.html` - Password reset form

4. **Integration**
   - Updated login page with "Forgot Password?" link
   - Email service with password reset template

## Configuration

### Environment Variables

Already configured in `.env`:

```env
# Token Expiration
PASSWORD_RESET_TOKEN_MAX_AGE=3600  # 1 hour (in seconds)

# Email Configuration (from email verification)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@panelmerge.com
MAIL_SUPPRESS_SEND=True  # False in production
```

### Token Expiration

Default: **1 hour** (3600 seconds)

To change:
```env
PASSWORD_RESET_TOKEN_MAX_AGE=7200  # 2 hours
PASSWORD_RESET_TOKEN_MAX_AGE=1800  # 30 minutes
```

## User Flow

### Password Reset Request

```
1. User clicks "Forgot Password?" on login page
   ↓
2. User enters email address
   ↓
3. System validates email (doesn't reveal if exists)
   ↓
4. If user exists:
   - Generate time-limited token
   - Send password reset email
   - Log action in audit trail
   ↓
5. User sees: "If email exists, reset link sent"
   ↓
6. User checks email for reset link
```

### Password Reset Completion

```
1. User clicks reset link in email
   ↓
2. Token validated (signature & expiration)
   ↓
3. If valid:
   - Show password reset form
   - Display password requirements
   ↓
4. User enters new password (twice)
   ↓
5. Password validated against requirements
   ↓
6. If valid:
   - Password updated in database
   - User logged out of all sessions
   - Audit log entry created
   - Success message shown
   ↓
7. User redirected to login page
```

### Error Scenarios

**Invalid/Expired Token:**
- User sees: "The password reset link is invalid or has expired"
- Redirected to forgot password page
- Can request new reset link

**Password Validation Fails:**
- Inline error messages shown
- User remains on reset form
- Can correct and resubmit

## API Endpoints

### GET/POST /auth/forgot-password
**Purpose**: Request password reset email

**Rate Limit**: 3 requests per hour per IP

**Request (POST)**:
```json
{
  "email": "user@example.com"
}
```

**Response**:
- Status: 200
- Message: "If the email exists in our system, a password reset link has been sent."
- Note: Same message whether email exists or not (security best practice)

**Security Features**:
- Generic response (doesn't reveal email existence)
- Rate limiting prevents email bombing
- Audit logging of all attempts

**Audit Log**:
```python
{
  "action_type": "PASSWORD_RESET",
  "action": "Password reset email sent to user@example.com",
  "resource_type": "user",
  "resource_id": "username"
}
```

---

### GET/POST /auth/reset-password/<token>
**Purpose**: Reset password using token from email

**Rate Limit**: 5 requests per hour per IP

**Request (POST)**:
```json
{
  "password": "NewSecurePass123!",
  "confirm_password": "NewSecurePass123!"
}
```

**Success Response**:
- Status: 302 Redirect to `/auth/login`
- Flash Message: "Your password has been reset successfully! You can now log in."

**Error Responses**:

| Error | Message | Action |
|-------|---------|--------|
| Invalid token | "The password reset link is invalid or has expired" | Redirect to forgot password |
| Expired token | "The password reset link is invalid or has expired" | Redirect to forgot password |
| User not found | "User not found" | Redirect to forgot password |
| Weak password | Specific validation error (e.g., "Password must be at least 8 characters") | Stay on form |
| Passwords don't match | "Passwords do not match" | Stay on form |

**Password Requirements**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number

**Audit Log**:
```python
{
  "action_type": "PASSWORD_RESET",
  "action": "Password reset completed for user: username",
  "resource_type": "user",
  "resource_id": "username",
  "details": {
    "email": "user@example.com",
    "reset_timestamp": "2025-10-13T14:30:00"
  }
}
```

## Email Template

### Password Reset Email

**Subject**: "Password Reset Request - PanelMerge"

**HTML Features**:
- Professional design with orange warning theme
- Clear "Reset Password" button
- Fallback plain text link
- 1-hour expiration notice
- Security warning if not requested
- Company branding

**Plain Text Version**:
```
Hello [User Name],

You requested a password reset for your PanelMerge account.

Click the link below to reset your password:

[Reset URL]

This link will expire in 1 hour.

If you did not request this reset, please ignore this email 
and your password will remain unchanged.

Best regards,
The PanelMerge Team
```

**HTML Template** (in `email_service.py`):
- Orange header for warning/action required
- Prominent reset button
- Warning box with expiration
- Security notice
- Professional footer

## Security Features

### Token Security

1. **Cryptographic Signing**:
   - Uses `itsdangerous.URLSafeTimedSerializer`
   - Tokens signed with `SECRET_KEY`
   - Cannot be forged or tampered
   - Includes timestamp for expiration

2. **Time-Limited Tokens**:
   - Default expiration: 1 hour
   - Configurable via `PASSWORD_RESET_TOKEN_MAX_AGE`
   - Old tokens automatically invalid after expiration

3. **Single-Use Tokens** ✅ IMPLEMENTED (October 13, 2025):
   - Tokens stored in `password_reset_tokens` database table
   - Each token can only be used once
   - Tokens marked as "used" after successful password reset
   - Prevents token reuse if intercepted
   - Automatic cleanup of expired/old tokens

### Account Lockout Protection

**NEW:** The system now includes automatic account lockout after multiple failed password reset attempts.

**Features:**
- Tracks failed password reset attempts per user
- Automatically locks accounts after threshold (default: 5 attempts)
- Configurable lockout duration (default: 24 hours)
- Email notifications to users and administrators
- Admin interface to unlock accounts
- Comprehensive audit trail

**Configuration:**
```env
ACCOUNT_LOCKOUT_THRESHOLD=5   # Failed attempts before lockout
ACCOUNT_LOCKOUT_DURATION=24   # Hours to lock account
```

**See also:** [ACCOUNT_LOCKOUT_SYSTEM.md](ACCOUNT_LOCKOUT_SYSTEM.md) for complete documentation.

### Rate Limiting

```python
# Forgot Password: 3 per hour
@limiter.limit("3 per hour")
def forgot_password():
    ...

# Reset Password: 5 per hour
@limiter.limit("5 per hour")
def reset_password(token):
    ...
```

**Protection Against**:
- Email bombing attacks
- Token brute-forcing
- System abuse
- Resource exhaustion

### Privacy Protection

**Email Existence**:
- Generic response message
- Same message whether email exists or not
- Prevents user enumeration
- Industry standard security practice

**Audit Logging**:
- All reset attempts logged
- Includes success and failure
- Non-existent email attempts tracked
- Helps detect suspicious activity

### Password Requirements

Enforced by `validate_password()` function:

```python
def validate_password(password):
    """
    Validates password strength
    Returns: (bool, str) - (is_valid, message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"
```

## User Interface

### Forgot Password Page

**Design Features**:
- Blue theme (matches login page)
- Large key icon
- Clear heading: "Forgot Your Password?"
- Simple email input form
- "Send Reset Link" button
- Links: Back to Login | Create Account

**Info Box**:
- "What happens next?" section
- Step-by-step instructions
- Check spam folder reminder
- 1-hour expiration notice

**Security Notice**:
- Small text at bottom
- Explains generic response for security

### Reset Password Page

**Design Features**:
- Green theme (positive action)
- Shield checkmark icon
- Clear heading: "Create New Password"
- Two password fields (new & confirm)
- Password requirements box
- "Reset Password" button
- Back to Login link

**Password Requirements Box**:
- Visual checklist with checkmarks
- All 4 requirements listed:
  - 8+ characters
  - Uppercase letter
  - Lowercase letter
  - Number

**Security Tips Box**:
- Yellow warning theme
- Tips for strong passwords
- Password manager recommendation

**Interactive JavaScript**:
- Real-time password validation (optional)
- Confirm password match check
- Visual feedback on requirements

### Login Page Update

**Changes**:
- "Forgot Password?" link added
- Points to `/auth/forgot-password`
- Located next to "Remember me" checkbox
- Blue color matches theme

## Testing

### Manual Testing Checklist

**Forgot Password Flow**:
- [ ] Access forgot password page from login
- [ ] Submit with valid email
- [ ] Check email received
- [ ] Click reset link in email
- [ ] Verify token accepted

**Reset Password Flow**:
- [ ] Enter new password (valid)
- [ ] Confirm password matches
- [ ] Submit form
- [ ] Verify success message
- [ ] Login with new password

**Error Scenarios**:
- [ ] Submit forgot password with invalid email format
- [ ] Submit with non-existent email (should get same message)
- [ ] Try reset link after 1 hour (should expire)
- [ ] Try reset with weak password
- [ ] Try reset with non-matching passwords
- [ ] Try reset with tampered token

**Rate Limiting**:
- [ ] Submit forgot password 4 times in hour (4th should fail)
- [ ] Submit reset password 6 times in hour (6th should fail)

**Audit Logging**:
- [ ] Check audit logs for reset request
- [ ] Check audit logs for password change
- [ ] Check audit logs for failed attempts

### Development Testing

**With `MAIL_SUPPRESS_SEND=True`**:
- Emails not actually sent
- Reset links logged to console
- Full flow can be tested
- No SMTP configuration needed

**Console Output Example**:
```
[DEV MODE] Email suppressed - To: user@example.com
[DEV MODE] Subject: Password Reset Request - PanelMerge
[Reset URL would be: http://localhost:5000/auth/reset-password/eyJ...]
```

### Automated Testing

```python
# test_password_reset.py

def test_forgot_password_request(client):
    """Test password reset request"""
    user = create_test_user()
    
    response = client.post('/auth/forgot-password', data={
        'email': user.email
    })
    
    assert b'reset link has been sent' in response.data

def test_reset_password_with_valid_token(client, email_service):
    """Test password reset with valid token"""
    user = create_test_user()
    
    # Generate token
    serializer = email_service.get_serializer('password-reset')
    token = serializer.dumps(user.email, salt='password-reset')
    
    # Reset password
    response = client.post(f'/auth/reset-password/{token}', data={
        'password': 'NewSecurePass123!',
        'confirm_password': 'NewSecurePass123!'
    })
    
    # Check password updated
    assert user.check_password('NewSecurePass123!')

def test_expired_token_rejected(client):
    """Test that expired tokens are rejected"""
    user = create_test_user()
    
    # Create expired token (simulate time passing)
    with freeze_time("2025-01-01 12:00:00"):
        token = generate_token(user.email)
    
    # Try to use it after expiration
    with freeze_time("2025-01-01 14:00:00"):  # 2 hours later
        response = client.get(f'/auth/reset-password/{token}')
        assert b'invalid or has expired' in response.data

def test_rate_limiting_on_forgot_password(client):
    """Test rate limiting on forgot password endpoint"""
    for i in range(3):
        response = client.post('/auth/forgot-password', data={
            'email': 'test@example.com'
        })
        assert response.status_code == 200
    
    # 4th request should be rate limited
    response = client.post('/auth/forgot-password', data={
        'email': 'test@example.com'
    })
    assert response.status_code == 429
```

## Troubleshooting

### Email Not Received

**Checklist**:
1. Check spam/junk folder
2. Verify email address correct
3. Check SMTP configuration
4. Check `MAIL_SUPPRESS_SEND` setting
5. Review application logs
6. Test with different email provider

**Common Issues**:
- Gmail blocking: Use App Password
- Port blocked: Try port 465 instead of 587
- Rate limits: Gmail has 500/day limit

### Token Errors

**"Invalid or expired token"**:

**Possible Causes**:
1. Token older than 1 hour
2. `SECRET_KEY` changed (invalidates all tokens)
3. Token URL corrupted
4. Token already used (if implementing single-use)

**Solution**: Request new password reset email

### Password Validation Errors

**Common Issues**:
- "Password too short" - Must be 8+ characters
- "Missing uppercase" - Add A-Z character
- "Missing lowercase" - Add a-z character  
- "Missing number" - Add 0-9 digit
- "Passwords don't match" - Retype carefully

### Rate Limiting Issues

**"Too Many Requests"**:
- Wait 1 hour to retry
- Check if legitimate user or attack
- Review rate limit settings if too restrictive
- Consider IP-based allowlisting for trusted IPs

## Audit Trail

All password reset events are logged:

### Events Logged

1. **Password Reset Requested (Exists)**:
```python
AuditActionType.PASSWORD_RESET
"Password reset email sent to user@example.com"
```

2. **Password Reset Requested (Non-existent)**:
```python
AuditActionType.PASSWORD_RESET
"Password reset attempted for non-existent email: user@example.com"
```

3. **Password Reset Completed**:
```python
AuditActionType.PASSWORD_RESET
"Password reset completed for user: username"
Details: {
    "email": "user@example.com",
    "reset_timestamp": "2025-10-13T14:30:00"
}
```

### Monitoring

**Review audit logs for**:
- High volume of reset requests (potential attack)
- Reset requests for admin accounts
- Failed reset attempts
- Unusual patterns or suspicious activity

**Query Example**:
```python
# Get all password reset events
resets = AuditLog.query.filter(
    AuditLog.action_description.like('%Password reset%')
).order_by(AuditLog.timestamp.desc()).all()
```

## Security Best Practices

### Implementation

✅ **Implemented**:
- Time-limited tokens (1 hour)
- Cryptographic token signing
- Rate limiting on endpoints
- Generic email existence response
- Strong password requirements
- Audit logging
- HTTPS required (via security service)

### Recommendations

**Consider Adding**:

1. ✅ **Single-Use Tokens** - IMPLEMENTED (October 13, 2025):
   - ✅ Created `password_reset_tokens` table
   - ✅ Tokens marked as used after password change
   - ✅ Prevents token reuse if intercepted
   - ✅ Automatic cleanup of expired tokens
   - See "Single-Use Token Implementation" section below

2. **Email Confirmation**:
   - Send confirmation email after password change
   - "Your password was changed" notification
   - Includes link to recover if unauthorized

3. **Account Lockout**:
   - Lock account after multiple failed reset attempts
   - Require admin intervention to unlock
   - Or automatic unlock after time period

4. **Multi-Factor Authentication**:
   - Require 2FA before password reset
   - Adds extra security layer
   - Prevents unauthorized resets

5. **Security Questions**:
   - Additional verification before reset
   - Backup recovery method
   - User-defined questions

## Integration with Existing Features

### Email Verification

Password reset reuses email infrastructure:
- Same `email_service.py` module
- Same token generation method
- Same email configuration
- Consistent user experience

### Audit System

Integrates with existing audit trail:
- Uses `AuditService.log_action()`
- Uses `AuditActionType.PASSWORD_RESET` for password reset events
- Consistent with other account actions
- Full event history

### Security System

Works with existing security features:
- Rate limiting (Flask-Limiter)
- HTTPS enforcement
- Session security
- CSRF protection

## Implemented Enhancements

1. ✅ **Password History** (Implemented October 13, 2025):
   - Prevents password reuse (last 5 passwords by default)
   - Stores hashed password history using bcrypt
   - Configurable history length via `PASSWORD_HISTORY_LENGTH`
   - Automatic cleanup of old entries
   - See `PASSWORD_HISTORY_IMPLEMENTATION.md` for details

## Future Enhancements

1. **Password Strength Meter**:
   - Visual indicator while typing
   - Real-time feedback
   - Suggestions for improvement

2. **Alternative Recovery**:
   - Security questions
   - SMS verification
   - Backup email address

3. ✅ **Admin Override** (Implemented October 13, 2025):
   - Admin can reset user password
   - Requires admin authentication
   - Forces password change on next login
   - Generates secure temporary password
   - Terminates all user sessions
   - Sends email notification to user
   - See `ADMIN_PASSWORD_RESET.md` for details

4. **Suspicious Activity Detection**:
   - Alert on multiple reset attempts
   - Geographic anomaly detection
   - Time-based pattern analysis

## Single-Use Token Implementation

### Overview

**Implemented**: October 13, 2025

The system now uses single-use tokens stored in a database table to prevent token reuse attacks. This adds an extra layer of security beyond time-based expiration.

### How It Works

1. **Token Generation**:
   - User requests password reset
   - System generates cryptographically signed token
   - Token stored in `password_reset_tokens` table with:
     - Token string
     - User ID
     - Created timestamp
     - Expiration timestamp
     - Used flag (default: False)
     - Used timestamp (null initially)

2. **Token Validation**:
   - User clicks reset link
   - System checks if token exists in database
   - Validates token is not used (`used = False`)
   - Validates token is not expired
   - Validates token cryptographic signature
   - Verifies token belongs to correct user

3. **Token Consumption**:
   - User successfully resets password
   - System marks token as used (`used = True`)
   - Records used timestamp
   - Token can never be used again

4. **Token Cleanup**:
   - Expired tokens automatically cleaned up
   - Old tokens (>30 days) removed periodically
   - Cleanup script: `scripts/cleanup_tokens.py`

### Database Schema

```sql
CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(500) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    used_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX ix_password_reset_tokens_token ON password_reset_tokens(token);
```

### Security Benefits

1. **Prevents Token Reuse**:
   - Intercepted tokens cannot be used twice
   - Even if attacker gets token, it's useless after first use
   - Protects against replay attacks

2. **Audit Trail**:
   - Complete record of all tokens generated
   - Track when tokens are used
   - Identify suspicious patterns

3. **Controlled Cleanup**:
   - Old tokens automatically removed
   - Prevents database bloat
   - Maintains only relevant data

### API Changes

**EmailService.send_password_reset_email()**:
```python
# Now stores token in database
token = serializer.dumps(user_email, salt='password-reset')
PasswordResetToken.create_token(user.id, token, expiration_seconds)
```

**reset_password() route**:
```python
# Now checks database for token validity
token_record = PasswordResetToken.get_valid_token(token)
if not token_record:
    # Token invalid, used, or expired
    return error_page

# After successful password reset
token_record.mark_as_used()
```

### Maintenance

**Automated Cleanup**:
```bash
# Run periodically (e.g., daily cron job)
python scripts/cleanup_tokens.py
```

**Manual Cleanup**:
```python
from app.models import PasswordResetToken

# Remove expired tokens
PasswordResetToken.cleanup_expired_tokens()

# Remove old tokens (>30 days)
PasswordResetToken.cleanup_old_tokens(days=30)
```

### Error Messages

Updated error message when token is reused:
```
"The password reset link is invalid, has expired, or has already been used."
```

This makes it clear that reused tokens are detected and rejected.

### Migration

Migration file: `migrations/versions/299ea9d516ff_add_password_reset_tokens_table_for_.py`

```bash
# Apply migration
flask db upgrade

# Rollback if needed (WARNING: loses token data)
flask db downgrade
```

---

## Related Documentation

- [EMAIL_VERIFICATION_SYSTEM.md](EMAIL_VERIFICATION_SYSTEM.md) - Email verification feature
- [AUTHENTICATION_SYSTEM.md](AUTHENTICATION_SYSTEM.md) - User authentication overview
- [AUDIT_TRAIL_SYSTEM.md](AUDIT_TRAIL_SYSTEM.md) - Audit logging details
- [SECURITY_GUIDE.md](SECURITY_GUIDE.md) - Overall security architecture
- [ACCOUNT_LOCKOUT_SYSTEM.md](ACCOUNT_LOCKOUT_SYSTEM.md) - Account lockout protection

## Support

For issues or questions:
- **Documentation**: This file
- **Email Service**: Check `app/email_service.py`
- **Routes**: Check `app/auth/routes.py`
- **Logs**: Review application logs and audit trail
- **Contact**: Support via contact form

---

**Version**: 1.0.0  
**Implemented**: October 13, 2025  
**Author**: PanelMerge Development Team
