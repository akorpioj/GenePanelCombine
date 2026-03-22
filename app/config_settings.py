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
    
    # Account Lockout Configuration
    ACCOUNT_LOCKOUT_THRESHOLD = int(os.getenv('ACCOUNT_LOCKOUT_THRESHOLD', '5'))  # Failed attempts before lockout
    ACCOUNT_LOCKOUT_DURATION = int(os.getenv('ACCOUNT_LOCKOUT_DURATION', '24'))  # Hours to lock account
    
    # Suspicious Activity Detection Configuration
    SUSPICIOUS_ACTIVITY_ENABLED = os.getenv('SUSPICIOUS_ACTIVITY_ENABLED', 'True').lower() == 'true'
    SUSPICIOUS_ACTIVITY_ATTEMPTS_THRESHOLD = int(os.getenv('SUSPICIOUS_ACTIVITY_ATTEMPTS_THRESHOLD', '5'))  # Attempts before alert
    SUSPICIOUS_ACTIVITY_TIME_WINDOW = int(os.getenv('SUSPICIOUS_ACTIVITY_TIME_WINDOW', '1'))  # Hours for multiple attempt detection
    SUSPICIOUS_ACTIVITY_RETENTION_DAYS = int(os.getenv('SUSPICIOUS_ACTIVITY_RETENTION_DAYS', '90'))  # Days to keep records
    
    # ML-based Anomaly Detection Configuration
    ML_ANOMALY_DETECTION_ENABLED = os.getenv('ML_ANOMALY_DETECTION_ENABLED', 'False').lower() == 'true'
    ML_ANOMALY_CONTAMINATION = float(os.getenv('ML_ANOMALY_CONTAMINATION', '0.1'))  # Expected proportion of anomalies (0.05-0.15)
    
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
    
    # Only set GOOGLE_APPLICATION_CREDENTIALS if the file exists
    # This allows fallback to user authentication for development
    gcs_key_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'gcs_credentials/gcs-service-account-key.json')
    if os.path.exists(gcs_key_path):
        GOOGLE_APPLICATION_CREDENTIALS = gcs_key_path
    else:
        GOOGLE_APPLICATION_CREDENTIALS = None  # Use default authentication (user credentials)
    
    # Storage Backend Configuration
    PRIMARY_STORAGE_BACKEND = os.getenv('PRIMARY_STORAGE_BACKEND', 'gcs')  # 'gcs' or 'local'
    BACKUP_STORAGE_BACKEND = os.getenv('BACKUP_STORAGE_BACKEND', 'local')  # 'local' for redundancy
    LOCAL_STORAGE_PATH = os.getenv('LOCAL_STORAGE_PATH', 'instance/saved_panels')
    
    # Panel Storage Configuration
    MAX_PANEL_VERSIONS = int(os.getenv('MAX_PANEL_VERSIONS', '10'))  # Keep last 10 versions
    AUTO_BACKUP_ENABLED = os.getenv('AUTO_BACKUP_ENABLED', 'True').lower() == 'true'
    BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '90'))  # Keep backups for 90 days
    
    # Version Control Configuration
    VERSION_CONTROL_ENABLED = os.getenv('VERSION_CONTROL_ENABLED', 'True').lower() == 'true'
    VERSION_CONTROL_BRANCH_ENABLED = os.getenv('VERSION_CONTROL_BRANCH_ENABLED', 'True').lower() == 'true'
    VERSION_CONTROL_TAG_ENABLED = os.getenv('VERSION_CONTROL_TAG_ENABLED', 'True').lower() == 'true'
    VERSION_CONTROL_MERGE_ENABLED = os.getenv('VERSION_CONTROL_MERGE_ENABLED', 'True').lower() == 'true'
    
    # Retention Policy Configuration
    DEFAULT_RETENTION_POLICY = {
        'max_versions': int(os.getenv('DEFAULT_MAX_VERSIONS', '10')),
        'backup_retention_days': int(os.getenv('DEFAULT_BACKUP_RETENTION_DAYS', '90')),
        'keep_tagged_versions': os.getenv('DEFAULT_KEEP_TAGGED_VERSIONS', 'True').lower() == 'true',
        'keep_production_tags': os.getenv('DEFAULT_KEEP_PRODUCTION_TAGS', 'True').lower() == 'true',
        'auto_cleanup_enabled': os.getenv('DEFAULT_AUTO_CLEANUP_ENABLED', 'True').lower() == 'true',
        'cleanup_frequency_hours': int(os.getenv('DEFAULT_CLEANUP_FREQUENCY_HOURS', '24'))
    }
    
    # Tag Protection Configuration
    PROTECTED_TAG_TYPES = os.getenv('PROTECTED_TAG_TYPES', 'PRODUCTION,STAGING').split(',')
    TAG_NAMING_PATTERN = os.getenv('TAG_NAMING_PATTERN', r'^[a-zA-Z0-9._-]+$')  # Regex pattern for tag names
    
    # Branch Configuration
    DEFAULT_BRANCH_NAME = os.getenv('DEFAULT_BRANCH_NAME', 'main')
    BRANCH_NAMING_PATTERN = os.getenv('BRANCH_NAMING_PATTERN', r'^[a-zA-Z0-9._/-]+$')  # Regex pattern for branch names
    MAX_BRANCHES_PER_PANEL = int(os.getenv('MAX_BRANCHES_PER_PANEL', '20'))
    
    # Merge Configuration
    DEFAULT_MERGE_STRATEGY = os.getenv('DEFAULT_MERGE_STRATEGY', 'auto')  # auto, manual, ours, theirs
    ALLOW_FAST_FORWARD_MERGE = os.getenv('ALLOW_FAST_FORWARD_MERGE', 'True').lower() == 'true'
    REQUIRE_MERGE_COMMENT = os.getenv('REQUIRE_MERGE_COMMENT', 'True').lower() == 'true'

    # PubMed Configuration
    PUBMED_EMAIL = os.getenv('PUBMED_EMAIL', 'default@example.com')
    PUBMED_API_KEY = os.getenv('PUBMED_API_KEY', None)
    PUBMED_TOOL_NAME = os.getenv('PUBMED_TOOL_NAME', 'PanelMerge-LitReview')
    PUBMED_MAX_RESULTS = int(os.getenv('PUBMED_MAX_RESULTS', 200))

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
    # Disable Cloud SQL for testing
    CLOUD_SQL_CONNECTION_NAME = None
    # Disable encryption for testing
    ENCRYPT_SENSITIVE_FIELDS = False

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
