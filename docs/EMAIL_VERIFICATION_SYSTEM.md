# Email Verification System

## Overview

The Email Verification System ensures that users provide valid email addresses during registration by requiring them to verify their email before they can log in. This security feature prevents fake accounts and confirms user identity.

## Features

- ✅ **Secure Token Generation**: Uses `itsdangerous` for time-limited verification tokens
- ✅ **Automated Email Sending**: Flask-Mail integration for reliable email delivery
- ✅ **Token Expiration**: Verification links expire after 24 hours
- ✅ **Resend Functionality**: Users can request new verification emails
- ✅ **Audit Logging**: All verification events are logged
- ✅ **Professional Email Templates**: HTML and plain text email formats
- ✅ **User-Friendly UI**: Clear instructions and status pages
- ✅ **Development Mode**: Email suppression for testing without SMTP

## Architecture

### Components

1. **EmailService** (`app/email_service.py`)
   - Token generation and validation
   - Email sending functionality
   - Verification email templates

2. **Authentication Routes** (`app/auth/routes.py`)
   - Modified registration flow
   - Email verification endpoints
   - Resend verification functionality

3. **User Model** (`app/models.py`)
   - `is_verified` field tracks email verification status

4. **Templates**
   - `auth/resend_verification.html` - Resend verification form
   - `auth/verify_status.html` - Verification status page

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@panelmerge.com
MAIL_MAX_EMAILS=50

# Development Mode (set to False in production)
MAIL_SUPPRESS_SEND=True

# Token Expiration (in seconds)
VERIFICATION_TOKEN_MAX_AGE=86400  # 24 hours
PASSWORD_RESET_TOKEN_MAX_AGE=3600  # 1 hour
```

### Gmail Setup

For Gmail SMTP:

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to Google Account → Security → 2-Step Verification → App passwords
   - Select "Mail" and your device
   - Copy the 16-character password
3. Use this password in `MAIL_PASSWORD`

### Production SMTP

For production, consider using:
- **SendGrid**: Professional email service with API
- **Amazon SES**: AWS email service
- **Mailgun**: Developer-friendly email API
- **Postmark**: Transactional email service

## User Flow

### Registration Flow

1. User fills out registration form
2. User account created with `is_verified=False`
3. Verification email sent automatically
4. User sees message: "Please check your email to verify your account"
5. User redirected to login page

### Verification Flow

1. User clicks verification link in email
2. Token validated (checks signature and expiration)
3. If valid:
   - `is_verified` set to `True`
   - Confirmation email sent
   - Success message displayed
   - User redirected to login
4. If invalid/expired:
   - Error message displayed
   - Option to resend verification

### Login Flow

1. User enters credentials
2. Password validated
3. Account active status checked
4. **Email verification checked** ⚠️
   - If not verified: Login blocked with helpful message
   - Link to resend verification provided
5. If all checks pass: User logged in

## API Endpoints

### POST /auth/register
**Purpose**: Create new user account and send verification email

**Request Body**:
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "organization": "Example Corp",
  "privacy_consent": true,
  "terms_consent": true
}
```

**Success Response**:
- Status: 302 Redirect to `/auth/login`
- Flash Message: "Registration successful! Please check your email to verify your account."

**Audit Log**:
- Registration event
- GDPR consent event
- Verification email sent event

---

### GET /auth/verify/<token>
**Purpose**: Verify user's email address using token

**Parameters**:
- `token` (path): JWT-style verification token

**Success Response**:
- Status: 302 Redirect to `/auth/login`
- Flash Message: "Email verified successfully! You can now log in."
- Confirmation email sent

**Error Responses**:
- Invalid/expired token: "The verification link is invalid or has expired."
- User not found: "User not found."
- Already verified: "Email already verified. You can log in."

**Audit Log**:
- Email verification success/failure

---

### GET/POST /auth/resend-verification
**Purpose**: Resend verification email to user

**Rate Limit**: 3 requests per hour

**GET Parameters**:
- `email` (query, optional): Pre-fill email field

**POST Request Body**:
```json
{
  "email": "john@example.com"
}
```

**Success Response**:
- Status: 200
- Flash Message: "Verification email sent! Please check your inbox."

**Security Note**: 
Does not reveal if email exists (returns same message either way)

**Audit Log**:
- Verification email resent event

---

### GET /auth/verify-status
**Purpose**: Show verification status for logged-in user

**Authentication**: Required (`@login_required`)

**Response**:
- If verified: Redirect to profile
- If not verified: Show verification status page with instructions

## Email Templates

### Verification Email

**Subject**: "Verify Your Email - PanelMerge"

**Content**:
- Personalized greeting
- Verification button/link
- Expiration notice (24 hours)
- Security message
- Professional branding

**HTML Features**:
- Responsive design
- Blue color scheme
- Clear call-to-action button
- Fallback plain text link
- Footer with copyright

### Verification Success Email

**Subject**: "Email Verified - PanelMerge"

**Content**:
- Confirmation message
- Login button
- Welcome message

## Security Features

### Token Security

1. **Cryptographic Signing**: 
   - Uses `itsdangerous.URLSafeTimedSerializer`
   - Tokens signed with `SECRET_KEY`
   - Cannot be forged or tampered

2. **Time-Limited**:
   - Tokens expire after 24 hours
   - Timestamp embedded and validated

3. **Single-Use Intent**:
   - Verification updates database state
   - Already-verified checks prevent re-use

### Rate Limiting

- Registration: 5 per minute
- Verification: 10 per hour
- Resend: 3 per hour

Prevents:
- Spam account creation
- Email bombing attacks
- Token brute-forcing

### Information Disclosure Prevention

- Resend endpoint doesn't reveal if email exists
- Generic error messages
- Consistent response times

## Audit Logging

All verification events are logged with:

```python
AuditActionType.ACCOUNT_ACTION
```

**Events Logged**:

1. **Verification Email Sent**
   ```python
   {
       "action": "Verification email sent to user@example.com",
       "resource_type": "user",
       "resource_id": "username",
       "timestamp": "2025-01-15T10:30:00"
   }
   ```

2. **Email Verified**
   ```python
   {
       "action": "Email verified for user: username",
       "resource_type": "user",
       "resource_id": "username",
       "details": {
           "email": "user@example.com",
           "verification_timestamp": "2025-01-15T10:35:00"
       }
   }
   ```

3. **Failed Login (Unverified)**
   ```python
   {
       "action": "Login failed - Email not verified",
       "username_or_email": "user@example.com",
       "error": "Email not verified"
   }
   ```

4. **Verification Email Resent**
   ```python
   {
       "action": "Verification email resent to user@example.com",
       "resource_type": "user",
       "resource_id": "username"
   }
   ```

## Database Schema

### User Model Changes

```python
class User(UserMixin, db.Model):
    # ... existing fields ...
    
    is_verified = db.Column(
        db.Boolean, 
        default=False, 
        nullable=False
    )
    
    # ... rest of model ...
```

**Migration**: No migration needed - field already exists in database

## Testing

### Development Mode

With `MAIL_SUPPRESS_SEND=True`:
- Emails not actually sent
- Verification links logged to console
- Token generation still works
- All flows can be tested

**Console Output Example**:
```
[DEV MODE] Email suppressed - To: user@example.com, Subject: Verify Your Email
[DEV MODE] Verification link would be: http://localhost:5000/auth/verify/eyJ...
```

### Manual Testing Checklist

- [ ] Register new user
- [ ] Check verification email received
- [ ] Click verification link (valid token)
- [ ] Verify success message shown
- [ ] Try to verify again (already verified)
- [ ] Try to login before verifying (should fail)
- [ ] Try to login after verifying (should succeed)
- [ ] Request resend verification
- [ ] Check rate limiting works
- [ ] Test expired token (wait 24+ hours or modify config)
- [ ] Test invalid token (malformed URL)

### Automated Testing

```python
# test_email_verification.py
def test_registration_sends_verification_email(client):
    """Test that registration sends verification email"""
    response = client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'SecurePass123!',
        'confirm_password': 'SecurePass123!',
        'privacy_consent': 'on',
        'terms_consent': 'on'
    })
    
    # Check user created but not verified
    user = User.query.filter_by(email='test@example.com').first()
    assert user is not None
    assert user.is_verified is False

def test_verify_email_with_valid_token(client, email_service):
    """Test email verification with valid token"""
    # Create unverified user
    user = create_test_user(is_verified=False)
    
    # Generate token
    token = email_service.generate_verification_token(user.email)
    
    # Verify
    response = client.get(f'/auth/verify/{token}')
    
    # Check verification
    user = User.query.get(user.id)
    assert user.is_verified is True
    assert b'Email verified successfully' in response.data

def test_login_blocked_until_verified(client):
    """Test that login is blocked for unverified users"""
    user = create_test_user(is_verified=False)
    
    response = client.post('/auth/login', data={
        'username_or_email': user.username,
        'password': 'TestPass123!'
    })
    
    assert b'verify your email' in response.data
    assert b'Resend verification' in response.data
```

## Troubleshooting

### Email Not Received

**Check**:
1. Spam/junk folder
2. Email address correct
3. SMTP credentials valid
4. MAIL_SUPPRESS_SEND=False in production
5. Check application logs for errors

**Common Issues**:
- Gmail blocking: Enable "Less secure app access" or use App Password
- Port blocked: Try port 465 with SSL instead of 587 with TLS
- Rate limits: Gmail has sending limits (500/day for free accounts)

### Token Errors

**"Invalid or expired token"**:
- Token older than 24 hours
- SECRET_KEY changed (invalidates all tokens)
- Token URL corrupted (check email client)

**Fix**: Request new verification email

### Login Still Blocked After Verification

**Check**:
1. Browser cache - clear and reload
2. Database - verify `is_verified=True`
3. Session - logout and login again

### Development Testing

**Can't receive emails locally**:
- Set `MAIL_SUPPRESS_SEND=True`
- Check console logs for verification links
- Copy link from logs to verify

## Migration Guide

### From No Email Verification

If upgrading existing system:

1. **Existing Users**: Run migration to set `is_verified=True`
   ```python
   # One-time script
   from app import create_app, db
   from app.models import User
   
   app = create_app()
   with app.app_context():
       User.query.update({User.is_verified: True})
       db.session.commit()
       print("All existing users marked as verified")
   ```

2. **New Users**: Will require verification automatically

3. **Communication**: Notify users of new security feature

## Best Practices

### Email Content

✅ **Do**:
- Use clear, action-oriented subject lines
- Include company branding
- Provide both HTML and plain text versions
- Make links prominent and clickable
- Include expiration time
- Add security notice

❌ **Don't**:
- Use generic subjects like "Verify"
- Send from personal email addresses
- Include sensitive information
- Use URL shorteners
- Make emails look like spam

### User Experience

✅ **Do**:
- Explain why verification is required
- Provide clear instructions
- Offer resend option
- Show helpful error messages
- Include support contact

❌ **Don't**:
- Block users permanently
- Hide error details
- Make process confusing
- Ignore edge cases

### Security

✅ **Do**:
- Use strong tokens with expiration
- Log all verification events
- Rate limit endpoints
- Validate tokens server-side
- Use HTTPS in production

❌ **Don't**:
- Use predictable tokens
- Accept tokens after verification
- Expose user existence
- Skip rate limiting
- Use HTTP links

## Future Enhancements

1. **Email Verification Reminders**
   - Send reminder after 3 days
   - Send reminder after 7 days
   - Auto-delete unverified accounts after 30 days

2. **Multi-Factor Authentication**
   - Build on email verification
   - Add SMS verification
   - Add authenticator app support

3. **Email Change Verification**
   - Verify new email when user changes it
   - Keep old email active until verified

4. **Magic Link Login**
   - Passwordless authentication
   - Email-based one-time links

5. **Email Preferences**
   - User can choose email frequency
   - Opt-in/out of notifications

## Related Documentation

- [AUTHENTICATION_SYSTEM.md](AUTHENTICATION_SYSTEM.md) - User authentication overview
- [GDPR_COMPLIANCE_IMPLEMENTATION.md](GDPR_COMPLIANCE_IMPLEMENTATION.md) - Data protection
- [AUDIT_TRAIL_SYSTEM.md](AUDIT_TRAIL_SYSTEM.md) - Audit logging details
- [SECURITY_GUIDE.md](SECURITY_GUIDE.md) - Overall security architecture

## Support

For issues or questions:
- Check logs: Application logs contain detailed error messages
- Review audit trail: All verification events are logged
- Contact support: [Contact form](http://localhost:5000/contact)

---

**Version**: 1.0.0  
**Last Updated**: 2025-01-15  
**Author**: PanelMerge Development Team
