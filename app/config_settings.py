import os
from dotenv import load_dotenv #Development only, for local .env file support

class Config:
    """Base configuration class. Contains default settings and settings common to
    all environments."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_complex_and_unguessable_default_secret_key'
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Cloud SQL Configuration
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    DB_NAME = os.getenv("DB_NAME")
    DB_HOST = os.getenv("DB_HOST")
    CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")    

# Add other application-wide configurations here
class DevelopmentConfig(Config):
    DEBUG = True
    # Load environment variables from .env file if it exists
    load_dotenv()
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '../instance/user.db')

# Add any development-specific settings, e.g., MAIL_SUPPRESS_SEND = True
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use an in-memory SQLite database for tests
    WTF_CSRF_ENABLED = False # Often useful to disable CSRF for simpler form testing
    SECRET_KEY = 'test_secret_key' # Consistent key for testing

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # In production, SECRET_KEY and DATABASE_URL MUST be set via environment variables or instance/config.py
    # Add any production-specific settings here, e.g., enabling more robust logging
    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{Config.DB_USER}:{Config.DB_PASS}@{Config.DB_HOST}/{Config.DB_NAME}'
        if Config.DB_HOST != 'localhost'
        else f'postgresql://{Config.DB_USER}:{Config.DB_PASS}@/{Config.DB_NAME}'
        f'?host=/cloudsql/{Config.CLOUD_SQL_CONNECTION_NAME}'
    )
