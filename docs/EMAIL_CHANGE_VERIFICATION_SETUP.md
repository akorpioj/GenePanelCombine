# Email Change Verification - Quick Setup Guide

## Prerequisites

- Existing PanelMerge installation with email verification already configured
- Database access
- Flask application with migrations support

## Installation Steps

### Step 1: Apply Database Migration

Run the database migration to add the new columns:

```bash
# Option 1: Using Flask-Migrate (recommended)
flask db upgrade

# Option 2: Run migration script directly
python migrations/versions/add_email_change_verification.py
```

This will add three new columns to the `user` table:
- `pending_email` - Stores the new email awaiting verification
- `email_change_token_hash` - Stores the hashed verification token
- `email_change_requested_at` - Timestamp of when change was requested

### Step 2: Verify Configuration

The email change verification uses the same email configuration as the existing email verification system. Ensure your `.env` file has:

```env
# Email Configuration (should already exist)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@panelmerge.com

# Token Expiration (should already exist)
VERIFICATION_TOKEN_MAX_AGE=86400  # 24 hours
```

### Step 3: Restart Application

Restart your Flask application to load the new code:

```bash
# Development
python run.py

# Production (example with gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

### Step 4: Verify Installation

Test the feature by:

1. **Login** to an existing account
2. **Navigate** to Profile → Edit Profile
3. **Change** email address to a new, valid email
4. **Verify** that:
   - Profile shows "Pending email change" notice
   - Verification email sent to new address
   - Old email still works for login
5. **Click** verification link in email
6. **Verify** that:
   - Email changed successfully
   - All sessions logged out
   - Notification sent to old email
   - Can login with new email

## Quick Test Commands

### Check Database Schema

```bash
# Connect to your database and verify columns exist
psql -d your_database -c "\d user"

# Or using Flask shell
flask shell
>>> from app.models import User
>>> User.__table__.columns.keys()
```

Should include: `pending_email`, `email_change_token_hash`, `email_change_requested_at`

### Test Email Service

```python
# In Flask shell
flask shell

>>> from app import create_app, db
>>> from app.models import User
>>> from app.email_service import email_service
>>> 
>>> app = create_app()
>>> with app.app_context():
>>>     user = User.query.first()
>>>     token = email_service.generate_email_change_token(user.id, 'test@example.com')
>>>     print(f"Token generated: {token[:30]}...")
>>>     
>>>     # Verify token
>>>     data = email_service.verify_email_change_token(token)
>>>     print(f"Token verified: {data}")
```

## New Routes Available

After installation, the following routes are available:

- `GET /auth/verify-email-change/<token>` - Verify new email address
- `POST /auth/profile/cancel-email-change` - Cancel pending email change

The existing route is enhanced:
- `POST /auth/profile/edit` - Now handles email changes with verification

## User Interface Changes

### Profile Page
- Shows pending email change notice (if any)
- Displays both current and pending email addresses
- Visual warning indicator with yellow background

### Edit Profile Page
- Enhanced email field with real-time validation
- Pending email change notice with cancel button
- Helpful guidance messages

## Troubleshooting

### Migration Fails

**Error**: Column already exists

**Solution**: The columns may already exist from a previous attempt. You can:

```sql
-- Check if columns exist
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'user' 
AND column_name IN ('pending_email', 'email_change_token_hash', 'email_change_requested_at');

-- If they exist, skip migration or manually mark as complete
flask db stamp head
```

### Import Errors

**Error**: Cannot import name 'email_service'

**Solution**: Ensure Flask application is properly initialized:

```python
# Verify in app/__init__.py that email_service is initialized
from app.email_service import email_service
email_service.init_app(app)
```

### Email Not Sending

**Error**: Verification emails not sent

**Solution**: 
1. Check SMTP configuration in `.env`
2. Verify `MAIL_SUPPRESS_SEND=False` in production
3. Check application logs for errors
4. Test with development mode first (`MAIL_SUPPRESS_SEND=True`)

### Sessions Not Revoked

**Error**: User still logged in after email change

**Solution**: 
1. Verify session_service is properly configured
2. Check Redis connection (if using Redis for sessions)
3. Review logs for session revocation errors

## Rollback Instructions

If you need to rollback the changes:

### Step 1: Rollback Database

```bash
# Using Flask-Migrate
flask db downgrade

# Or manually
psql -d your_database <<EOF
ALTER TABLE user DROP COLUMN pending_email;
ALTER TABLE user DROP COLUMN email_change_token_hash;
ALTER TABLE user DROP COLUMN email_change_requested_at;
EOF
```

### Step 2: Restore Code

```bash
# Using git
git revert <commit-hash>

# Or manually remove the added code sections
```

### Step 3: Restart Application

```bash
python run.py
```

## Support

For issues or questions:
- **Documentation**: See `docs/EMAIL_VERIFICATION_SYSTEM.md`
- **Implementation Details**: See `docs/EMAIL_CHANGE_VERIFICATION_IMPLEMENTATION.md`
- **Logs**: Check application logs for detailed error messages
- **Audit Trail**: Review audit logs for email change events

## Next Steps

After successful installation:

1. **Monitor** the feature usage through audit logs
2. **Gather** user feedback on the email change process
3. **Review** security logs for any suspicious email change attempts
4. **Consider** implementing additional enhancements (see Implementation doc)

---

**Setup Time**: ~5-10 minutes  
**Complexity**: Low  
**Risk Level**: Low (feature is isolated and well-tested)
