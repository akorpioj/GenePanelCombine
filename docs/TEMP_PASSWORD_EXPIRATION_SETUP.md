# Temporary Password Expiration - Quick Setup Guide

## Prerequisites

- Existing PanelMerge installation with admin password reset functionality
- Database access
- Flask application with migrations support

## Installation Steps

### Step 1: Apply Database Migration

Run the database migration to add the new columns:

```bash
# Using Flask-Migrate (recommended)
flask db upgrade

# Or run migration script directly
python migrations/versions/add_temp_password_expiration.py
```

This will add three new columns to the `user` table:
- `temp_password_token` - Unique token for temporary password
- `temp_password_expires_at` - Timestamp when password expires
- `temp_password_created_by` - Foreign key to admin user who created it

### Step 2: Configure Expiration Time (Optional)

Add to your `.env` file if you want to change the default 24-hour expiration:

```env
# Temporary password expiration (in hours)
TEMP_PASSWORD_EXPIRATION_HOURS=24  # Default: 24 hours

# Example configurations:
# High security: TEMP_PASSWORD_EXPIRATION_HOURS=4
# Standard: TEMP_PASSWORD_EXPIRATION_HOURS=24
# Development: TEMP_PASSWORD_EXPIRATION_HOURS=168
```

**Note**: If not set, defaults to 24 hours.

### Step 3: Restart Application

Restart your Flask application to load the new code:

```bash
# Development
python run.py

# Production (example with systemd)
sudo systemctl restart panelmerge

# Production (example with gunicorn)
sudo systemctl restart gunicorn
```

### Step 4: Verify Installation

Test the feature:

1. **Login as admin**
2. **Navigate to** Admin → Reset User Password
3. **Select a test user** and reset password
4. **Check email** - should show expiration time
5. **Login with temp password** - should work and show time remaining
6. **Wait for expiration** (or modify database) and test expired password

#### Quick Database Check

```bash
# Connect to database and verify columns exist
flask shell
>>> from app.models import User
>>> User.__table__.columns.keys()
```

Should include: `temp_password_token`, `temp_password_expires_at`, `temp_password_created_by`

## Quick Test Commands

### Check Temp Password Status

```python
# Flask shell
flask shell
>>> from app.models import User
>>> user = User.query.filter_by(username='test_user').first()
>>> 
>>> # Check if user has temp password
>>> if user.has_temp_password():
>>>     print(f"Has temp password: Yes")
>>>     print(f"Expires at: {user.temp_password_expires_at}")
>>>     print(f"Time remaining: {user.get_temp_password_time_remaining()}")
>>>     print(f"Is expired: {user.is_temp_password_expired()}")
>>> else:
>>>     print("No temp password set")
```

### Manually Test Expiration

```python
# Flask shell - simulate expired password
flask shell
>>> from app import db
>>> from app.models import User
>>> from datetime import datetime, timedelta
>>> 
>>> user = User.query.filter_by(username='test_user').first()
>>> 
>>> # Set expiration to 1 hour ago (simulate expired)
>>> user.temp_password_expires_at = datetime.now() - timedelta(hours=1)
>>> db.session.commit()
>>> 
>>> # Now try to login - should be denied
```

### Extend Expiration for Testing

```python
# Flask shell - give more time
flask shell
>>> from app import db
>>> from app.models import User
>>> from datetime import datetime, timedelta
>>> 
>>> user = User.query.filter_by(username='test_user').first()
>>> 
>>> # Extend by 24 hours from now
>>> user.temp_password_expires_at = datetime.now() + timedelta(hours=24)
>>> db.session.commit()
>>> print(f"Extended. New expiration: {user.temp_password_expires_at}")
```

## Configuration Options

### Expiration Times for Different Scenarios

```env
# High Security Environments
TEMP_PASSWORD_EXPIRATION_HOURS=4

# Standard Corporate (Default)
TEMP_PASSWORD_EXPIRATION_HOURS=24

# External Contractors
TEMP_PASSWORD_EXPIRATION_HOURS=2

# Development/Testing
TEMP_PASSWORD_EXPIRATION_HOURS=168  # 7 days
```

## User Experience Changes

### For Administrators

**Before**:
- Reset password
- Email sent with temp password
- No expiration

**After**:
- Reset password
- Email sent with temp password **and expiration time**
- Password automatically expires after configured hours
- Audit logs include expiration information

### For End Users

**Before**:
- Receive temp password email
- Login anytime
- Change password

**After**:
- Receive temp password email with expiration warning
- Login within expiration window
- See time remaining message
- Change password (clears expiration)
- If expired: Cannot login, must contact admin

## Email Template Changes

The admin password reset email now includes:

**Text Version**:
```
⏰ EXPIRATION: This temporary password will expire in 24 hours.
```

**HTML Version**:
- Yellow warning box showing expiration time
- Updated security notices mentioning expiration

## Troubleshooting

### Migration Fails

**Error**: Foreign key constraint fails

**Solution**:
```sql
-- Check for orphaned admin references
SELECT id, temp_password_created_by FROM user 
WHERE temp_password_created_by IS NOT NULL 
AND temp_password_created_by NOT IN (SELECT id FROM user);

-- Clear orphaned references
UPDATE user SET temp_password_created_by = NULL 
WHERE temp_password_created_by NOT IN (SELECT id FROM user);

-- Then re-run migration
flask db upgrade
```

### Temp Password Not Expiring

**Check**:
1. Verify migration applied: `flask db current`
2. Check system time: `date`
3. Verify configuration loaded: `echo $TEMP_PASSWORD_EXPIRATION_HOURS`
4. Check user record in database:
   ```sql
   SELECT username, temp_password_expires_at, force_password_change 
   FROM user WHERE username = 'test_user';
   ```

### User Locked Out Immediately

**Cause**: Expiration set too short or timezone issue

**Solution**:
```python
# Extend expiration for affected users
from app import db
from app.models import User
from datetime import datetime, timedelta

user = User.query.filter_by(username='username').first()
user.temp_password_expires_at = datetime.now() + timedelta(hours=24)
db.session.commit()
```

### Email Not Showing Expiration

**Check**:
1. Verify `send_admin_password_reset_email()` called with `expiration_hours` parameter
2. Check email template updated
3. Clear any email caching
4. Test with `MAIL_SUPPRESS_SEND=True` and check console output

## Rollback Instructions

If you need to rollback the changes:

### Step 1: Rollback Database

```bash
# Using Flask-Migrate
flask db downgrade

# Or manually
psql -d your_database <<EOF
ALTER TABLE user DROP CONSTRAINT fk_user_temp_password_created_by;
ALTER TABLE user DROP COLUMN temp_password_created_by;
ALTER TABLE user DROP COLUMN temp_password_expires_at;
ALTER TABLE user DROP COLUMN temp_password_token;
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

## Monitoring and Maintenance

### Check for Expired Passwords

```sql
-- Find users with expired temp passwords
SELECT username, email, temp_password_expires_at,
       NOW() - temp_password_expires_at as expired_duration
FROM user 
WHERE temp_password_expires_at < NOW() 
  AND temp_password_expires_at IS NOT NULL
ORDER BY temp_password_expires_at DESC;
```

### Clean Up Old Expired Passwords

```python
# Flask shell - cleanup script
from app import db
from app.models import User
from datetime import datetime

# Find and clear expired temp passwords
users = User.query.filter(
    User.temp_password_expires_at < datetime.now(),
    User.temp_password_expires_at.isnot(None)
).all()

for user in users:
    user.clear_temp_password()
    user.force_password_change = False
    print(f"Cleared expired temp password for {user.username}")

db.session.commit()
print(f"Cleaned up {len(users)} expired passwords")
```

### Monitor Usage

```sql
-- Count temp passwords by status
SELECT 
    CASE 
        WHEN temp_password_expires_at IS NULL THEN 'No temp password'
        WHEN temp_password_expires_at > NOW() THEN 'Active'
        ELSE 'Expired'
    END as status,
    COUNT(*) as count
FROM user
GROUP BY status;
```

## Best Practices

### For Production Deployment

1. **Test in Staging First**: 
   - Apply migration in staging environment
   - Test with various expiration times
   - Verify email templates

2. **Communicate Changes**:
   - Notify administrators of new feature
   - Update internal documentation
   - Train support staff on new behavior

3. **Set Appropriate Expiration**:
   - Review security policy
   - Consider user work patterns
   - Balance security with usability

4. **Monitor Initially**:
   - Watch audit logs for expired password attempts
   - Track user feedback
   - Adjust expiration if needed

5. **Plan for Support**:
   - Document extension procedure
   - Train admins on troubleshooting
   - Prepare FAQ for users

### For Ongoing Operations

1. **Regular Cleanup**:
   - Schedule monthly cleanup of old expired passwords
   - Remove unnecessary database records
   - Monitor database growth

2. **Audit Review**:
   - Monthly review of temp password usage
   - Look for patterns (frequent resets, frequent expirations)
   - Adjust policies as needed

3. **User Education**:
   - Remind users to check email promptly
   - Provide clear instructions in reset emails
   - Document self-service options

## Support

For issues or questions:
- **Full Documentation**: `docs/ADMIN_PASSWORD_RESET.md` (Temporary Password Expiration section)
- **Implementation Guide**: `docs/TEMP_PASSWORD_EXPIRATION_IMPLEMENTATION.md`
- **Database Schema**: Check User model in `app/models.py`
- **Audit Logs**: Review for expiration-related events
- **Support**: Contact system administrator

## Next Steps

After successful installation:

1. ✅ **Test Feature**: Reset a test user's password and verify expiration
2. ✅ **Configure Expiration**: Set appropriate time for your organization
3. ✅ **Update Policies**: Document new expiration policy
4. ✅ **Train Admins**: Ensure admins understand new behavior
5. ✅ **Monitor Usage**: Watch audit logs for first few weeks
6. ✅ **Gather Feedback**: Ask users and admins for feedback

---

**Setup Time**: ~10 minutes  
**Complexity**: Low  
**Risk Level**: Low (backward compatible)  
**Rollback**: Easy (single migration)
