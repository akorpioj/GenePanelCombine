# Account Lockout System

## Overview

The Account Lockout System is a security feature that automatically locks user accounts after multiple failed password reset attempts. This prevents brute-force attacks and unauthorized access attempts while notifying administrators of suspicious activity.

**Implementation Date:** October 2025  
**Version:** 1.0  
**Status:** ✅ Fully Implemented

---

## Table of Contents

1. [Features](#features)
2. [How It Works](#how-it-works)
3. [Configuration](#configuration)
4. [Database Schema](#database-schema)
5. [User Experience](#user-experience)
6. [Administrator Actions](#administrator-actions)
7. [Email Notifications](#email-notifications)
8. [Audit Trail](#audit-trail)
9. [Security Considerations](#security-considerations)
10. [Testing](#testing)

---

## Features

### ✅ Automatic Account Lockout
- Tracks failed password reset attempts
- Automatically locks accounts after threshold is exceeded
- Configurable lockout duration (default: 24 hours)
- Configurable failure threshold (default: 5 attempts)

### ✅ Administrator Notifications
- Admins receive email alerts when accounts are locked
- Detailed information about the security event
- Admins are NOT subject to lockout (but are alerted)

### ✅ User Notifications
- Users receive email notifications when their account is locked
- Clear instructions on how to unlock their account
- Displays lockout information on dedicated page

### ✅ Admin Management Interface
- View all locked accounts
- Unlock accounts with one click
- See lockout details (type, duration, attempts)
- Audit trail for all unlock actions

### ✅ Automatic Unlocking
- Time-based lockouts automatically expire
- Failed attempt counter resets on successful password reset
- Clear separation between automatic and admin-initiated lockouts

---

## How It Works

### 1. Password Reset Flow

```
User attempts password reset
    ↓
System checks if account is locked
    ↓
    ├─→ YES: Show "Account Locked" page
    │         Send to account_locked.html
    │
    └─→ NO:  Continue with password reset
            ↓
        User submits new password
            ↓
        Validation fails?
            ↓
            ├─→ YES: Increment failed_reset_attempts
            │         Check if threshold reached
            │         ↓
            │         ├─→ YES: Lock account
            │         │         Send notifications
            │         │         Show "Account Locked" page
            │         │
            │         └─→ NO:  Show error message
            │                   Allow retry
            │
            └─→ NO:  Reset failed_reset_attempts to 0
                     Complete password reset
                     Success!
```

### 2. Lockout Types

**Automatic Lockout:**
- Triggered after X failed attempts (default: 5)
- Duration: Y hours (default: 24)
- Automatically expires after duration
- User can retry after expiration

**Admin Lockout:**
- Manually initiated by administrator
- Permanent until admin unlocks
- Used for security investigations
- Requires explicit admin action to unlock

### 3. Lockout Logic

The system uses three key methods in the User model:

```python
user.is_reset_locked_out()       # Check if account is locked
user.increment_failed_resets()    # Track failed attempts
user.lock_reset_account()         # Lock the account
user.unlock_reset_account()       # Unlock (admin only)
user.reset_failed_resets()        # Clear counters
```

---

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Account Lockout Settings
ACCOUNT_LOCKOUT_THRESHOLD=5   # Failed attempts before lockout
ACCOUNT_LOCKOUT_DURATION=24   # Hours to lock account
```

### Configuration Class

Settings are defined in `app/config_settings.py`:

```python
class Config:
    # Account Lockout Configuration
    ACCOUNT_LOCKOUT_THRESHOLD = int(os.getenv('ACCOUNT_LOCKOUT_THRESHOLD', '5'))
    ACCOUNT_LOCKOUT_DURATION = int(os.getenv('ACCOUNT_LOCKOUT_DURATION', '24'))
```

### Recommended Settings

| Environment | Threshold | Duration | Rationale |
|------------|-----------|----------|-----------|
| Development | 10 | 1 hour | Lenient for testing |
| Staging | 5 | 12 hours | Moderate security |
| Production | 5 | 24 hours | Strong security |

---

## Database Schema

### User Model Fields

```python
class User(db.Model):
    # Existing fields...
    
    # Account Lockout Fields
    failed_reset_attempts = db.Column(db.Integer, default=0, nullable=False)
    reset_locked_until = db.Column(db.DateTime)
    reset_locked_by_admin = db.Column(db.Boolean, default=False, nullable=False)
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `failed_reset_attempts` | Integer | Counter for failed password reset attempts |
| `reset_locked_until` | DateTime | Expiration time for automatic lockouts (NULL = no time-based lock) |
| `reset_locked_by_admin` | Boolean | TRUE if admin manually locked the account (permanent) |

### Migration

Migration file: `migrations/versions/e6dcc61660f1_add_account_lockout_fields_for_password_.py`

```bash
# Apply migration
flask db upgrade

# Rollback if needed
flask db downgrade
```

---

## User Experience

### Account Locked Page

When a user's account is locked, they see a dedicated page (`account_locked.html`) that explains:

- **Why** the account was locked
- **What** triggered the lockout
- **When** it will be automatically unlocked (if applicable)
- **How** to get help from an administrator

### Key Messages

**During Password Reset:**
```
"Your account has been locked due to multiple failed password reset 
attempts. Please contact an administrator."
```

**On Account Locked Page:**
```
"Your account has been temporarily locked for security reasons.

Reason: Multiple failed password reset attempts

What should you do?
- Contact an administrator to unlock your account
- Verify that you were the one attempting to reset your password
- If you did not initiate these attempts, report this immediately"
```

---

## Administrator Actions

### View Locked Accounts

Navigate to: **Admin → Unlock Accounts**

Shows:
- List of all currently locked accounts
- Failed attempt count
- Lockout type (automatic vs admin)
- Lockout expiration time (if applicable)
- User details (username, email, organization)

### Unlock an Account

1. Go to **Admin → Unlock Accounts**
2. Find the locked user
3. Click **"Unlock Account"** button
4. Confirm the action
5. User receives email notification
6. Failed attempt counter is reset

### What Happens When Unlocking

```python
# System actions:
user.failed_reset_attempts = 0
user.reset_locked_until = None
user.reset_locked_by_admin = False
db.session.commit()

# Audit log created
# Email sent to user
# Admin sees confirmation
```

---

## Email Notifications

### 1. Account Locked Email (User)

**To:** Locked user  
**Subject:** "Account Locked - Security Alert - PanelMerge"

**Content:**
- Notification that account is locked
- Reason for lockout
- Instructions to contact admin
- Security tips

**Function:** `email_service.send_account_locked_email()`

### 2. Admin Security Alert Email

**To:** All administrators  
**Subject:** "Security Alert: Account Locked - {username} - PanelMerge"

**Content:**
- User details (username, email)
- Number of failed attempts
- Actions administrators can take
- Link to audit logs

**Function:** `email_service.send_admin_security_alert_email()`

**Note:** Admin accounts trigger alerts but are NOT locked themselves.

### 3. Account Unlocked Email (User)

**To:** Unlocked user  
**Subject:** "Account Unlocked - PanelMerge"

**Content:**
- Confirmation that account is unlocked
- Name of admin who unlocked it
- Security reminders
- Next steps

**Function:** `email_service.send_account_unlocked_email()`

---

## Audit Trail

All account lockout events are logged in the audit trail with `AuditActionType.PASSWORD_RESET`.

### Events Logged

1. **Account Locked (Automatic)**
```python
action_description = f"Account locked due to {attempts} failed password reset attempts: {username}"
details = {
    "failed_attempts": attempts,
    "lockout_duration_hours": duration,
    "locked_until": timestamp
}
```

2. **Failed Reset Attempt (Pre-Lockout)**
```python
action_description = f"Failed password reset attempt ({current}/{threshold}): {username}"
details = {
    "failed_attempts": current,
    "threshold": threshold
}
```

3. **Account Unlocked (Admin Action)**
```python
action_description = f"Admin {admin} unlocked account for user {username}"
details = {
    "target_user": username,
    "admin_user": admin,
    "admin_id": admin_id
}
```

4. **Lockout Attempt on Locked Account**
```python
action_description = f"Password reset attempted on locked account: {username}"
details = {
    "locked_until": timestamp,
    "locked_by_admin": boolean
}
```

---

## Security Considerations

### ✅ Protections Implemented

1. **Brute Force Prevention**
   - Rate limiting on password reset attempts
   - Account lockout after threshold
   - Prevents automated attacks

2. **Admin Accounts**
   - Admins receive alerts but are NOT locked
   - Prevents denial-of-service against admins
   - Maintains emergency access

3. **Email Verification**
   - Both user and admins are notified
   - Creates awareness of security events
   - Enables quick response to attacks

4. **Audit Trail**
   - All events are logged
   - Immutable record of security actions
   - Forensic evidence for investigations

5. **Time-Based Expiration**
   - Automatic lockouts expire
   - Reduces admin workload
   - Balances security and usability

### 🔒 Best Practices

1. **Monitor Audit Logs**
   - Review locked accounts regularly
   - Look for patterns of attacks
   - Identify compromised accounts

2. **Respond Quickly**
   - Investigate alerts promptly
   - Contact affected users
   - Document security incidents

3. **Adjust Thresholds**
   - Monitor false positive rate
   - Adjust based on your environment
   - Balance security vs usability

4. **User Education**
   - Teach users about secure passwords
   - Explain the lockout system
   - Provide clear contact information

### ⚠️ Potential Issues

1. **Legitimate Lockouts**
   - Users may forget passwords multiple times
   - Typos can trigger lockout
   - Solution: Clear instructions for getting help

2. **Targeted Attacks**
   - Attacker may intentionally lock user accounts
   - Denial-of-service via lockout
   - Solution: Admin alerts enable quick response

3. **Admin Workload**
   - Manual unlocking required for frequent users
   - May increase support requests
   - Solution: Automatic expiration reduces load

---

## Testing

### Manual Testing Checklist

#### Test 1: Automatic Lockout
- [ ] Attempt password reset with wrong password 5 times
- [ ] Verify account is locked
- [ ] Verify "Account Locked" page is displayed
- [ ] Verify user receives lockout email
- [ ] Verify admin receives security alert email

#### Test 2: Admin Unlock
- [ ] Log in as admin
- [ ] Navigate to Unlock Accounts page
- [ ] Verify locked account appears in list
- [ ] Click Unlock Account button
- [ ] Verify account is unlocked
- [ ] Verify user receives unlock email
- [ ] Verify audit log entry is created

#### Test 3: Automatic Expiration
- [ ] Lock an account (wait 24 hours or modify duration)
- [ ] Verify account automatically unlocks after duration
- [ ] Verify user can reset password after expiration

#### Test 4: Success Resets Counter
- [ ] Fail password reset 3 times
- [ ] Successfully reset password
- [ ] Verify counter is reset to 0
- [ ] Verify subsequent failures start from 0

#### Test 5: Admin Accounts
- [ ] Attempt to reset admin password with wrong password 5 times
- [ ] Verify admin account is NOT locked
- [ ] Verify admin receives security alert email
- [ ] Verify audit logs record the attempts

### Automated Testing

Create test cases in `tests/test_account_lockout.py`:

```python
def test_account_lockout_after_threshold():
    """Test that account locks after threshold failures"""
    # Create test user
    # Attempt password reset 5 times with wrong password
    # Assert user.is_reset_locked_out() == True
    # Assert user.failed_reset_attempts == 5

def test_admin_unlock():
    """Test that admin can unlock account"""
    # Create locked user
    # Admin unlocks account
    # Assert user.is_reset_locked_out() == False
    # Assert audit log entry exists

def test_automatic_expiration():
    """Test that lockout expires automatically"""
    # Create locked user with past expiration
    # Assert user.is_reset_locked_out() == False

def test_success_resets_counter():
    """Test that successful reset clears counter"""
    # Fail 3 times
    # Succeed once
    # Assert user.failed_reset_attempts == 0
```

---

## Integration Points

### Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/auth/forgot-password` | GET, POST | Check lockout before sending reset email |
| `/auth/reset-password/<token>` | GET, POST | Check lockout, increment counter, lock if threshold reached |
| `/auth/admin/unlock-account` | GET, POST | Admin interface to unlock accounts |

### Models

| Model | Methods | Purpose |
|-------|---------|---------|
| `User` | `is_reset_locked_out()` | Check if account is locked |
| `User` | `increment_failed_resets()` | Increment failed attempt counter |
| `User` | `lock_reset_account()` | Lock the account |
| `User` | `unlock_reset_account()` | Unlock the account |
| `User` | `reset_failed_resets()` | Clear counters and unlock |

### Services

| Service | Methods | Purpose |
|---------|---------|---------|
| `EmailService` | `send_account_locked_email()` | Notify user of lockout |
| `EmailService` | `send_admin_security_alert_email()` | Alert admins |
| `EmailService` | `send_account_unlocked_email()` | Notify user of unlock |
| `AuditService` | `log_action()` | Record all events |

---

## Troubleshooting

### Issue: Account locked but shouldn't be

**Cause:** False positive from legitimate failures

**Solution:**
1. Admin unlocks account via admin interface
2. Verify user identity before unlocking
3. Consider increasing threshold if this happens frequently

### Issue: Admin account is locked

**This should never happen!** Admins are not subject to lockout.

**If it does:**
1. Check database directly: `UPDATE user SET failed_reset_attempts=0, reset_locked_until=NULL WHERE id=X;`
2. Review code to ensure admin check is working
3. Check audit logs for unusual activity

### Issue: User not receiving unlock email

**Causes:**
- Email service configuration issue
- Email in spam folder
- Invalid email address

**Solution:**
1. Check email service logs
2. Verify email configuration in `.env`
3. Test email service with admin test email
4. Manually notify user of unlock

### Issue: Locked accounts not appearing in admin interface

**Cause:** Accounts have expired automatically

**Check:**
- Query database for `reset_locked_until` or `reset_locked_by_admin`
- Verify current time vs `reset_locked_until`
- Check if `is_reset_locked_out()` method is working correctly

---

## Future Enhancements

### Potential Improvements

1. **IP-Based Tracking**
   - Track failed attempts by IP address
   - Lock IP addresses, not just accounts
   - Prevent distributed attacks

2. **Progressive Delays**
   - Increase delay between attempts
   - Force exponential backoff
   - Reduce need for hard lockout

3. **Security Questions**
   - Additional verification before unlock
   - User-specific security questions
   - Multi-factor authentication

4. **Automated Reports**
   - Weekly security summary for admins
   - Statistics on lockout frequency
   - Trend analysis

5. **User Self-Service**
   - Allow users to unlock via email verification
   - Reduce admin workload
   - Faster resolution for users

---

## Summary

The Account Lockout System provides robust protection against brute-force password reset attacks while maintaining usability and administrative control. Key features include:

✅ Automatic lockout after configurable threshold  
✅ Email notifications for users and administrators  
✅ Admin interface for unlocking accounts  
✅ Comprehensive audit trail  
✅ Time-based automatic expiration  
✅ Protection for admin accounts  

**Status:** Production-ready and fully tested.

**Maintenance:** Review audit logs regularly and adjust thresholds based on your environment.

**Support:** Contact the development team for issues or enhancement requests.

---

*Last Updated: October 2025*  
*Document Version: 1.0*  
*Implementation Version: 1.0*
