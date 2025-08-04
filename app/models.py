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
    PANEL_CREATE = "PANEL_CREATE"
    PANEL_UPDATE = "PANEL_UPDATE"
    PANEL_SHARE = "PANEL_SHARE"
    PANEL_LIST = "PANEL_LIST"
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
    
    def create_new_version(self, user_id, comment=None):
        """Create a new version of this panel"""
        latest = self.get_latest_version()
        new_version_number = (latest.version_number + 1) if latest else 1
        
        new_version = PanelVersion(
            panel_id=self.id,
            version_number=new_version_number,
            created_by_id=user_id,
            comment=comment or f"Version {new_version_number}",
            gene_count=self.gene_count
        )
        
        db.session.add(new_version)
        db.session.flush()  # Get the ID
        
        # Update panel reference
        self.current_version_id = new_version.id
        self.version_count = new_version_number
        self.updated_at = datetime.datetime.now()
        
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
    
    # Relationships
    changes = db.relationship('PanelChange', backref='version', lazy='dynamic', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('panel_id', 'version_number', name='uq_panel_version'),
        db.Index('idx_panel_versions_panel_version', 'panel_id', 'version_number'),
        db.Index('idx_panel_versions_created', 'created_at'),
    )
    
    def __repr__(self):
        return f'<PanelVersion {self.panel_id}v{self.version_number}>'
    
    def to_dict(self):
        """Convert version to dictionary"""
        return {
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
        }

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
