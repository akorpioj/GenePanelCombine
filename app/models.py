import os
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from enum import Enum
# Import the Cloud SQL Python Connector library
from google.cloud.sql.connector import Connector, IPTypes

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
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    organization = db.Column(db.String(100))
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    
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

class PanelDownload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Optional for anonymous users
    ip_address = db.Column(db.String(45), nullable=False)
    download_date = db.Column(db.DateTime, nullable=False)
    panel_ids = db.Column(db.String(255), nullable=False)  # Comma-separated list of panel IDs
    list_types = db.Column(db.String(255), nullable=False)  # Comma-separated list of list types
    gene_count = db.Column(db.Integer)  # Number of genes in the downloaded list

def db_init(app):
    """
    Initializes a connection pool for a Cloud SQL instance of Postgres
    using the Cloud SQL Python Connector. The application is configured to use
    this pool for all database operations.
    """# These variables are set in the Cloud Run environment.
    db_pass = os.getenv("DB_PASS")                  # e.g. 'my-db-password'

    # --- Cloud SQL Python Connector Initialization ---   
    if app.config["CLOUD_SQL_CONNECTION_NAME"]:
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
