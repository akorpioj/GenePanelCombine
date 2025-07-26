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
