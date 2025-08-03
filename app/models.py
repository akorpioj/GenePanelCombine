import os
import datetime
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
    
    # Additional security fields
    last_ip_address = db.Column(db.String(45))
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    
    # User preferences
    timezone_preference = db.Column(db.String(50), default='UTC')  # IANA timezone name
    
    # Relationship to track user downloads
    downloads = db.relationship('PanelDownload', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
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

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 can be up to 45 chars
    visit_date = db.Column(db.DateTime, nullable=False)
    path = db.Column(db.String(255), nullable=False)
    user_agent = db.Column(db.String(255))

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
        db_pass = os.getenv("DB_PASS")

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
