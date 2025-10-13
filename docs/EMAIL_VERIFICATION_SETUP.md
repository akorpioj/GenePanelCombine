# Email Verification System - Quick Setup Guide

## Installation Complete! 🎉

The email verification system has been successfully implemented. Follow these steps to activate it:

## What Was Added

### New Files Created:
1. **`app/email_service.py`** - Email service with verification functionality
2. **`app/templates/auth/resend_verification.html`** - Resend verification page
3. **`app/templates/auth/verify_status.html`** - Verification status page
4. **`docs/EMAIL_VERIFICATION_SYSTEM.md`** - Complete documentation
5. **`.env.email.example`** - Email configuration template
6. **`scripts/test_email_service.py`** - Testing script

### Files Modified:
1. **`requirements.txt`** - Added Flask-Mail
2. **`app/__init__.py`** - Initialize email service
3. **`app/auth/routes.py`** - Added verification routes and logic

## Quick Start (3 Steps)

### Step 1: Install Flask-Mail

```powershell
pip install Flask-Mail
```

### Step 2: Configure Email Settings

Add these to your `.env` file (see `.env.email.example` for full details):

```env
# For Development (emails won't actually send)
MAIL_SUPPRESS_SEND=True

# For Production with Gmail
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password  # See Gmail setup below
MAIL_DEFAULT_SENDER=noreply@panelmerge.com
```

### Step 3: Test the System

```powershell
python scripts/test_email_service.py
```

## Gmail Setup (for Production)

1. **Enable 2-Factor Authentication**
   - Go to Google Account → Security → 2-Step Verification
   - Follow setup wizard

2. **Generate App Password**
   - Visit: https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the 16-character password
   - Use this in `MAIL_PASSWORD` (not your regular Gmail password!)

3. **Update .env File**
   ```env
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx  # App password
   MAIL_SUPPRESS_SEND=False  # Actually send emails
   ```

## How It Works

### For New Users:
1. User registers → Account created with `is_verified=False`
2. Verification email sent automatically
3. User clicks link in email
4. Account verified → `is_verified=True`
5. User can now log in

### For Existing Users:
- All existing users will need to be marked as verified
- Run this one-time script:

```python
# In Flask shell: flask shell
from app.models import User, db
User.query.update({User.is_verified: True})
db.session.commit()
print(f"Verified {User.query.count()} users")
```

## New Routes Available

- **`/auth/verify/<token>`** - Verify email with token
- **`/auth/resend-verification`** - Resend verification email
- **`/auth/verify-status`** - Check verification status

## Development Mode

With `MAIL_SUPPRESS_SEND=True`:
- ✅ No SMTP credentials needed
- ✅ No actual emails sent
- ✅ Verification links logged to console
- ✅ Full flow can be tested locally

**Example console output:**
```
[DEV MODE] Email suppressed - To: user@example.com
[DEV MODE] Verification link would be:
http://localhost:5000/auth/verify/eyJhbGciOiJI...
```

Copy the link and open in browser to test verification!

## Testing Checklist

Run the test script to verify everything works:

```powershell
# Test all components
python scripts/test_email_service.py

# Test specific components
python scripts/test_email_service.py --test config   # Check configuration
python scripts/test_email_service.py --test token    # Test token generation
python scripts/test_email_service.py --test email    # Test email sending
python scripts/test_email_service.py --test flow     # Test full verification flow
```

## Production Deployment

### Before Going Live:

1. **Configure Production Email Service**
   - Consider using SendGrid, Amazon SES, or Mailgun
   - More reliable than Gmail for production
   - Better deliverability and monitoring

2. **Update Settings**
   ```env
   MAIL_SUPPRESS_SEND=False  # Actually send emails
   VERIFICATION_TOKEN_MAX_AGE=86400  # 24 hours
   ```

3. **Set Up DNS Records**
   - SPF record: Authorize sending servers
   - DKIM: Email authentication
   - DMARC: Email validation policy

4. **Monitor Email Delivery**
   - Check bounce rates
   - Monitor spam complaints
   - Review audit logs

### Recommended Production Services:

**SendGrid** (Free tier: 100 emails/day)
```env
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key
```

**Amazon SES** (Pay per email, very cheap)
```env
MAIL_SERVER=email-smtp.us-east-1.amazonaws.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-ses-access-key
MAIL_PASSWORD=your-ses-secret-key
```

## Security Features

✅ **Implemented:**
- Cryptographic token signing (itsdangerous)
- Time-limited tokens (24-hour expiration)
- Rate limiting on verification endpoints
- Audit logging of all verification events
- Secure password requirements maintained
- GDPR consent tracking preserved

✅ **Rate Limits:**
- Registration: 5 per minute
- Verification: 10 per hour
- Resend: 3 per hour

## Troubleshooting

### "Email not received"
- Check spam/junk folder
- Verify SMTP credentials
- Check `MAIL_SUPPRESS_SEND` setting
- Review application logs

### "Invalid or expired token"
- Token is older than 24 hours
- Request new verification email
- Check SECRET_KEY hasn't changed

### "Can't send email" (Production)
- Verify SMTP credentials correct
- Check firewall allows port 587
- For Gmail: Use App Password, not regular password
- Try different SMTP provider

### "Tests failing"
- Run: `python scripts/test_email_service.py`
- Check configuration with `--test config`
- Review error messages in output

## Documentation

**Full documentation**: `docs/EMAIL_VERIFICATION_SYSTEM.md`

Includes:
- Complete API reference
- Email template customization
- Security best practices
- Migration guide
- Testing strategies
- Troubleshooting guide

## Support

- **Documentation**: See `docs/EMAIL_VERIFICATION_SYSTEM.md`
- **Test Script**: `scripts/test_email_service.py`
- **Configuration Example**: `.env.email.example`
- **Audit Logs**: Check AuditLog table for verification events

## Next Steps

1. ✅ Install Flask-Mail: `pip install Flask-Mail`
2. ✅ Configure email settings in `.env`
3. ✅ Run test script: `python scripts/test_email_service.py`
4. ✅ Test registration flow
5. ✅ Test verification flow
6. ✅ Update existing users if needed
7. ✅ Deploy to production with real SMTP

---

**Questions?** Check `docs/EMAIL_VERIFICATION_SYSTEM.md` for detailed information.

**Ready to test?** Run `python scripts/test_email_service.py` now!
