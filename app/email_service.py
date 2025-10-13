"""
Email Service for PanelMerge
Provides email sending functionality including verification emails
"""

import os
import logging
from datetime import datetime, timedelta
from flask import render_template, current_app, url_for
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from typing import Optional

logger = logging.getLogger(__name__)

# Initialize Flask-Mail (will be configured in __init__.py)
mail = Mail()


class EmailService:
    """Service for sending emails"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize email service with Flask app"""
        self.app = app
        
        # Configure Flask-Mail settings from environment or config
        app.config.setdefault('MAIL_SERVER', os.getenv('MAIL_SERVER', 'smtp.gmail.com'))
        app.config.setdefault('MAIL_PORT', int(os.getenv('MAIL_PORT', 587)))
        app.config.setdefault('MAIL_USE_TLS', os.getenv('MAIL_USE_TLS', 'True').lower() == 'true')
        app.config.setdefault('MAIL_USE_SSL', os.getenv('MAIL_USE_SSL', 'False').lower() == 'true')
        app.config.setdefault('MAIL_USERNAME', os.getenv('MAIL_USERNAME'))
        app.config.setdefault('MAIL_PASSWORD', os.getenv('MAIL_PASSWORD'))
        app.config.setdefault('MAIL_DEFAULT_SENDER', os.getenv('MAIL_DEFAULT_SENDER', 'noreply@panelmerge.com'))
        app.config.setdefault('MAIL_MAX_EMAILS', int(os.getenv('MAIL_MAX_EMAILS', 50)))
        
        # Development mode - suppress actual email sending
        app.config.setdefault('MAIL_SUPPRESS_SEND', os.getenv('MAIL_SUPPRESS_SEND', 'True').lower() == 'true')
        
        # Verification token settings
        app.config.setdefault('VERIFICATION_TOKEN_MAX_AGE', int(os.getenv('VERIFICATION_TOKEN_MAX_AGE', 86400)))  # 24 hours
        app.config.setdefault('PASSWORD_RESET_TOKEN_MAX_AGE', int(os.getenv('PASSWORD_RESET_TOKEN_MAX_AGE', 3600)))  # 1 hour
        
        mail.init_app(app)
        logger.info("Email service initialized")
    
    def get_serializer(self, salt='email-verification'):
        """Get URLSafeTimedSerializer for token generation"""
        return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    def generate_verification_token(self, email: str) -> str:
        """
        Generate email verification token
        
        Args:
            email: User's email address
            
        Returns:
            Verification token string
        """
        serializer = self.get_serializer('email-verification')
        return serializer.dumps(email, salt='email-verification')
    
    def verify_token(self, token: str, salt='email-verification', max_age=None) -> Optional[str]:
        """
        Verify and decode a token
        
        Args:
            token: Token to verify
            salt: Salt used for token generation
            max_age: Maximum age in seconds (None uses default from config)
            
        Returns:
            Email address if valid, None otherwise
        """
        if max_age is None:
            max_age = current_app.config.get('VERIFICATION_TOKEN_MAX_AGE', 86400)
        
        serializer = self.get_serializer(salt)
        try:
            email = serializer.loads(token, salt=salt, max_age=max_age)
            return email
        except SignatureExpired:
            logger.warning(f"Token expired for verification attempt")
            return None
        except BadSignature:
            logger.warning(f"Invalid token signature for verification attempt")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    def send_email(self, subject: str, recipient: str, text_body: str, 
                   html_body: str = None, sender: str = None) -> bool:
        """
        Send an email
        
        Args:
            subject: Email subject
            recipient: Recipient email address
            text_body: Plain text body
            html_body: HTML body (optional)
            sender: Sender email (optional, uses default if not provided)
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            msg = Message(
                subject=subject,
                sender=sender or current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[recipient]
            )
            msg.body = text_body
            if html_body:
                msg.html = html_body
            
            # Check if email sending is suppressed (development mode)
            if current_app.config.get('MAIL_SUPPRESS_SEND', False):
                logger.info(f"[DEV MODE] Email suppressed - To: {recipient}, Subject: {subject}")
                logger.info(f"[DEV MODE] Verification link would be: {text_body}")
                return True
            
            mail.send(msg)
            logger.info(f"Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            return False
    
    def send_verification_email(self, user_email: str, user_name: str) -> bool:
        """
        Send email verification email to user
        
        Args:
            user_email: User's email address
            user_name: User's name
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Generate verification token
            token = self.generate_verification_token(user_email)
            
            # Build verification URL (using _external=True for full URL)
            verify_url = url_for('auth.verify_email', token=token, _external=True)
            
            # Email subject
            subject = "Verify Your Email - PanelMerge"
            
            # Plain text body
            text_body = f"""
Hello {user_name},

Thank you for registering with PanelMerge!

Please verify your email address by clicking the link below:

{verify_url}

This link will expire in 24 hours.

If you did not create an account, please ignore this email.

Best regards,
The PanelMerge Team
            """.strip()
            
            # HTML body (optional, for better formatting)
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #3b82f6; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9fafb; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; 
                   text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #6b7280; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to PanelMerge!</h1>
        </div>
        <div class="content">
            <p>Hello {user_name},</p>
            <p>Thank you for registering with PanelMerge!</p>
            <p>Please verify your email address by clicking the button below:</p>
            <p style="text-align: center;">
                <a href="{verify_url}" class="button">Verify Email Address</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background-color: #e5e7eb; padding: 10px; border-radius: 3px;">
                {verify_url}
            </p>
            <p><strong>This link will expire in 24 hours.</strong></p>
            <p>If you did not create an account, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>This is an automated email from PanelMerge. Please do not reply.</p>
            <p>&copy; 2025 PanelMerge. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
            """.strip()
            
            return self.send_email(subject, user_email, text_body, html_body)
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {user_email}: {e}")
            return False
    
    def send_verification_success_email(self, user_email: str, user_name: str) -> bool:
        """
        Send confirmation email after successful verification
        
        Args:
            user_email: User's email address
            user_name: User's name
            
        Returns:
            True if sent successfully, False otherwise
        """
        subject = "Email Verified - PanelMerge"
        
        text_body = f"""
Hello {user_name},

Your email address has been successfully verified!

You can now access all features of PanelMerge.

Log in at: {url_for('auth.login', _external=True)}

Best regards,
The PanelMerge Team
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #10b981; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9fafb; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; 
                   text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #6b7280; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✓ Email Verified!</h1>
        </div>
        <div class="content">
            <p>Hello {user_name},</p>
            <p>Your email address has been successfully verified!</p>
            <p>You can now access all features of PanelMerge.</p>
            <p style="text-align: center;">
                <a href="{url_for('auth.login', _external=True)}" class="button">Log In Now</a>
            </p>
        </div>
        <div class="footer">
            <p>&copy; 2025 PanelMerge. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return self.send_email(subject, user_email, text_body, html_body)
    
    def send_password_reset_email(self, user_email: str, user_name: str) -> bool:
        """
        Send password reset email
        
        Args:
            user_email: User's email address
            user_name: User's name
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Generate reset token
            serializer = self.get_serializer('password-reset')
            token = serializer.dumps(user_email, salt='password-reset')
            
            # Build reset URL
            reset_url = url_for('auth.reset_password', token=token, _external=True)

            subject = "Password Reset Request - PanelMerge"

            text_body = f"""
Hello {user_name},

You requested a password reset for your PanelMerge account.

Click the link below to reset your password:

{reset_url}

This link will expire in 1 hour.

If you did not request this reset, please ignore this email and your password will remain unchanged.

Best regards,
The PanelMerge Team
            """.strip()
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f59e0b; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9fafb; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; 
                   text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #6b7280; }}
        .warning {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 10px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hello {user_name},</p>
            <p>You requested a password reset for your PanelMerge account.</p>
            <p style="text-align: center;">
                <a href="{reset_url}" class="button">Reset Password</a>
            </p>
            <div class="warning">
                <strong>⚠️ This link will expire in 1 hour.</strong>
            </div>
            <p>If you did not request this reset, please ignore this email and your password will remain unchanged.</p>
        </div>
        <div class="footer">
            <p>&copy; 2025 PanelMerge. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
            """.strip()
            
            return self.send_email(subject, user_email, text_body, html_body)
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user_email}: {e}")
            return False
    
    def send_admin_password_reset_email(self, user_email: str, user_name: str, temp_password: str, admin_name: str) -> bool:
        """
        Send admin password reset notification email with temporary password
        
        Args:
            user_email: User's email address
            user_name: User's name
            temp_password: Temporary password
            admin_name: Name of admin who reset the password
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            subject = "Your Password Has Been Reset - PanelMerge"

            text_body = f"""
Hello {user_name},

An administrator ({admin_name}) has reset your PanelMerge account password.

Your temporary password is: {temp_password}

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
            """.strip()
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #dc2626; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9fafb; }}
        .password-box {{ background-color: #fff; border: 2px solid #3b82f6; padding: 15px; 
                         text-align: center; font-size: 18px; font-family: monospace; 
                         letter-spacing: 2px; margin: 20px 0; border-radius: 5px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; 
                   text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #6b7280; }}
        .warning {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 10px; margin: 10px 0; }}
        .danger {{ background-color: #fee2e2; border-left: 4px solid #dc2626; padding: 10px; margin: 10px 0; }}
        .steps {{ background-color: #fff; padding: 15px; margin: 15px 0; border-radius: 5px; }}
        .steps ol {{ margin: 10px 0; padding-left: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Password Reset by Administrator</h1>
        </div>
        <div class="content">
            <p>Hello {user_name},</p>
            <p>An administrator (<strong>{admin_name}</strong>) has reset your PanelMerge account password.</p>
            
            <div class="warning">
                <strong>⚠️ IMPORTANT:</strong> You will be required to change this password when you log in.
            </div>
            
            <p><strong>Your temporary password:</strong></p>
            <div class="password-box">
                {temp_password}
            </div>
            
            <div class="steps">
                <strong>How to log in:</strong>
                <ol>
                    <li>Go to the PanelMerge login page</li>
                    <li>Use your username and the temporary password above</li>
                    <li>You will be prompted to create a new password</li>
                    <li>Choose a strong password you haven't used before</li>
                </ol>
            </div>
            
            <div class="danger">
                <strong>🛡️ Security Notice:</strong>
                <ul style="margin: 5px 0; padding-left: 20px;">
                    <li>All your active sessions have been logged out</li>
                    <li>This temporary password should be changed immediately</li>
                    <li>If you did not request this reset, contact an administrator immediately</li>
                </ul>
            </div>
        </div>
        <div class="footer">
            <p>&copy; 2025 PanelMerge. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
            """.strip()
            
            return self.send_email(subject, user_email, text_body, html_body)
            
        except Exception as e:
            logger.error(f"Failed to send admin password reset email to {user_email}: {e}")
            return False


# Global instance
email_service = EmailService()
