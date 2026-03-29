import os
import datetime
from typing import List
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from enum import Enum
# Import the Cloud SQL Python Connector library
from google.cloud.sql.connector import Connector, IPTypes

# Import encryption services for sensitive field protection
try:
    from .encryption_service import EncryptedField, EncryptedJSONField
except ImportError:
    # Fallback for when encryption service is not available
    class EncryptedField:
        def __init__(self, field_name):
            self.field_name = field_name
        def __get__(self, obj, objtype=None):
            return getattr(obj, self.field_name) if obj else self
        def __set__(self, obj, value):
            setattr(obj, self.field_name, value)
    
    class EncryptedJSONField:
        def __init__(self, field_name):
            self.field_name = field_name
        def __get__(self, obj, objtype=None):
            return getattr(obj, self.field_name) if obj else self
        def __set__(self, obj, value):
            setattr(obj, self.field_name, value)

db = SQLAlchemy()  # Add this line to define db

class UserRole(Enum):
    """User roles for role-based access control"""
    VIEWER = "VIEWER"      # Can only view and use basic features
    USER = "USER"          # Standard user with upload capabilities
    EDITOR = "EDITOR"      # Can manage panels and moderate content
    ADMIN = "ADMIN"        # Full system access

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Encrypted sensitive fields
    _first_name = db.Column('first_name_encrypted', db.Text)
    _last_name = db.Column('last_name_encrypted', db.Text)  
    _organization = db.Column('organization_encrypted', db.Text)
    
    # Use encryption descriptors for sensitive data
    first_name = EncryptedField('_first_name')
    last_name = EncryptedField('_last_name')
    organization = EncryptedField('_organization')
    
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)
    last_login = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    
    # Email change verification fields
    pending_email = db.Column(db.String(120))  # New email awaiting verification
    email_change_token_hash = db.Column(db.String(255))  # Hashed token for security
    email_change_requested_at = db.Column(db.DateTime)  # When change was requested
    
    # Additional security fields
    last_ip_address = db.Column(db.String(45))
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    force_password_change = db.Column(db.Boolean, default=False, nullable=False)  # Admin can force password change
    
    # Temporary password expiration fields (for admin-reset passwords)
    temp_password_token = db.Column(db.String(255))  # Token for temporary password validation
    temp_password_expires_at = db.Column(db.DateTime)  # Expiration time for temporary password
    temp_password_created_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Admin who created temp password
    
    # Account lockout fields for password reset abuse
    failed_reset_attempts = db.Column(db.Integer, default=0, nullable=False)  # Track failed password reset attempts
    reset_locked_until = db.Column(db.DateTime)  # Lockout expiration for password resets
    reset_locked_by_admin = db.Column(db.Boolean, default=False, nullable=False)  # Requires admin intervention
    
    # User preferences
    timezone_preference = db.Column(db.String(50), default='UTC')  # IANA timezone name
    time_format_preference = db.Column(db.String(10), default='24h')  # '12h' or '24h'
    
    # Relationship to track user downloads
    downloads = db.relationship('PanelDownload', backref='user', lazy=True)

    def set_password(self, password, add_to_history=True):
        """
        Set user password and optionally add to password history
        
        Args:
            password: Plain text password
            add_to_history: Whether to add this password to history (default: True)
        """
        self.password_hash = generate_password_hash(password)
        
        # Add to password history if requested and user has an ID
        if add_to_history and self.id:
            from .config_settings import DevelopmentConfig
            max_history = int(os.getenv('PASSWORD_HISTORY_LENGTH', 5))
            PasswordHistory.add_password(self.id, self.password_hash, max_history)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def check_password_reuse(self, password):
        """
        Check if password has been used recently
        
        Args:
            password: Plain text password to check
            
        Returns:
            bool: True if password was used recently (should reject), False otherwise
        """
        if not self.id:
            return False
        
        max_history = int(os.getenv('PASSWORD_HISTORY_LENGTH', 5))
        return PasswordHistory.check_password_reuse(self.id, password, max_history)
    
    def get_full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def has_role(self, role):
        """Check if user has specific role or higher"""
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.USER: 2,
            UserRole.EDITOR: 3,
            UserRole.ADMIN: 4
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(role, 0)
    
    def can_upload(self):
        """Check if user can upload files"""
        return self.has_role(UserRole.USER)
    
    def can_moderate(self):
        """Check if user can moderate content"""
        return self.has_role(UserRole.EDITOR)
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    # Account Lockout Methods for Password Reset
    def increment_failed_resets(self):
        """Increment failed password reset attempts counter"""
        self.failed_reset_attempts = (self.failed_reset_attempts or 0) + 1
    
    def reset_failed_resets(self):
        """Reset failed password reset attempts counter"""
        self.failed_reset_attempts = 0
        self.reset_locked_until = None
        self.reset_locked_by_admin = False
    
    def is_reset_locked_out(self):
        """
        Check if account is locked out from password resets
        
        Returns:
            bool: True if locked out, False otherwise
        """
        # Check if locked by admin (requires admin intervention)
        if self.reset_locked_by_admin:
            return True
        
        # Check if temporary lockout is still active
        if self.reset_locked_until:
            if datetime.datetime.now() < self.reset_locked_until:
                return True
            else:
                # Lockout expired, clear it
                self.reset_locked_until = None
                self.failed_reset_attempts = 0
                return False
        
        return False
    
    def lock_reset_account(self, duration_hours=24, by_admin=False):
        """
        Lock account from password resets
        
        Args:
            duration_hours: Hours to lock account (default: 24)
            by_admin: Whether lock requires admin intervention (default: False)
        """
        if by_admin:
            self.reset_locked_by_admin = True
            self.reset_locked_until = None  # Permanent until admin unlocks
        else:
            self.reset_locked_until = datetime.datetime.now() + datetime.timedelta(hours=duration_hours)
            self.reset_locked_by_admin = False
    
    def unlock_reset_account(self):
        """Unlock account (admin action)"""
        self.reset_locked_until = None
        self.reset_locked_by_admin = False
        self.failed_reset_attempts = 0
    
    # Email Change Methods
    def request_email_change(self, new_email: str, token_hash: str):
        """
        Request email change - stores pending email and token hash
        
        Args:
            new_email: The new email address to change to
            token_hash: Hashed verification token
        """
        self.pending_email = new_email
        self.email_change_token_hash = token_hash
        self.email_change_requested_at = datetime.datetime.now()
    
    def cancel_email_change(self):
        """Cancel pending email change"""
        self.pending_email = None
        self.email_change_token_hash = None
        self.email_change_requested_at = None
    
    def has_pending_email_change(self) -> bool:
        """Check if there's a pending email change"""
        return self.pending_email is not None
    
    def complete_email_change(self):
        """Complete the email change - moves pending email to email"""
        if self.pending_email:
            old_email = self.email
            self.email = self.pending_email
            self.pending_email = None
            self.email_change_token_hash = None
            self.email_change_requested_at = None
            return old_email
        return None
    
    # Temporary Password Methods
    def set_temp_password(self, password: str, token: str, admin_id: int, expiration_hours: int = 24):
        """
        Set temporary password with expiration
        
        Args:
            password: The temporary password (plain text)
            token: Unique token for this temporary password
            admin_id: ID of admin who created the temp password
            expiration_hours: Hours until password expires (default: 24)
        """
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
        self.temp_password_token = token
        self.temp_password_expires_at = datetime.datetime.now() + datetime.timedelta(hours=expiration_hours)
        self.temp_password_created_by = admin_id
        self.force_password_change = True
    
    def is_temp_password_expired(self) -> bool:
        """Check if temporary password has expired"""
        if not self.temp_password_expires_at:
            return False  # No temp password set
        return datetime.datetime.now() > self.temp_password_expires_at
    
    def has_temp_password(self) -> bool:
        """Check if user has a temporary password set"""
        return self.temp_password_token is not None and self.temp_password_expires_at is not None
    
    def clear_temp_password(self):
        """Clear temporary password fields after successful password change"""
        self.temp_password_token = None
        self.temp_password_expires_at = None
        self.temp_password_created_by = None
    
    def get_temp_password_time_remaining(self) -> str:
        """Get human-readable time remaining for temp password"""
        if not self.temp_password_expires_at:
            return "No expiration"
        
        remaining = self.temp_password_expires_at - datetime.datetime.now()
        if remaining.total_seconds() <= 0:
            return "Expired"
        
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours} hour{'s' if hours != 1 else ''} {minutes} min"
        else:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
    
    def get_timezone(self):
        """Get user's preferred timezone"""
        import pytz
        try:
            return pytz.timezone(self.timezone_preference or 'UTC')
        except pytz.UnknownTimeZoneError:
            return pytz.UTC
    
    def set_timezone(self, timezone_name):
        """Set user's timezone preference"""
        import pytz
        try:
            # Validate timezone
            pytz.timezone(timezone_name)
            self.timezone_preference = timezone_name
            return True
        except pytz.UnknownTimeZoneError:
            return False
    
    def get_active_admin_messages(self):
        """Get all active admin messages for display"""
        # Since AdminMessage is defined in the same module, we can reference it directly
        return AdminMessage.get_active_messages()
    
    def __repr__(self):
        """String representation of User"""
        return f'<User {self.username}>'
    
    @staticmethod
    def guest_can_upload():
        """Check if guest users can upload files - currently allowed for all"""
        return True
    
    @staticmethod
    def guest_has_user_access():
        """Check if guest users have USER-level access - currently allowed for all"""
        return True
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.get_full_name(),
            'organization': self.organization,
            'role': self.role.value if self.role else 'user',
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class PasswordHistory(db.Model):
    """
    Model to store password history for users
    Prevents password reuse by keeping track of previous passwords
    """
    __tablename__ = 'password_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('password_history', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<PasswordHistory user_id={self.user_id} created_at={self.created_at}>'
    
    @staticmethod
    def add_password(user_id, password_hash, max_history=5):
        """
        Add a password to the history and maintain the configured history length
        
        Args:
            user_id: ID of the user
            password_hash: Hashed password to store
            max_history: Maximum number of passwords to keep (default: 5)
        """
        # Add new password to history
        history_entry = PasswordHistory(
            user_id=user_id,
            password_hash=password_hash
        )
        db.session.add(history_entry)
        
        # Clean up old passwords beyond the limit
        all_passwords = PasswordHistory.query.filter_by(user_id=user_id).order_by(
            PasswordHistory.created_at.desc()
        ).all()
        
        if len(all_passwords) > max_history:
            # Delete oldest passwords
            for old_password in all_passwords[max_history:]:
                db.session.delete(old_password)
        
        db.session.commit()
    
    @staticmethod
    def check_password_reuse(user_id, password, max_history=5):
        """
        Check if a password has been used recently
        
        Args:
            user_id: ID of the user
            password: Plain text password to check
            max_history: Number of recent passwords to check against
            
        Returns:
            bool: True if password was used recently (should be rejected), False otherwise
        """
        recent_passwords = PasswordHistory.query.filter_by(user_id=user_id).order_by(
            PasswordHistory.created_at.desc()
        ).limit(max_history).all()
        
        for history_entry in recent_passwords:
            if check_password_hash(history_entry.password_hash, password):
                return True
        
        return False


class PasswordResetToken(db.Model):
    """
    Model to store password reset tokens for single-use validation
    Prevents token reuse by tracking which tokens have been used
    """
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(500), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    used_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('password_reset_tokens', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<PasswordResetToken user_id={self.user_id} used={self.used} created_at={self.created_at}>'
    
    def is_valid(self):
        """
        Check if token is valid (not used and not expired)
        
        Returns:
            bool: True if token is valid, False otherwise
        """
        if self.used:
            return False
        if datetime.datetime.now() > self.expires_at:
            return False
        return True
    
    def mark_as_used(self):
        """Mark token as used and record timestamp"""
        self.used = True
        self.used_at = datetime.datetime.now()
        db.session.commit()
    
    @staticmethod
    def create_token(user_id, token_string, expiration_seconds=3600):
        """
        Create a new password reset token
        
        Args:
            user_id: ID of the user
            token_string: The token string to store
            expiration_seconds: How long the token is valid (default: 1 hour)
            
        Returns:
            PasswordResetToken: The created token object
        """
        expires_at = datetime.datetime.now() + datetime.timedelta(seconds=expiration_seconds)
        
        token = PasswordResetToken(
            token=token_string,
            user_id=user_id,
            expires_at=expires_at
        )
        db.session.add(token)
        db.session.commit()
        
        return token
    
    @staticmethod
    def get_valid_token(token_string):
        """
        Get a token if it exists and is valid
        
        Args:
            token_string: The token string to look up
            
        Returns:
            PasswordResetToken or None: The token if valid, None otherwise
        """
        token = PasswordResetToken.query.filter_by(token=token_string).first()
        
        if token and token.is_valid():
            return token
        
        return None
    
    @staticmethod
    def cleanup_expired_tokens():
        """
        Remove expired tokens from the database
        Should be run periodically as maintenance
        
        Returns:
            int: Number of tokens deleted
        """
        expired_tokens = PasswordResetToken.query.filter(
            PasswordResetToken.expires_at < datetime.datetime.now()
        ).all()
        
        count = len(expired_tokens)
        for token in expired_tokens:
            db.session.delete(token)
        
        db.session.commit()
        return count
    
    @staticmethod
    def cleanup_old_tokens(days=30):
        """
        Remove old tokens (used or expired) older than specified days
        
        Args:
            days: Number of days to keep tokens (default: 30)
            
        Returns:
            int: Number of tokens deleted
        """
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        old_tokens = PasswordResetToken.query.filter(
            PasswordResetToken.created_at < cutoff_date
        ).all()
        
        count = len(old_tokens)
        for token in old_tokens:
            db.session.delete(token)
        
        db.session.commit()
        return count


class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 can be up to 45 chars
    visit_date = db.Column(db.DateTime, nullable=False)
    path = db.Column(db.String(255), nullable=False)
    user_agent = db.Column(db.String(255))


class SuspiciousActivity(db.Model):
    """
    Model to track suspicious password reset activity
    Used for detecting attacks and compromised accounts
    """
    __tablename__ = 'suspicious_activity'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    activity_type = db.Column(db.String(50), nullable=False)  # 'reset_request', 'reset_attempt', 'reset_success'
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False, index=True)
    alert_triggered = db.Column(db.Boolean, default=False, nullable=False)
    alert_reason = db.Column(db.Text)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('suspicious_activities', lazy='dynamic'))
    
    def __repr__(self):
        return f'<SuspiciousActivity {self.activity_type} for {self.email} from {self.ip_address}>'
    
    @staticmethod
    def log_activity(email, activity_type, ip_address, user_agent=None, user_id=None, 
                    country=None, city=None):
        """
        Log a password reset activity
        
        Args:
            email: User's email address
            activity_type: Type of activity ('reset_request', 'reset_attempt', 'reset_success')
            ip_address: IP address of the request
            user_agent: User agent string
            user_id: User ID (if known)
            country: Country from IP geolocation
            city: City from IP geolocation
            
        Returns:
            SuspiciousActivity: The created activity record
        """
        activity = SuspiciousActivity(
            email=email,
            activity_type=activity_type,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
            country=country,
            city=city
        )
        db.session.add(activity)
        db.session.commit()
        
        return activity
    
    @staticmethod
    def detect_multiple_attempts(email, hours=1, threshold=5):
        """
        Detect multiple reset attempts from different IPs within time window
        
        Args:
            email: Email to check
            hours: Time window in hours
            threshold: Number of attempts to trigger alert
            
        Returns:
            tuple: (is_suspicious, reason, count)
        """
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
        
        attempts = SuspiciousActivity.query.filter(
            SuspiciousActivity.email == email,
            SuspiciousActivity.activity_type.in_(['reset_request', 'reset_attempt']),
            SuspiciousActivity.timestamp >= cutoff_time
        ).all()
        
        count = len(attempts)
        
        if count >= threshold:
            unique_ips = len(set([a.ip_address for a in attempts]))
            reason = f"{count} password reset attempts in {hours} hour(s) from {unique_ips} different IP address(es)"
            return True, reason, count
        
        return False, None, count
    
    @staticmethod
    def detect_geographic_anomaly(email, current_ip, current_country=None):
        """
        Detect geographic anomalies (requests from unusual locations)
        
        Args:
            email: Email to check
            current_ip: Current IP address
            current_country: Current country (if known)
            
        Returns:
            tuple: (is_suspicious, reason)
        """
        # Get recent successful activities (last 30 days)
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=30)
        
        recent_activities = SuspiciousActivity.query.filter(
            SuspiciousActivity.email == email,
            SuspiciousActivity.activity_type == 'reset_success',
            SuspiciousActivity.timestamp >= cutoff_time,
            SuspiciousActivity.country.isnot(None)
        ).order_by(SuspiciousActivity.timestamp.desc()).limit(10).all()
        
        if not recent_activities:
            # No history, can't detect anomaly
            return False, None
        
        # Get countries from recent activities
        recent_countries = [a.country for a in recent_activities if a.country]
        
        if not recent_countries:
            return False, None
        
        # If current country is known and different from all recent countries
        if current_country and current_country not in recent_countries:
            most_common = max(set(recent_countries), key=recent_countries.count)
            reason = f"Password reset from unusual location: {current_country} (usually from {most_common})"
            return True, reason
        
        # Check if current IP was never seen before
        recent_ips = [a.ip_address for a in recent_activities]
        if current_ip not in recent_ips:
            # New IP, but we only alert if also new country
            if current_country and current_country not in recent_countries:
                reason = f"Password reset from new IP and new country: {current_country}"
                return True, reason
        
        return False, None
    
    @staticmethod
    def detect_time_pattern_anomaly(email, current_hour):
        """
        Detect unusual timing patterns (e.g., activity at odd hours)
        
        Args:
            email: Email to check
            current_hour: Current hour (0-23)
            
        Returns:
            tuple: (is_suspicious, reason)
        """
        # Get recent successful activities (last 90 days)
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=90)
        
        recent_activities = SuspiciousActivity.query.filter(
            SuspiciousActivity.email == email,
            SuspiciousActivity.activity_type == 'reset_success',
            SuspiciousActivity.timestamp >= cutoff_time
        ).all()
        
        if len(recent_activities) < 5:
            # Not enough data to establish pattern
            return False, None
        
        # Get hours of previous activities
        activity_hours = [a.timestamp.hour for a in recent_activities]
        
        # Calculate if current hour is unusual (more than 4 hours from any previous activity)
        min_difference = min([abs(current_hour - h) for h in activity_hours])
        
        # Consider both forward and backward wrapping (24-hour clock)
        wrapped_differences = [min(abs(current_hour - h), 24 - abs(current_hour - h)) for h in activity_hours]
        min_wrapped_difference = min(wrapped_differences)
        
        if min_wrapped_difference >= 6:  # 6+ hours from normal pattern
            typical_hours = f"{min(activity_hours)}-{max(activity_hours)}"
            reason = f"Password reset at unusual hour: {current_hour}:00 (typically active {typical_hours}:00)"
            return True, reason
        
        return False, None
    
    @staticmethod
    def check_all_patterns(email, ip_address, user_id=None, country=None):
        """
        Check all suspicious patterns and return results
        
        Args:
            email: Email to check
            ip_address: Current IP address
            user_id: User ID (if known)
            country: Current country (if known)
            
        Returns:
            dict: Detection results with alerts and reasons
        """
        current_hour = datetime.datetime.now().hour
        
        # Check rule-based patterns
        multiple_attempts, attempts_reason, attempts_count = SuspiciousActivity.detect_multiple_attempts(email)
        geo_anomaly, geo_reason = SuspiciousActivity.detect_geographic_anomaly(email, ip_address, country)
        time_anomaly, time_reason = SuspiciousActivity.detect_time_pattern_anomaly(email, current_hour)
        
        # Check ML-based anomaly detection (if enabled and model available)
        ml_anomaly = False
        ml_score = 0.0
        ml_reason = ""
        
        try:
            from flask import current_app
            if current_app.config.get('ML_ANOMALY_DETECTION_ENABLED', False):
                from app.ml_anomaly_detector import ml_detector
                
                # Extract features and predict
                features = ml_detector.extract_features(
                    email, ip_address, user_id, country, db.session
                )
                ml_anomaly, ml_score, ml_reason = ml_detector.predict_anomaly(features)
        except Exception as e:
            # ML detection is optional, don't fail if it errors
            import logging
            logging.getLogger(__name__).warning(f"ML anomaly detection error: {e}")
        
        # Combine all detection results
        is_suspicious = multiple_attempts or geo_anomaly or time_anomaly or ml_anomaly
        
        reasons = []
        if attempts_reason:
            reasons.append(attempts_reason)
        if geo_reason:
            reasons.append(geo_reason)
        if time_reason:
            reasons.append(time_reason)
        if ml_reason and ml_anomaly:
            reasons.append(ml_reason)
        
        return {
            'is_suspicious': is_suspicious,
            'reasons': reasons,
            'multiple_attempts': multiple_attempts,
            'attempts_count': attempts_count,
            'geo_anomaly': geo_anomaly,
            'time_anomaly': time_anomaly,
            'ml_anomaly': ml_anomaly,
            'ml_score': ml_score
        }
    
    @staticmethod
    def cleanup_old_records(days=90):
        """
        Remove old suspicious activity records
        
        Args:
            days: Number of days to keep records
            
        Returns:
            int: Number of records deleted
        """
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        old_records = SuspiciousActivity.query.filter(
            SuspiciousActivity.timestamp < cutoff_date
        ).all()
        
        count = len(old_records)
        for record in old_records:
            db.session.delete(record)
        
        db.session.commit()
        return count


class AuditActionType(Enum):
    """Types of actions that can be audited"""
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    REGISTER = "REGISTER"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PROFILE_UPDATE = "PROFILE_UPDATE"
    PANEL_DOWNLOAD = "PANEL_DOWNLOAD"
    PANEL_UPLOAD = "PANEL_UPLOAD"
    PANEL_DELETE = "PANEL_DELETE"
    PANEL_CREATE = "PANEL_CREATE"
    PANEL_UPDATE = "PANEL_UPDATE"
    PANEL_SHARE = "PANEL_SHARE"
    PANEL_LIST = "PANEL_LIST"
    PANEL_EXPORT_TEMPLATE_CREATE = "PANEL_EXPORT_TEMPLATE_CREATE"
    PANEL_EXPORT_TEMPLATE_UPDATE = "PANEL_EXPORT_TEMPLATE_UPDATE"
    PANEL_EXPORT_TEMPLATE_DELETE = "PANEL_EXPORT_TEMPLATE_DELETE"
    SEARCH = "SEARCH"
    VIEW = "VIEW"
    CACHE_CLEAR = "CACHE_CLEAR"
    ADMIN_ACTION = "ADMIN_ACTION"
    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    USER_DELETE = "USER_DELETE"
    ROLE_CHANGE = "ROLE_CHANGE"
    DATA_EXPORT = "DATA_EXPORT"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    SESSION_MANAGEMENT = "SESSION_MANAGEMENT"
    ERROR = "ERROR"
    
    # Enhanced Security Audit Types
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    ACCESS_DENIED = "ACCESS_DENIED"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    BRUTE_FORCE_ATTEMPT = "BRUTE_FORCE_ATTEMPT"
    ACCOUNT_LOCKOUT = "ACCOUNT_LOCKOUT"
    PASSWORD_RESET = "PASSWORD_RESET"
    MFA_EVENT = "MFA_EVENT"
    API_ACCESS = "API_ACCESS"
    FILE_ACCESS = "FILE_ACCESS"
    DATA_BREACH_ATTEMPT = "DATA_BREACH_ATTEMPT"
    COMPLIANCE_EVENT = "COMPLIANCE_EVENT"
    SYSTEM_SECURITY = "SYSTEM_SECURITY"

class AuditLog(db.Model):
    """Comprehensive audit trail for user actions and system changes"""
    id = db.Column(db.Integer, primary_key=True)
    
    # User information
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Nullable for anonymous actions
    username = db.Column(db.String(80), nullable=True)  # Store username for reference even if user is deleted
    
    # Action details
    action_type = db.Column(db.Enum(AuditActionType), nullable=False)
    action_description = db.Column(db.String(500), nullable=False)
    
    # Request/Session information
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(500))
    session_id = db.Column(db.String(200))  # Updated length for longer session IDs
    
    # Resource information
    resource_type = db.Column(db.String(50))  # e.g., 'panel', 'user', 'search'
    resource_id = db.Column(db.String(100))   # ID of the affected resource
    
    # Encrypted change tracking - store as encrypted fields
    _old_values = db.Column('old_values_encrypted', db.Text)  # Encrypted JSON string of old values
    _new_values = db.Column('new_values_encrypted', db.Text)  # Encrypted JSON string of new values
    _details = db.Column('details_encrypted', db.Text)       # Encrypted JSON string for additional context
    
    # Use encryption descriptors for sensitive audit data
    old_values = EncryptedJSONField('_old_values')
    new_values = EncryptedJSONField('_new_values')
    details = EncryptedJSONField('_details')
    
    # Timestamp and status
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)
    success = db.Column(db.Boolean, default=True, nullable=False)
    error_message = db.Column(db.String(1000))
    
    # Performance metrics
    duration_ms = db.Column(db.Integer)  # Action duration in milliseconds
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.action_type.value} by {self.username or "Anonymous"} at {self.timestamp}>'
    
    def to_dict(self):
        """Convert audit log to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action_type': self.action_type.value if self.action_type else None,
            'action_description': self.action_description,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'session_id': self.session_id,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'success': self.success,
            'error_message': self.error_message,
            'duration_ms': self.duration_ms
        }

class PanelDownload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Optional for anonymous users
    ip_address = db.Column(db.String(45), nullable=False)
    download_date = db.Column(db.DateTime, nullable=False)
    panel_ids = db.Column(db.String(255), nullable=False)  # Comma-separated list of panel IDs
    list_types = db.Column(db.String(255), nullable=False)  # Comma-separated list of list types
    gene_count = db.Column(db.Integer)  # Number of genes in the downloaded list


class AdminMessage(db.Model):
    """Admin messages displayed on the main page"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Message content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='info', nullable=False)  # info, warning, success, error
    
    # Admin who created the message
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_by = db.relationship('User', backref='admin_messages')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional expiration date
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f'<AdminMessage {self.id}: {self.title}>'
    
    def is_expired(self):
        """Check if the message has expired"""
        if self.expires_at is None:
            return False
        return datetime.datetime.now() > self.expires_at
    
    def is_visible(self):
        """Check if the message should be displayed"""
        return self.is_active and not self.is_expired()
    
    @classmethod
    def get_active_messages(cls):
        """Get all active, non-expired messages"""
        current_time = datetime.datetime.now()
        return cls.query.filter(
            cls.is_active == True,
            db.or_(cls.expires_at == None, cls.expires_at > current_time)
        ).order_by(cls.created_at.desc()).all()


# ===== SAVED PANELS SYSTEM MODELS =====

class PanelStatus(Enum):
    """Status of a saved panel"""
    ACTIVE = "ACTIVE"           # Panel is active and available
    ARCHIVED = "ARCHIVED"       # Panel is archived but accessible
    DELETED = "DELETED"         # Panel is soft-deleted
    DRAFT = "DRAFT"            # Panel is in draft state

class PanelVisibility(Enum):
    """Visibility levels for panels"""
    PRIVATE = "PRIVATE"         # Only owner can see
    SHARED = "SHARED"          # Shared with specific users/teams
    PUBLIC = "PUBLIC"          # Visible to all users (future feature)

class SavedPanel(db.Model):
    """Main saved panel model - stores panel metadata"""
    __tablename__ = 'saved_panels'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Panel metadata
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text)
    tags = db.Column(db.String(500))  # Comma-separated tags
    
    # Ownership and permissions
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    owner = db.relationship('User', backref='saved_panels', lazy=True)
    
    # Panel properties
    status = db.Column(db.Enum(PanelStatus), default=PanelStatus.ACTIVE, nullable=False, index=True)
    visibility = db.Column(db.Enum(PanelVisibility), default=PanelVisibility.PRIVATE, nullable=False)
    gene_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Source information
    source_type = db.Column(db.String(50))  # 'upload', 'panelapp', 'manual', 'template'
    source_reference = db.Column(db.String(1000))  # Increased from 255 to 1000 for longer panel lists
    
    # Version tracking
    current_version_id = db.Column(db.Integer, db.ForeignKey('panel_versions.id'), nullable=True)
    version_count = db.Column(db.Integer, default=1, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, nullable=False)
    last_accessed_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    
    # Storage backend reference
    storage_backend = db.Column(db.String(20), default='gcs', nullable=False)  # 'gcs', 'local'
    storage_path = db.Column(db.String(500))  # Path in storage backend
    
    # Relationships
    versions = db.relationship('PanelVersion', backref='panel', lazy='dynamic', 
                             foreign_keys='PanelVersion.panel_id')
    current_version = db.relationship('PanelVersion', foreign_keys=[current_version_id], 
                                    post_update=True, uselist=False)
    shares = db.relationship('PanelShare', backref='panel', lazy='dynamic', cascade='all, delete-orphan')
    genes = db.relationship('PanelGene', backref='panel', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_saved_panels_owner_status', 'owner_id', 'status'),
        db.Index('idx_saved_panels_created', 'created_at'),
        db.Index('idx_saved_panels_updated', 'updated_at'),
        db.Index('idx_saved_panels_name_owner', 'name', 'owner_id'),
    )
    
    def __repr__(self):
        return f'<SavedPanel {self.id}: {self.name} by {self.owner.username if self.owner else "Unknown"}>'
    
    def get_latest_version(self):
        """Get the latest version of this panel"""
        return self.versions.order_by(PanelVersion.version_number.desc()).first()
    
    @property
    def current_version_number(self):
        """Get the current version number"""
        if self.current_version:
            return self.current_version.version_number
        latest = self.get_latest_version()
        return latest.version_number if latest else 1
    
    def create_new_version(self, user_id, comment=None, changes_summary=None):
        """Create a new version of this panel"""
        latest = self.get_latest_version()
        new_version_number = (latest.version_number + 1) if latest else 1
        
        new_version = PanelVersion(
            panel_id=self.id,
            version_number=new_version_number,
            created_by_id=user_id,
            comment=comment or f"Version {new_version_number}",
            changes_summary=changes_summary,
            gene_count=self.gene_count
        )
        
        db.session.add(new_version)
        db.session.flush()  # Get the ID
        
        # Update panel reference
        self.current_version_id = new_version.id
        self.version_count = new_version_number
        self.updated_at = datetime.datetime.now()

        print("Created new PanelVersion:", new_version.id, new_version.version_number)
        
        return new_version
    
    def is_shared_with_user(self, user_id):
        """Check if panel is shared with specific user"""
        return self.shares.filter_by(shared_with_user_id=user_id, is_active=True).first() is not None
    
    def to_dict(self, include_genes=False):
        """Convert panel to dictionary"""
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'tags': self.tags.split(',') if self.tags else [],
            'owner': {
                'id': self.owner.id,
                'username': self.owner.username,
                'full_name': self.owner.get_full_name()
            } if self.owner else None,
            'status': self.status.value,
            'visibility': self.visibility.value,
            'gene_count': self.gene_count,
            'source_type': self.source_type,
            'source_reference': self.source_reference,
            'version_count': self.version_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
        }
        
        if include_genes:
            result['genes'] = [gene.to_dict() for gene in self.genes.filter_by(is_active=True)]
        
        return result

class PanelVersion(db.Model):
    """Panel version history - tracks changes over time"""
    __tablename__ = 'panel_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('saved_panels.id'), nullable=False, index=True)
    
    # Version information
    version_number = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    
    # Version metadata
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_by = db.relationship('User', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    
    # Snapshot data
    gene_count = db.Column(db.Integer, default=0)
    changes_summary = db.Column(db.Text)  # JSON string of what changed
    
    # Storage reference for this version
    storage_path = db.Column(db.String(500))  # Path to version data in storage
    
    # Version control enhancements
    is_protected = db.Column(db.Boolean, default=False, nullable=False, index=True)
    retention_priority = db.Column(db.Integer, default=1, nullable=False, index=True)
    last_accessed_at = db.Column(db.DateTime, index=True)
    access_count = db.Column(db.Integer, default=0, nullable=False)
    size_bytes = db.Column(db.BigInteger)
    
    # Relationships
    changes = db.relationship('PanelChange', backref='version', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('PanelVersionTag', backref='version', lazy='dynamic', cascade='all, delete-orphan')
    version_metadata = db.relationship('PanelVersionMetadata', backref='version', uselist=False, cascade='all, delete-orphan', primaryjoin='PanelVersion.id == PanelVersionMetadata.version_id')
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('panel_id', 'version_number', name='uq_panel_version'),
        db.Index('idx_panel_versions_panel_version', 'panel_id', 'version_number'),
        db.Index('idx_panel_versions_created', 'created_at'),
        db.Index('idx_panel_versions_protected', 'is_protected'),
        db.Index('idx_panel_versions_priority', 'retention_priority'),
        db.Index('idx_panel_versions_accessed', 'last_accessed_at'),
    )
    
    def __repr__(self):
        return f'<PanelVersion {self.panel_id}v{self.version_number}>'
    
    def to_dict(self, include_tags=False, include_metadata=False):
        """Convert version to dictionary"""
        result = {
            'id': self.id,
            'version_number': self.version_number,
            'comment': self.comment,
            'created_by': {
                'id': self.created_by.id,
                'username': self.created_by.username,
                'full_name': self.created_by.get_full_name()
            } if self.created_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'gene_count': self.gene_count,
            'changes_summary': self.changes_summary,
            'is_protected': self.is_protected,
            'retention_priority': self.retention_priority,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            'access_count': self.access_count,
            'size_bytes': self.size_bytes
        }
        
        if include_tags:
            result['tags'] = [tag.to_dict() for tag in self.tags]
        
        if include_metadata and self.version_metadata:
            result['metadata'] = self.version_metadata.to_dict()
        
        return result

    def update_access_stats(self):
        """Update access statistics for this version"""
        self.last_accessed_at = datetime.datetime.now()
        self.access_count += 1
        db.session.commit()

    def add_tag(self, tag_name: str, tag_type: 'TagType', user_id: int, description: str = None):
        """Add a tag to this version"""
        from app.version_control_service import TagType
        
        tag = PanelVersionTag(
            version_id=self.id,
            tag_name=tag_name,
            tag_type=tag_type,
            description=description,
            created_by_id=user_id,
            is_protected=(tag_type in [TagType.PRODUCTION, TagType.STAGING])
        )
        db.session.add(tag)
        
        # Mark version as protected if it has protected tags
        if tag_type in [TagType.PRODUCTION, TagType.STAGING]:
            self.is_protected = True
            self.retention_priority = 10  # High priority
        
        return tag

    def get_tags_by_type(self, tag_type: 'TagType' = None) -> List['PanelVersionTag']:
        """Get tags for this version, optionally filtered by type"""
        query = self.tags
        if tag_type:
            query = query.filter_by(tag_type=tag_type)
        return query.all()

    def is_deletable(self) -> bool:
        """Check if this version can be deleted based on protection and tags"""
        if self.is_protected:
            return False
        
        # Check for protected tags
        protected_tags = self.tags.filter_by(is_protected=True).first()
        if protected_tags:
            return False
        
        return True

class PanelGene(db.Model):
    """Individual genes within a saved panel"""
    __tablename__ = 'panel_genes'
    
    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('saved_panels.id'), nullable=False, index=True)
    
    # Gene information
    gene_symbol = db.Column(db.String(50), nullable=False, index=True)
    gene_name = db.Column(db.String(255))
    ensembl_id = db.Column(db.String(100), index=True)
    hgnc_id = db.Column(db.String(100))
    
    # Panel-specific gene data
    confidence_level = db.Column(db.String(100))  # 'high', 'medium', 'low'
    mode_of_inheritance = db.Column(db.String(500))  # For example: 'MONOALLELIC, autosomal or pseudoautosomal, imprinted status unknown'
    phenotype = db.Column(db.Text) # Source data may be a list: ['Dyskeratosis congenita, autosomal recessive 5 615190', '615190 DC type 4 and 5', '616373 Pulmonary fibrosis and/or bone marrow failure, telomere-related', 'Dyskeratosis congenita, autosomal dominant 4, 615190', 'Dyskeratosis congenita, autosomal recessive 5, 615190', '615190 Dyskeratosis congenita', '616373 Pulmonary fibrosis and/or bone marrow failure, telomere-related, 3']
    evidence_level = db.Column(db.String(200))  # Source data may be a list: ['NHS GMS', 'Expert Review Green']
    
    # Source information
    source_panel_id = db.Column(db.String(100))  # Original PanelApp panel ID
    source_list_type = db.Column(db.String(100))  # 'green', 'amber', 'red'
    
    # Status and metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    added_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    added_by = db.relationship('User', lazy=True)
    added_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    
    # Custom user notes and modifications
    user_notes = db.Column(db.Text)
    custom_confidence = db.Column(db.String(20))  # User override of confidence
    is_modified = db.Column(db.Boolean, default=False)  # True if user modified this gene
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_panel_genes_panel_active', 'panel_id', 'is_active'),
        db.Index('idx_panel_genes_symbol', 'gene_symbol'),
        db.Index('idx_panel_genes_panel_symbol', 'panel_id', 'gene_symbol'),
        db.UniqueConstraint('panel_id', 'gene_symbol', name='uq_panel_gene_symbol'),
    )
    
    def __repr__(self):
        return f'<PanelGene {self.gene_symbol} in panel {self.panel_id}>'
    
    def to_dict(self):
        """Convert gene to dictionary"""
        return {
            'id': self.id,
            'gene_symbol': self.gene_symbol,
            'gene_name': self.gene_name,
            'ensembl_id': self.ensembl_id,
            'hgnc_id': self.hgnc_id,
            'confidence_level': self.confidence_level,
            'mode_of_inheritance': self.mode_of_inheritance,
            'phenotype': self.phenotype,
            'evidence_level': self.evidence_level,
            'source_panel_id': self.source_panel_id,
            'source_list_type': self.source_list_type,
            'is_active': self.is_active,
            'added_by': {
                'id': self.added_by.id,
                'username': self.added_by.username
            } if self.added_by else None,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'user_notes': self.user_notes,
            'custom_confidence': self.custom_confidence,
            'is_modified': self.is_modified,
        }

class SharePermission(Enum):
    """Permission levels for shared panels"""
    VIEW = "VIEW"          # Can view the panel
    COMMENT = "COMMENT"    # Can view and comment
    EDIT = "EDIT"         # Can modify the panel
    ADMIN = "ADMIN"       # Can manage sharing and permissions

class PanelShare(db.Model):
    """Panel sharing and collaboration"""
    __tablename__ = 'panel_shares'
    
    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('saved_panels.id'), nullable=False, index=True)
    
    # Sharing details
    shared_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_by = db.relationship('User', foreign_keys=[shared_by_id], lazy=True)
    
    shared_with_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    shared_with_user = db.relationship('User', foreign_keys=[shared_with_user_id], lazy=True)
    
    # Team sharing (future feature)
    shared_with_team_id = db.Column(db.Integer, nullable=True)  # Future: ForeignKey to Team model
    
    # Permissions and settings
    permission_level = db.Column(db.Enum(SharePermission), default=SharePermission.VIEW, nullable=False)
    can_reshare = db.Column(db.Boolean, default=False, nullable=False)
    
    # Status and metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional expiration
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    last_accessed_at = db.Column(db.DateTime, nullable=True)
    
    # Optional sharing link
    share_token = db.Column(db.String(255), unique=True, nullable=True, index=True)
    
    # Constraints
    __table_args__ = (
        db.Index('idx_panel_shares_panel_active', 'panel_id', 'is_active'),
        db.Index('idx_panel_shares_user_active', 'shared_with_user_id', 'is_active'),
        db.CheckConstraint(
            '(shared_with_user_id IS NOT NULL) OR (shared_with_team_id IS NOT NULL) OR (share_token IS NOT NULL)',
            name='check_share_target'
        ),
    )
    
    def __repr__(self):
        return f'<PanelShare panel:{self.panel_id} with user:{self.shared_with_user_id}>'
    
    def is_expired(self):
        """Check if the share has expired"""
        return self.expires_at and datetime.datetime.now() > self.expires_at
    
    def is_valid(self):
        """Check if the share is valid and active"""
        return self.is_active and not self.is_expired()
    
    def to_dict(self):
        """Convert share to dictionary"""
        return {
            'id': self.id,
            'panel_id': self.panel_id,
            'shared_by': {
                'id': self.shared_by.id,
                'username': self.shared_by.username,
                'full_name': self.shared_by.get_full_name()
            } if self.shared_by else None,
            'shared_with_user': {
                'id': self.shared_with_user.id,
                'username': self.shared_with_user.username,
                'full_name': self.shared_with_user.get_full_name()
            } if self.shared_with_user else None,
            'permission_level': self.permission_level.value,
            'can_reshare': self.can_reshare,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
        }

class ChangeType(Enum):
    """Types of changes that can be tracked"""
    PANEL_CREATED = "PANEL_CREATED"
    GENE_ADDED = "GENE_ADDED"
    GENE_REMOVED = "GENE_REMOVED"
    GENE_MODIFIED = "GENE_MODIFIED"
    METADATA_CHANGED = "METADATA_CHANGED"
    CONFIDENCE_CHANGED = "CONFIDENCE_CHANGED"
    SOURCE_UPDATED = "SOURCE_UPDATED"


class TagType(Enum):
    """Types of version tags"""
    PRODUCTION = "PRODUCTION"
    STAGING = "STAGING"
    RELEASE = "RELEASE"
    HOTFIX = "HOTFIX"
    FEATURE = "FEATURE"
    BACKUP = "BACKUP"


class VersionType(Enum):
    """Types of versions in the version control system"""
    MAIN = "MAIN"
    BRANCH = "BRANCH"
    TAG = "TAG"
    MERGE = "MERGE"


class PanelVersionTag(db.Model):
    """Tags for panel versions"""
    __tablename__ = 'panel_version_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('panel_versions.id', ondelete='CASCADE'), nullable=False, index=True)
    tag_name = db.Column(db.String(100), nullable=False, index=True)
    tag_type = db.Column(db.Enum(TagType), nullable=False, index=True)
    description = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_by = db.relationship('User', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    is_protected = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('version_id', 'tag_name', name='uq_version_tag_name'),
        db.Index('idx_panel_tags_version', 'version_id'),
        db.Index('idx_panel_tags_name', 'tag_name'),
        db.Index('idx_panel_tags_type', 'tag_type'),
        db.Index('idx_panel_tags_protected', 'is_protected'),
    )
    
    def __repr__(self):
        return f'<PanelVersionTag {self.tag_name}:{self.tag_type.value}>'
    
    def to_dict(self):
        """Convert tag to dictionary"""
        return {
            'id': self.id,
            'version_id': self.version_id,
            'tag_name': self.tag_name,
            'tag_type': self.tag_type.value,
            'description': self.description,
            'created_by': {
                'id': self.created_by.id,
                'username': self.created_by.username
            } if self.created_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_protected': self.is_protected
        }


class PanelVersionBranch(db.Model):
    """Branches for panel version control"""
    __tablename__ = 'panel_version_branches'
    
    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('saved_panels.id', ondelete='CASCADE'), nullable=False, index=True)
    branch_name = db.Column(db.String(100), nullable=False, index=True)
    parent_version_id = db.Column(db.Integer, db.ForeignKey('panel_versions.id'), nullable=False)
    head_version_id = db.Column(db.Integer, db.ForeignKey('panel_versions.id'), nullable=True)
    description = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_by = db.relationship('User', foreign_keys=[created_by_id], lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_merged = db.Column(db.Boolean, default=False, nullable=False, index=True)
    merged_at = db.Column(db.DateTime)
    merged_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    merged_by = db.relationship('User', foreign_keys=[merged_by_id], lazy=True)
    
    # Relationships
    parent_version = db.relationship('PanelVersion', foreign_keys=[parent_version_id], lazy=True)
    head_version = db.relationship('PanelVersion', foreign_keys=[head_version_id], lazy=True)
    panel = db.relationship('SavedPanel', lazy=True)
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('panel_id', 'branch_name', name='uq_panel_branch_name'),
        db.Index('idx_panel_branches_panel', 'panel_id'),
        db.Index('idx_panel_branches_name', 'branch_name'),
        db.Index('idx_panel_branches_active', 'is_active'),
        db.Index('idx_panel_branches_merged', 'is_merged'),
    )
    
    def __repr__(self):
        return f'<PanelVersionBranch {self.branch_name}>'
    
    def to_dict(self):
        """Convert branch to dictionary"""
        return {
            'id': self.id,
            'panel_id': self.panel_id,
            'branch_name': self.branch_name,
            'description': self.description,
            'parent_version': {
                'id': self.parent_version.id,
                'version_number': self.parent_version.version_number
            } if self.parent_version else None,
            'head_version': {
                'id': self.head_version.id,
                'version_number': self.head_version.version_number
            } if self.head_version else None,
            'created_by': {
                'id': self.created_by.id,
                'username': self.created_by.username
            } if self.created_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'is_merged': self.is_merged,
            'merged_at': self.merged_at.isoformat() if self.merged_at else None,
            'merged_by': {
                'id': self.merged_by.id,
                'username': self.merged_by.username
            } if self.merged_by else None
        }

    def mark_as_merged(self, user_id: int):
        """Mark this branch as merged"""
        self.is_merged = True
        self.merged_at = datetime.datetime.now()
        self.merged_by_id = user_id
        self.is_active = False


class PanelVersionMetadata(db.Model):
    """Extended metadata for panel versions"""
    __tablename__ = 'panel_version_metadata'
    
    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('panel_versions.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    version_type = db.Column(db.Enum(VersionType), default=VersionType.MAIN, nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('panel_version_branches.id'), nullable=True, index=True)
    parent_version_id = db.Column(db.Integer, db.ForeignKey('panel_versions.id'), nullable=True)
    merge_source_version_id = db.Column(db.Integer, db.ForeignKey('panel_versions.id'), nullable=True)
    commit_hash = db.Column(db.String(64), nullable=True, index=True)
    diff_summary = db.Column(db.Text)
    file_changes_count = db.Column(db.Integer, default=0, nullable=False)
    lines_added = db.Column(db.Integer, default=0, nullable=False)
    lines_removed = db.Column(db.Integer, default=0, nullable=False)
    retention_priority = db.Column(db.Integer, default=1, nullable=False, index=True)
    
    # Relationships
    branch = db.relationship('PanelVersionBranch', lazy=True)
    parent_version = db.relationship('PanelVersion', foreign_keys=[parent_version_id], lazy=True)
    merge_source_version = db.relationship('PanelVersion', foreign_keys=[merge_source_version_id], lazy=True)
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('version_id', name='uq_version_metadata'),
        db.Index('idx_version_metadata_version', 'version_id'),
        db.Index('idx_version_metadata_type', 'version_type'),
        db.Index('idx_version_metadata_branch', 'branch_id'),
        db.Index('idx_version_metadata_priority', 'retention_priority'),
        db.Index('idx_version_metadata_hash', 'commit_hash'),
    )
    
    def __repr__(self):
        return f'<PanelVersionMetadata {self.version_id}:{self.version_type.value}>'
    
    def to_dict(self):
        """Convert metadata to dictionary"""
        return {
            'id': self.id,
            'version_id': self.version_id,
            'version_type': self.version_type.value,
            'branch': {
                'id': self.branch.id,
                'name': self.branch.branch_name
            } if self.branch else None,
            'parent_version': {
                'id': self.parent_version.id,
                'version_number': self.parent_version.version_number
            } if self.parent_version else None,
            'merge_source_version': {
                'id': self.merge_source_version.id,
                'version_number': self.merge_source_version.version_number
            } if self.merge_source_version else None,
            'commit_hash': self.commit_hash,
            'diff_summary': self.diff_summary,
            'file_changes_count': self.file_changes_count,
            'lines_added': self.lines_added,
            'lines_removed': self.lines_removed,
            'retention_priority': self.retention_priority
        }


class PanelRetentionPolicy(db.Model):
    """Configurable retention policies for panels"""
    __tablename__ = 'panel_retention_policies'
    
    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('saved_panels.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    max_versions = db.Column(db.Integer, default=10, nullable=False)
    backup_retention_days = db.Column(db.Integer, default=90, nullable=False)
    keep_tagged_versions = db.Column(db.Boolean, default=True, nullable=False)
    keep_production_tags = db.Column(db.Boolean, default=True, nullable=False)
    auto_cleanup_enabled = db.Column(db.Boolean, default=True, nullable=False)
    last_cleanup_at = db.Column(db.DateTime)
    cleanup_frequency_hours = db.Column(db.Integer, default=24, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_by = db.relationship('User', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, nullable=False)
    
    # Relationships
    panel = db.relationship('SavedPanel', lazy=True)
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('panel_id', name='uq_panel_retention_policy'),
        db.Index('idx_retention_policies_panel', 'panel_id'),
        db.Index('idx_retention_policies_cleanup', 'auto_cleanup_enabled', 'last_cleanup_at'),
    )
    
    def __repr__(self):
        return f'<PanelRetentionPolicy {self.panel_id}: max={self.max_versions}>'
    
    def to_dict(self):
        """Convert retention policy to dictionary"""
        return {
            'id': self.id,
            'panel_id': self.panel_id,
            'max_versions': self.max_versions,
            'backup_retention_days': self.backup_retention_days,
            'keep_tagged_versions': self.keep_tagged_versions,
            'keep_production_tags': self.keep_production_tags,
            'auto_cleanup_enabled': self.auto_cleanup_enabled,
            'last_cleanup_at': self.last_cleanup_at.isoformat() if self.last_cleanup_at else None,
            'cleanup_frequency_hours': self.cleanup_frequency_hours,
            'created_by': {
                'id': self.created_by.id,
                'username': self.created_by.username
            } if self.created_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def needs_cleanup(self) -> bool:
        """Check if cleanup is needed based on frequency"""
        if not self.auto_cleanup_enabled:
            return False
        
        if not self.last_cleanup_at:
            return True
        
        frequency_delta = datetime.timedelta(hours=self.cleanup_frequency_hours)
        return datetime.datetime.now() - self.last_cleanup_at > frequency_delta

    def update_cleanup_timestamp(self):
        """Update the last cleanup timestamp"""
        self.last_cleanup_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()


class PanelChange(db.Model):
    """Detailed change tracking for panels"""
    __tablename__ = 'panel_changes'
    
    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('saved_panels.id'), nullable=False, index=True)
    version_id = db.Column(db.Integer, db.ForeignKey('panel_versions.id'), nullable=False, index=True)
    
    # Change details
    change_type = db.Column(db.Enum(ChangeType), nullable=False)
    target_type = db.Column(db.String(50), nullable=False)  # 'gene', 'metadata', 'panel'
    target_id = db.Column(db.String(100))  # Gene symbol or field name
    
    # Change data (encrypted for sensitive information)
    _old_value = db.Column('old_value_encrypted', db.Text)
    _new_value = db.Column('new_value_encrypted', db.Text)
    
    # Use encryption descriptors
    old_value = EncryptedJSONField('_old_value')
    new_value = EncryptedJSONField('_new_value')
    
    # Metadata
    changed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    changed_by = db.relationship('User', lazy=True)
    changed_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    
    change_reason = db.Column(db.String(255))  # Optional reason for change
    
    # Indexes
    __table_args__ = (
        db.Index('idx_panel_changes_panel_version', 'panel_id', 'version_id'),
        db.Index('idx_panel_changes_type', 'change_type'),
        db.Index('idx_panel_changes_date', 'changed_at'),
    )
    
    def __repr__(self):
        return f'<PanelChange {self.change_type.value} on {self.target_type}:{self.target_id}>'
    
    def to_dict(self):
        """Convert change to dictionary"""
        return {
            'id': self.id,
            'change_type': self.change_type.value,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'changed_by': {
                'id': self.changed_by.id,
                'username': self.changed_by.username,
                'full_name': self.changed_by.get_full_name()
            } if self.changed_by else None,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None,
            'change_reason': self.change_reason,
        }


class ExportTemplate(db.Model):
    """Export templates for saving user export preferences"""
    __tablename__ = 'export_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # Template details
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    
    # Export settings
    format = db.Column(db.String(20), nullable=False)  # excel, csv, tsv, json
    include_metadata = db.Column(db.Boolean, default=True, nullable=False)
    include_versions = db.Column(db.Boolean, default=True, nullable=False)
    include_genes = db.Column(db.Boolean, default=True, nullable=False)
    
    # Optional filename pattern (e.g., "{panel_name}_{date}")
    filename_pattern = db.Column(db.String(255))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, nullable=False)
    last_used_at = db.Column(db.DateTime)
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('export_templates', lazy='dynamic'))
    
    # Indexes
    __table_args__ = (
        db.Index('idx_export_templates_user', 'user_id'),
        db.Index('idx_export_templates_default', 'user_id', 'is_default'),
        db.UniqueConstraint('user_id', 'name', name='uq_user_template_name'),
    )
    
    def __repr__(self):
        return f'<ExportTemplate {self.name} ({self.format})>'
    
    def to_dict(self):
        """Convert template to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_default': self.is_default,
            'format': self.format,
            'include_metadata': self.include_metadata,
            'include_versions': self.include_versions,
            'include_genes': self.include_genes,
            'filename_pattern': self.filename_pattern,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'usage_count': self.usage_count
        }
    
    def mark_as_used(self):
        """Update usage statistics"""
        self.last_used_at = datetime.datetime.now()
        self.usage_count += 1
        self.updated_at = datetime.datetime.now()


# ===== LITERATURE REVIEW SYSTEM MODELS =====

class LiteratureSearch(db.Model):
    """Stores user's PubMed search history"""
    __tablename__ = 'literature_searches'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    user = db.relationship('User', backref=db.backref('literature_searches', lazy='dynamic'))

    # Search parameters
    search_query = db.Column('query', db.Text, nullable=False)
    filters = db.Column(db.JSON)            # date range, publication types, etc.
    result_count = db.Column(db.Integer, default=0, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False, index=True)

    # Relationships
    results = db.relationship('SearchResult', backref='search', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_lit_searches_user', 'user_id'),
        db.Index('idx_lit_searches_created', 'created_at'),
    )

    def __repr__(self):
        return f'<LiteratureSearch {self.id}: "{self.search_query[:40]}" by user {self.user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'query': self.search_query,
            'filters': self.filters,
            'result_count': self.result_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class LiteratureArticle(db.Model):
    """Cached PubMed article metadata"""
    __tablename__ = 'literature_articles'

    id = db.Column(db.Integer, primary_key=True)

    # PubMed identifiers
    pubmed_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    pmc_id = db.Column(db.String(20), index=True)
    doi = db.Column(db.String(255), index=True)

    # Article metadata
    title = db.Column(db.Text, nullable=False)
    abstract = db.Column(db.Text)
    authors = db.Column(db.JSON)            # list of author name strings
    journal = db.Column(db.String(500))
    publication_date = db.Column(db.Date)
    publication_types = db.Column(db.JSON)  # e.g. ["Journal Article", "Review"]
    mesh_terms = db.Column(db.JSON)         # list of MeSH term strings
    keywords = db.Column(db.JSON)           # author keywords
    gene_mentions = db.Column(db.JSON)      # gene symbols extracted from title/abstract

    # Cache management
    cached_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    cache_expires_at = db.Column(db.DateTime, index=True)

    # Relationships
    search_results = db.relationship('SearchResult', backref='article', lazy='dynamic', cascade='all, delete-orphan')
    user_actions = db.relationship('UserArticleAction', backref='article', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_lit_articles_pubmed', 'pubmed_id'),
        db.Index('idx_lit_articles_cache_expires', 'cache_expires_at'),
    )

    def __repr__(self):
        return f'<LiteratureArticle {self.pubmed_id}: {self.title[:60] if self.title else ""}>'

    def to_dict(self):
        return {
            'id': self.id,
            'pubmed_id': self.pubmed_id,
            'pmc_id': self.pmc_id,
            'doi': self.doi,
            'title': self.title,
            'abstract': self.abstract,
            'authors': self.authors,
            'journal': self.journal,
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'publication_types': self.publication_types,
            'mesh_terms': self.mesh_terms,
            'keywords': self.keywords,
            'gene_mentions': self.gene_mentions,
            'cached_at': self.cached_at.isoformat() if self.cached_at else None,
            'cache_expires_at': self.cache_expires_at.isoformat() if self.cache_expires_at else None,
        }


class SearchResult(db.Model):
    """Junction table linking searches to articles (with rank)"""
    __tablename__ = 'search_results'

    id = db.Column(db.Integer, primary_key=True)
    search_id = db.Column(db.Integer, db.ForeignKey('literature_searches.id', ondelete='CASCADE'), nullable=False, index=True)
    article_id = db.Column(db.Integer, db.ForeignKey('literature_articles.id', ondelete='CASCADE'), nullable=False, index=True)
    rank = db.Column(db.Integer)            # position in PubMed result list

    __table_args__ = (
        db.UniqueConstraint('search_id', 'article_id', name='uq_search_article'),
        db.Index('idx_search_results_search', 'search_id'),
        db.Index('idx_search_results_article', 'article_id'),
    )

    def __repr__(self):
        return f'<SearchResult search:{self.search_id} article:{self.article_id} rank:{self.rank}>'


class UserArticleAction(db.Model):
    """Tracks per-user actions on articles (save, view, export)"""
    __tablename__ = 'user_article_actions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    article_id = db.Column(db.Integer, db.ForeignKey('literature_articles.id', ondelete='CASCADE'), nullable=False, index=True)
    user = db.relationship('User', backref=db.backref('article_actions', lazy='dynamic'))

    # Action tracking
    is_saved = db.Column(db.Boolean, default=False, nullable=False)
    is_viewed = db.Column(db.Boolean, default=False, nullable=False)
    view_count = db.Column(db.Integer, default=0, nullable=False)
    notes = db.Column(db.Text)             # user's personal notes on the article

    # Timestamps
    first_viewed_at = db.Column(db.DateTime)
    last_viewed_at = db.Column(db.DateTime)
    saved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'article_id', name='uq_user_article_action'),
        db.Index('idx_user_article_actions_user', 'user_id'),
        db.Index('idx_user_article_actions_article', 'article_id'),
        db.Index('idx_user_article_actions_saved', 'user_id', 'is_saved'),
    )

    def __repr__(self):
        return f'<UserArticleAction user:{self.user_id} article:{self.article_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'article_id': self.article_id,
            'is_saved': self.is_saved,
            'is_viewed': self.is_viewed,
            'view_count': self.view_count,
            'notes': self.notes,
            'first_viewed_at': self.first_viewed_at.isoformat() if self.first_viewed_at else None,
            'last_viewed_at': self.last_viewed_at.isoformat() if self.last_viewed_at else None,
            'saved_at': self.saved_at.isoformat() if self.saved_at else None,
        }


class KnowhowCategory(db.Model):
    """Dynamic KnowHow category, managed by admins"""
    __tablename__ = 'knowhow_categories'

    id          = db.Column(db.Integer, primary_key=True)
    slug        = db.Column(db.String(64), unique=True, nullable=False)
    label       = db.Column(db.String(128), nullable=False)
    color       = db.Column(db.String(32), nullable=False, default='#0369a1')
    description = db.Column(db.Text, nullable=True)
    position    = db.Column(db.Integer, nullable=False, default=0)
    created_at  = db.Column(db.DateTime, default=datetime.datetime.now)

    subcategories = db.relationship(
        'KnowhowSubcategory', backref='category',
        cascade='all, delete-orphan',
        order_by='KnowhowSubcategory.position'
    )

    def __repr__(self):
        return f'<KnowhowCategory {self.slug}>'


class KnowhowSubcategory(db.Model):
    """Folder within a KnowHow category"""
    __tablename__ = 'knowhow_subcategories'

    id          = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('knowhow_categories.id', ondelete='CASCADE'), nullable=False)
    label       = db.Column(db.String(128), nullable=False)
    position    = db.Column(db.Integer, nullable=False, default=0)
    created_at  = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f'<KnowhowSubcategory {self.id}: {self.label}>'


class KnowhowLink(db.Model):
    """Community-contributed links for KnowHow sections"""
    __tablename__ = 'knowhow_links'

    id             = db.Column(db.Integer, primary_key=True)
    category       = db.Column(db.String(64), nullable=False, index=True)
    url            = db.Column(db.String(2048), nullable=False)
    description    = db.Column(db.String(512), nullable=False)
    user_id        = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('knowhow_subcategories.id', ondelete='SET NULL'), nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)

    user        = db.relationship('User', backref=db.backref('knowhow_links', lazy='dynamic'))
    subcategory = db.relationship('KnowhowSubcategory', backref=db.backref('links', lazy='dynamic'))

    def __repr__(self):
        return f'<KnowhowLink {self.category}: {self.url[:60]}>'


class KnowhowArticle(db.Model):
    """User-authored articles for KnowHow sections"""
    __tablename__ = 'knowhow_articles'

    id             = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(256), nullable=False)
    summary        = db.Column(db.String(512), nullable=True)
    category       = db.Column(db.String(64), nullable=False, index=True)
    content        = db.Column(db.Text, nullable=False, default='')
    user_id        = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('knowhow_subcategories.id', ondelete='SET NULL'), nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    updated_at     = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, nullable=False)

    user        = db.relationship('User', backref=db.backref('knowhow_articles', lazy='dynamic'))
    subcategory = db.relationship('KnowhowSubcategory', backref=db.backref('articles', lazy='dynamic'))

    def __repr__(self):
        return f'<KnowhowArticle {self.id}: {self.title[:60]}>'


class KnowhowBookmark(db.Model):
    """Personal reading-list bookmark linking a user to a KnowHow article"""
    __tablename__ = 'knowhow_bookmarks'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('knowhow_articles.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'article_id', name='uq_knowhow_bookmark_user_article'),
    )

    user    = db.relationship('User', backref=db.backref('knowhow_bookmarks', lazy='dynamic'))
    article = db.relationship('KnowhowArticle', backref=db.backref('bookmarks', lazy='dynamic'))

    def __repr__(self):
        return f'<KnowhowBookmark user={self.user_id} article={self.article_id}>'


class KnowhowReaction(db.Model):
    """Single-click 'Helpful' reaction on a KnowHow article (one per user per article)"""
    __tablename__ = 'knowhow_reactions'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('knowhow_articles.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'article_id', name='uq_knowhow_reaction_user_article'),
    )

    user    = db.relationship('User', backref=db.backref('knowhow_reactions', lazy='dynamic'))
    article = db.relationship('KnowhowArticle', backref=db.backref('reactions', lazy='dynamic'))

    def __repr__(self):
        return f'<KnowhowReaction user={self.user_id} article={self.article_id}>'


def db_init(app):
    """
    Initializes database connection. For testing, uses SQLite in-memory database.
    For production, uses Cloud SQL with Python Connector.
    """
    
    # Skip Cloud SQL connector for testing
    if app.config.get('TESTING', False):
        app.logger.info("Testing mode: Using SQLite in-memory database")
        # Use the SQLite URI from testing config
        db.init_app(app)
    else:
        # Production/Development Cloud SQL setup

        # --- Cloud SQL Python Connector Initialization ---   
        if app.config.get("CLOUD_SQL_CONNECTION_NAME"):
            try:
                connector = Connector()

                def getconn() -> sqlalchemy.engine.base.Connection:
                    conn = connector.connect(
                        app.config["CLOUD_SQL_CONNECTION_NAME"],
                        "pg8000",
                        user=app.config["DB_USER"],
                        password=app.config["DB_PASS"],
                        db=app.config["DB_NAME"],
                        ip_type=IPTypes.PRIVATE if os.getenv('CLOUD_RUN') else IPTypes.PUBLIC
                    )
                    return conn
            except Exception as e:
                app.logger.error(f"Failed to initialize Cloud SQL connector: {e}")
                raise

            app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+pg8000://"
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                "creator": getconn
            }
        # --- End of Connector Logic ---

        db.init_app(app)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass  # Folder already exists

    # Assuming the database is already created, we can create tables
    """
    with app.app_context():
        db.create_all()
        # Create the admin user if it doesn't exist
        admin_user = User.query.filter_by(role=UserRole.ADMIN).first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email=os.getenv('DB_EMAIL', 'admin@panelmerge.local'),
                password_hash=generate_password_hash(os.getenv('DB_PASS', 'Admin123!')),
                first_name='Admin',
                last_name='User',
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
            )
            db.session.add(admin_user)
            db.session.commit()
        else:
            app.logger.info("Admin user already exists, skipping creation.")
        app.logger.info("Database initialized and admin user created if needed.")
        return db
    """
