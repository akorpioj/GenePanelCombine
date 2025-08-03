import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# Do this before defining Config class
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path, override=True)

class Config:
    """Base configuration class. Contains default settings and settings common to
    all environments."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY') or 'a_very_complex_and_unguessable_default_secret_key'
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security Configuration
    REQUIRE_HTTPS = os.getenv('REQUIRE_HTTPS', 'False').lower() == 'true'
    HSTS_MAX_AGE = int(os.getenv('HSTS_MAX_AGE', '31536000'))  # 1 year
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '3600'))  # 1 hour
    
    # Enhanced Session Configuration
    MAX_CONCURRENT_SESSIONS = int(os.getenv('MAX_CONCURRENT_SESSIONS', '5'))
    SESSION_ROTATION_INTERVAL = int(os.getenv('SESSION_ROTATION_INTERVAL', '1800'))  # 30 minutes
    ENABLE_SESSION_ANALYTICS = os.getenv('ENABLE_SESSION_ANALYTICS', 'True').lower() == 'true'
    
    # Encryption Configuration
    ENCRYPTION_MASTER_KEY = os.getenv('ENCRYPTION_MASTER_KEY')
    ENCRYPT_SENSITIVE_FIELDS = os.getenv('ENCRYPT_SENSITIVE_FIELDS', 'True').lower() == 'true'
    
    # Cloud SQL Configuration
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    DB_EMAIL = os.getenv("DB_EMAIL")
    DB_NAME = os.getenv("DB_NAME")
    DB_HOST = os.getenv("DB_HOST")
    CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")
    INSTANCE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
    
    # Redis Cache Configuration
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = os.getenv('REDIS_URL')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 3600))
    CACHE_PANEL_TIMEOUT = int(os.getenv('CACHE_PANEL_TIMEOUT', 1800))
    CACHE_GENE_TIMEOUT = int(os.getenv('CACHE_GENE_TIMEOUT', 86400))
    
    # Google Cloud Storage Configuration
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT', 'gene-panel-combine')
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'gcs-service-account-key.json')
    
    # Storage Backend Configuration
    PRIMARY_STORAGE_BACKEND = os.getenv('PRIMARY_STORAGE_BACKEND', 'gcs')  # 'gcs' or 'local'
    BACKUP_STORAGE_BACKEND = os.getenv('BACKUP_STORAGE_BACKEND', 'local')  # 'local' for redundancy
    LOCAL_STORAGE_PATH = os.getenv('LOCAL_STORAGE_PATH', 'instance/saved_panels')
    
    # Panel Storage Configuration
    MAX_PANEL_VERSIONS = int(os.getenv('MAX_PANEL_VERSIONS', '10'))  # Keep last 10 versions
    AUTO_BACKUP_ENABLED = os.getenv('AUTO_BACKUP_ENABLED', 'True').lower() == 'true'
    BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '90'))  # Keep backups for 90 days

# Add other application-wide configurations here
class DevelopmentConfig(Config):
    DEBUG = True
    # Use SQLite for local development with absolute path
    DB_FILE = os.path.join(Config.INSTANCE_PATH, 'gene_panel.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_FILE}'
    # CLOUD_SQL_CONNECTION_NAME = None
    # Original PostgreSQL config commented out for reference
    #DB_PORT = 5433  # Match the port in start_cloud_sql_proxy.ps1
    #SQLALCHEMY_DATABASE_URI = f'postgresql://{Config.DB_USER}:{Config.DB_PASS}@localhost:{DB_PORT}/{Config.DB_NAME}'
    
    # Disable HTTPS enforcement in development
    REQUIRE_HTTPS = False
    HSTS_MAX_AGE = 0  # Disable HSTS in development

# Add any development-specific settings, e.g., MAIL_SUPPRESS_SEND = True
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use an in-memory SQLite database for tests
    WTF_CSRF_ENABLED = False # Often useful to disable CSRF for simpler form testing
    SECRET_KEY = 'test_secret_key' # Consistent key for testing
    # Use simple cache for testing
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # SQLALCHEMY_DATABASE_URI will be configured dynamically at app startup
    # using the Cloud SQL Python Connector, so we can leave it as None here.
    SQLALCHEMY_DATABASE_URI = None # Set in models.py
    CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME", "gene-panel-combine:europe-north1:gene-panel-user-db") # e.g. 'project:region:instance'
    
    # Production Security Settings
    REQUIRE_HTTPS = True
    HSTS_MAX_AGE = 31536000  # 1 year
    SESSION_TIMEOUT = 1800   # 30 minutes for production
    ENCRYPT_SENSITIVE_FIELDS = True
    
    # Production Session Settings
    MAX_CONCURRENT_SESSIONS = 3  # Stricter in production
    SESSION_ROTATION_INTERVAL = 900  # 15 minutes in production
    ENABLE_SESSION_ANALYTICS = True
