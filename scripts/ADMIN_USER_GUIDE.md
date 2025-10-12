# Admin User Management Script

This directory contains scripts for creating and managing admin users in the PanelMerge application.

## Features

✅ **Create new admin users** with full profile information  
✅ **Change passwords** for existing admin users  
✅ **Reset failed login attempts** and unlock accounts  
✅ **Interactive or command-line modes** for flexible usage  
✅ **Secure password handling** with getpass (no echo)

## Files

- `create_admin_user.ps1` - PowerShell wrapper script (Windows)
- `db/create_admin_user.py` - Main Python script for admin user management

---

## Usage

### 🆕 Create New Admin User

#### PowerShell (Interactive Mode - Recommended)
```powershell
.\create_admin_user.ps1
```
This will prompt you for all required information.

#### PowerShell (With Parameters)
```powershell
.\create_admin_user.ps1 -Username "admin" -Email "admin@example.com"
```

#### PowerShell (Non-Interactive Mode)
```powershell
.\create_admin_user.ps1 -Username "admin" -Email "admin@example.com" -Password "SecurePassword123!" -NonInteractive
```

#### PowerShell (All Parameters)
```powershell
.\create_admin_user.ps1 -Username "admin" -Email "admin@example.com" -Password "SecurePassword123!" -FirstName "John" -LastName "Doe" -Organization "My Company" -NonInteractive
```

#### Python Direct (Interactive)
```bash
python scripts/db/create_admin_user.py
```

#### Python Direct (Non-Interactive)
```bash
python scripts/db/create_admin_user.py -u admin -e admin@example.com -p SecurePassword123! --non-interactive
```

---

### 🔑 Change Admin User Password

#### PowerShell (Interactive Mode - Recommended)
```powershell
.\create_admin_user.ps1 -ChangePassword
```
This will:
1. Prompt for the username
2. Display user information for confirmation
3. Prompt for new password (twice for confirmation)
4. Reset failed login attempts to 0
5. Unlock the account if it was locked

#### PowerShell (With Parameters)
```powershell
.\create_admin_user.ps1 -ChangePassword -Username "admin"
```

#### PowerShell (Non-Interactive Mode)
```powershell
.\create_admin_user.ps1 -ChangePassword -Username "admin" -Password "NewSecurePassword123!" -NonInteractive
```

#### Python Direct (Interactive)
```bash
python scripts/db/create_admin_user.py --change-password
```

#### Python Direct (With Parameters)
```bash
python scripts/db/create_admin_user.py --change-password -u admin
```

#### Python Direct (Non-Interactive)
```bash
python scripts/db/create_admin_user.py --change-password -u admin -p NewPassword123! --non-interactive
```

---

## Command Line Arguments

### General Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `--change-password` | | Change password for existing admin user (instead of creating new) |
| `--non-interactive` | | Run without prompts (requires all necessary args) |

### User Information Arguments

| Argument | Short | Description | Used In |
|----------|-------|-------------|---------|
| `--username` | `-u` | Username for the admin user | Create, Change Password |
| `--email` | `-e` | Email address for the admin user | Create only |
| `--password` | `-p` | Password (not recommended for security) | Create, Change Password |
| `--first-name` | `-f` | First name (optional) | Create only |
| `--last-name` | `-l` | Last name (optional) | Create only |
| `--organization` | `-o` | Organization name (optional) | Create only |

---

## Security Notes

### Password Security
- **⚠️ Avoid using `-p/--password` parameter** in production as it may be visible in command history
- In interactive mode, passwords are entered securely using `getpass` (no echo)
- Passwords must be at least 8 characters long
- Consider using password managers to generate strong passwords

### User Creation
- The script checks for existing users with the same username or email
- Admin users are created with:
  - Role: ADMIN
  - Active: True
  - Verified: True
  - Failed login attempts: 0

### Password Change Features
- ✅ Displays user information before changing password for confirmation
- ✅ Requires confirmation in interactive mode
- ✅ Automatically resets failed login attempts to 0
- ✅ Automatically unlocks the account if it was locked
- ✅ Validates password strength (minimum 8 characters)

---

## Prerequisites

1. Python 3.x installed and accessible via command line
2. Virtual environment activated (if using one)
3. All required Python packages installed (`pip install -r requirements.txt`)
4. Database configuration properly set up

---

## Examples

### Example 1: Create admin user interactively (safest)
```powershell
.\create_admin_user.ps1
```
**Output:**
```
Creating admin user for PanelMerge
========================================
Enter username: admin
Enter email address: admin@example.com
Enter password: ********
Confirm password: ********
Enter first name (optional): John
Enter last name (optional): Doe
Enter organization (optional): My Company

Admin user created successfully!
Username: admin
Email: admin@example.com
Role: ADMIN
Active: True
Verified: True
Full name: John Doe
Organization: My Company
```

### Example 2: Change password interactively
```powershell
.\create_admin_user.ps1 -ChangePassword
```
**Output:**
```
Change Admin User Password
========================================
Enter username of admin user: admin

User found:
  Username: admin
  Email: admin@example.com
  Role: ADMIN
  Full name: John Doe
  Organization: My Company

Change password for this user? (yes/no): yes

Enter new password: ********
Confirm new password: ********

✓ Password changed successfully for user 'admin'!
  - Failed login attempts reset to 0
  - Account unlocked (if it was locked)
```

### Example 3: Create admin in automation script
```powershell
.\create_admin_user.ps1 -Username "auto_admin" -Email "auto@company.com" -Password "AutoGeneratedPassword123!" -NonInteractive
```

### Example 4: Change password in automation script
```powershell
.\create_admin_user.ps1 -ChangePassword -Username "admin" -Password "NewPassword123!" -NonInteractive
```

### Example 5: Unlock locked account by changing password
```bash
python scripts/db/create_admin_user.py --change-password -u lockeduser
```
This will prompt for new password and automatically:
- Reset failed login attempts to 0
- Remove account lock
- Update the password

---

## Use Cases

### 1. Initial Setup
When first deploying the application, create the initial admin user:
```powershell
.\create_admin_user.ps1
```

### 2. Forgotten Password
If an admin forgets their password:
```powershell
.\create_admin_user.ps1 -ChangePassword -Username "admin"
```

### 3. Account Locked Due to Failed Logins
If an account is locked due to too many failed login attempts:
```powershell
.\create_admin_user.ps1 -ChangePassword -Username "locked_admin"
```
This will unlock the account and reset the failed login counter.

### 4. Security Breach Response
If credentials may have been compromised, immediately change the password:
```powershell
.\create_admin_user.ps1 -ChangePassword -Username "compromised_admin"
```

### 5. Automated Deployment
In CI/CD pipelines or automated deployments:
```bash
python scripts/db/create_admin_user.py -u admin -e admin@example.com -p "${ADMIN_PASSWORD}" --non-interactive
```

### 6. Password Rotation Policy
For regular password changes as part of security policy:
```bash
python scripts/db/create_admin_user.py --change-password -u admin -p "${NEW_PASSWORD}" --non-interactive
```

---

## Troubleshooting

### Python not found
- Ensure Python is installed and in your PATH
- Try using `python3` instead of `python`
- On Windows, try using `py` command

### Database connection errors
- Check database configuration in `app/config_settings.py`
- Ensure database server is running
- Verify connection credentials
- Check environment variables (`.env` file)

### User not found (when changing password)
- Verify the username is correct (case-sensitive)
- Check that the user exists in the database
- Use the admin panel to view existing users

### Permission errors
- Run PowerShell as Administrator if needed
- Check file permissions in the project directory
- Ensure you have write access to the database

### Import errors
- Ensure you're running from the project root directory
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check that virtual environment is activated if using one
- Verify `PYTHONPATH` includes the project root

### Password validation errors
- Password must be at least 8 characters
- Consider including uppercase, lowercase, numbers, and special characters
- Avoid common passwords or dictionary words

---

## Security Best Practices

### 1. Strong Passwords
- Use complex passwords with:
  - Minimum 8 characters (preferably 12+)
  - Mixed case letters (A-Z, a-z)
  - Numbers (0-9)
  - Special characters (!@#$%^&*)
- Use password generators for maximum security

### 2. Secure Storage
- Store admin credentials in a password manager
- Never commit passwords to version control
- Use environment variables for automated deployments
- Rotate passwords regularly (e.g., every 90 days)

### 3. Access Control
- Limit the number of admin accounts
- Create regular user accounts for daily tasks
- Use admin accounts only for administrative tasks
- Monitor admin user activity through audit logs

### 4. Regular Maintenance
- Review admin user list regularly
- Remove accounts that are no longer needed
- Update passwords after staff changes
- Check audit logs for suspicious activity

### 5. Monitoring
- Enable audit logging for all admin actions
- Set up alerts for failed login attempts
- Review security logs regularly
- Implement IP-based access restrictions if needed

---

## Integration with Application Features

This script works seamlessly with PanelMerge's security features:

- ✅ **Audit Logging**: All operations are logged in the audit trail
- ✅ **Encryption**: Sensitive user data is encrypted at rest
- ✅ **Session Management**: Supports enhanced session security
- ✅ **Failed Login Protection**: Resets lockout counters
- ✅ **GDPR Compliance**: Follows data protection principles

---

## Help Command

For detailed help and examples:

```bash
# Python script
python scripts/db/create_admin_user.py --help

# PowerShell script
Get-Help .\create_admin_user.ps1 -Detailed
```

---

## Version History

- **v1.1** (October 2025): Added password change functionality
- **v1.0** (Initial): Basic admin user creation

---

## Support

For issues or questions:
- Check the main application documentation
- Review the troubleshooting section above
- Contact: anita.korpioja@gmail.com

---

## Related Documentation

- `docs/AUTHENTICATION_SYSTEM.md` - Authentication and user management details
- `docs/AUDIT_TRAIL_SYSTEM.md` - Audit logging information
- `docs/SECURITY_GUIDE.md` - Overall security architecture
- `docs/GDPR_COMPLIANCE_IMPLEMENTATION.md` - Data protection policies
