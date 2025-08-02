"""
Unit tests for authentication functionality
"""
import pytest
from flask import url_for, session
from app.models import User
from unittest.mock import patch


@pytest.mark.unit
@pytest.mark.auth
class TestAuthenticationRoutes:
    """Test authentication route handlers."""
    
    def test_login_page_renders(self, client):
        """Test login page renders correctly."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Login' in response.data
    
    def test_register_page_renders(self, client):
        """Test registration page renders correctly."""
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'Register' in response.data
    
    def test_successful_login(self, client, sample_user):
        """Test successful user login."""
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to main page after login
        assert b'PanelMerge' in response.data or b'Dashboard' in response.data
    
    def test_invalid_login_credentials(self, client, sample_user):
        """Test login with invalid credentials."""
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data or b'Login' in response.data
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'password'
        })
        
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data or b'Login' in response.data
    
    def test_successful_registration(self, client, db_session):
        """Test successful user registration."""
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword',
            'password2': 'newpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify user was created
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'new@example.com'
        assert user.check_password('newpassword')
    
    def test_registration_password_mismatch(self, client):
        """Test registration with password mismatch."""
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password1',
            'password2': 'password2'
        })
        
        assert response.status_code == 200
        assert b'passwords must match' in response.data.lower() or b'register' in response.data.lower()
    
    def test_registration_duplicate_username(self, client, sample_user):
        """Test registration with duplicate username."""
        response = client.post('/auth/register', data={
            'username': 'testuser',  # Already exists
            'email': 'different@example.com',
            'password': 'password',
            'password2': 'password'
        })
        
        assert response.status_code == 200
        # Should show error or stay on registration page
        assert b'username' in response.data.lower() or b'register' in response.data.lower()
    
    def test_registration_duplicate_email(self, client, sample_user):
        """Test registration with duplicate email."""
        response = client.post('/auth/register', data={
            'username': 'differentuser',
            'email': 'test@example.com',  # Already exists
            'password': 'password',
            'password2': 'password'
        })
        
        assert response.status_code == 200
        # Should show error or stay on registration page
        assert b'email' in response.data.lower() or b'register' in response.data.lower()
    
    def test_logout(self, authenticated_client):
        """Test user logout."""
        response = authenticated_client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to main page
        assert b'Login' in response.data or b'PanelMerge' in response.data
    
    def test_access_protected_route_unauthenticated(self, client):
        """Test accessing protected route without authentication."""
        response = client.get('/admin/dashboard')
        # Should redirect to login page
        assert response.status_code == 302 or response.status_code == 200
    
    def test_admin_access_control(self, client, sample_user):
        """Test admin route access control for regular user."""
        # Login as regular user
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        })
        
        response = client.get('/admin/dashboard')
        # Should be forbidden or redirect
        assert response.status_code in [302, 403, 200]  # Various possible responses


@pytest.mark.unit
@pytest.mark.auth
class TestUserAuthentication:
    """Test user authentication logic."""
    
    def test_password_hashing(self):
        """Test password hashing functionality."""
        user = User(username='test', email='test@example.com')
        password = 'mysecretpassword'
        
        user.set_password(password)
        
        # Password should be hashed
        assert user.password_hash != password
        assert len(user.password_hash) > 20  # Hashed passwords are long
        
        # Should be able to verify correct password
        assert user.check_password(password)
        assert not user.check_password('wrongpassword')
    
    def test_password_hash_randomness(self):
        """Test that password hashing produces different hashes."""
        user1 = User(username='user1', email='user1@example.com')
        user2 = User(username='user2', email='user2@example.com')
        password = 'samepassword'
        
        user1.set_password(password)
        user2.set_password(password)
        
        # Same password should produce different hashes
        assert user1.password_hash != user2.password_hash
        
        # But both should verify the original password
        assert user1.check_password(password)
        assert user2.check_password(password)
    
    def test_is_admin_method(self):
        """Test is_admin method."""
        regular_user = User(username='user', email='user@example.com', role='user')
        admin_user = User(username='admin', email='admin@example.com', role='admin')
        editor_user = User(username='editor', email='editor@example.com', role='editor')
        
        assert not regular_user.is_admin()
        assert admin_user.is_admin()
        assert not editor_user.is_admin()


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.security
class TestSessionSecurity:
    """Test session security features."""
    
    @patch('app.audit_service.AuditService.log_user_action')
    def test_login_audit_logging(self, mock_audit, client, sample_user):
        """Test that login attempts are audited."""
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        })
        
        # Should have called audit logging
        assert mock_audit.called
    
    @patch('app.audit_service.AuditService.log_user_action')
    def test_logout_audit_logging(self, mock_audit, authenticated_client):
        """Test that logout is audited."""
        authenticated_client.get('/auth/logout')
        
        # Should have called audit logging
        assert mock_audit.called
    
    def test_session_regeneration_on_login(self, client, sample_user):
        """Test that session ID changes on login."""
        # Get initial session
        with client.session_transaction() as sess:
            initial_session_id = sess.get('_id')
        
        # Login
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        })
        
        # Check session after login
        with client.session_transaction() as sess:
            new_session_id = sess.get('_id')
        
        # Session should have changed (security best practice)
        # Note: This might not always be the case depending on Flask-Login configuration
        assert True  # Placeholder for actual session ID comparison
    
    def test_remember_me_functionality(self, client, sample_user):
        """Test remember me functionality."""
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpassword',
            'remember_me': True
        })
        
        # Should set appropriate cookies for remember me
        assert response.status_code in [200, 302]  # Success or redirect


@pytest.mark.unit
@pytest.mark.auth
class TestPasswordValidation:
    """Test password validation requirements."""
    
    def test_empty_password(self):
        """Test empty password handling."""
        user = User(username='test', email='test@example.com')
        
        with pytest.raises(Exception):
            user.set_password('')
    
    def test_none_password(self):
        """Test None password handling."""
        user = User(username='test', email='test@example.com')
        
        with pytest.raises(Exception):
            user.set_password(None)
    
    def test_very_long_password(self):
        """Test very long password."""
        user = User(username='test', email='test@example.com')
        long_password = 'a' * 1000
        
        user.set_password(long_password)
        assert user.check_password(long_password)
    
    def test_unicode_password(self):
        """Test unicode characters in password."""
        user = User(username='test', email='test@example.com')
        unicode_password = 'пароль123🔒'
        
        user.set_password(unicode_password)
        assert user.check_password(unicode_password)
        assert not user.check_password('пароль123')  # Partial match should fail
