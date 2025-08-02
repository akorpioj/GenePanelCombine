"""
Pytest configuration and shared fixtures for PanelMerge tests
"""
import os
import tempfile
import pytest
from unittest.mock import Mock, patch
from flask import Flask
from app import create_app
from app.models import db, User, AdminMessage, AuditLog, Visit, PanelDownload, UserRole
from app.extensions import cache
import redis


@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    # Set environment variables to force test mode
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'True'
    
    # Create a temporary file to serve as the database
    db_fd, db_path = tempfile.mkstemp()
    
    # Create app with testing configuration
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'REDIS_URL': 'redis://localhost:6379/15',  # Use test DB
        'CACHE_TYPE': 'SimpleCache',  # Use simple cache for testing
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'DATABASE_URL': f'sqlite:///{db_path}',  # Override any production DB
    })
    
    # Establish an application context
    with app.app_context():
        db.create_all()
        yield app
        
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def db_session(app):
    """Create a database session for testing."""
    with app.app_context():
        # Clear all data
        db.session.remove()
        db.drop_all()
        db.create_all()
        yield db.session
        db.session.remove()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        username='testuser',
        email='test@example.com',
        role=UserRole.USER
    )
    user.set_password('testpassword')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    admin = User(
        username='admin',
        email='admin@example.com',
        role=UserRole.ADMIN
    )
    admin.set_password('adminpassword')
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture
def authenticated_client(client, sample_user):
    """Client with authenticated user."""
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    }, follow_redirects=True)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Client with authenticated admin user."""
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'adminpassword'
    }, follow_redirects=True)
    return client


@pytest.fixture
def sample_panel():
    """Create a sample panel for testing (mock data)."""
    return {
        'panel_id': 1,
        'name': 'Test Panel',
        'version': '1.0',
        'description': 'A test panel',
        'gene_count': 5,
        'genes': ['BRCA1', 'TP53', 'EGFR', 'KRAS', 'APC']
    }


@pytest.fixture
def sample_gene():
    """Create a sample gene for testing (mock data)."""
    return {
        'gene_symbol': 'BRCA1',
        'gene_name': 'BRCA1 DNA Repair Associated',
        'panel_id': 1
    }


@pytest.fixture
def sample_admin_message(db_session, admin_user):
    """Create a sample admin message for testing."""
    import datetime
    
    message = AdminMessage(
        title='Test Message',
        message='This is a test message',
        message_type='info',
        created_by_id=admin_user.id,
        expires_at=datetime.datetime.now() + datetime.timedelta(days=7)
    )
    db_session.add(message)
    db_session.commit()
    return message


@pytest.fixture
def mock_redis():
    """Mock Redis connection for testing."""
    with patch('redis.Redis') as mock_redis_class:
        mock_redis_instance = Mock()
        mock_redis_class.return_value = mock_redis_instance
        yield mock_redis_instance


@pytest.fixture
def mock_cache():
    """Mock cache for testing."""
    with patch.object(cache, 'get') as mock_get, \
         patch.object(cache, 'set') as mock_set, \
         patch.object(cache, 'delete') as mock_delete:
        yield {
            'get': mock_get,
            'set': mock_set,
            'delete': mock_delete
        }


@pytest.fixture
def sample_file_data():
    """Sample file data for upload testing."""
    return {
        'valid_csv': 'Gene Symbol,Gene Name\nBRCA1,BRCA1 DNA Repair Associated\nTP53,Tumor Protein P53',
        'invalid_csv': 'Invalid,Data\nWithout,Headers',
        'valid_excel_data': [
            ['Gene Symbol', 'Gene Name'],
            ['BRCA1', 'BRCA1 DNA Repair Associated'],
            ['TP53', 'Tumor Protein P53']
        ]
    }


@pytest.fixture
def api_headers():
    """Common headers for API testing."""
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }


@pytest.fixture
def jwt_token(client, sample_user):
    """Generate JWT token for API authentication."""
    response = client.post('/api/v1/auth/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    if response.status_code == 200:
        return response.json.get('access_token')
    return None


@pytest.fixture
def auth_headers(api_headers, jwt_token):
    """Headers with JWT authentication."""
    headers = api_headers.copy()
    if jwt_token:
        headers['Authorization'] = f'Bearer {jwt_token}'
    return headers


# Custom markers for test organization
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.api = pytest.mark.api
pytest.mark.auth = pytest.mark.auth
pytest.mark.database = pytest.mark.database
pytest.mark.cache = pytest.mark.cache
pytest.mark.security = pytest.mark.security
pytest.mark.slow = pytest.mark.slow
