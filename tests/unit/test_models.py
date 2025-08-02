"""
Unit tests for database models
"""
import pytest
import datetime
from datetime import timedelta
from app.models import User, AdminMessage, AuditLog, Visit, PanelDownload, UserRole, db

@pytest.mark.unit
@pytest.mark.database
class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, db_session):
        """Test creating a new user."""
        user = User(
            username='newuser',
            email='new@example.com',
            role=UserRole.USER
        )
        user.set_password('password123')
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.role == UserRole.USER
        assert user.check_password('password123')
        assert not user.check_password('wrongpassword')
    
    def test_user_password_hashing(self, db_session):
        """Test password hashing and verification."""
        user = User(username='testuser', email='test@example.com')
        user.set_password('mypassword')
        
        # Password should be hashed
        assert user.password_hash != 'mypassword'
        assert user.check_password('mypassword')
        assert not user.check_password('wrongpassword')
    
    def test_user_repr(self, sample_user):
        """Test user string representation."""
        assert repr(sample_user) == '<User testuser>'
    
    def test_user_is_admin(self, db_session):
        """Test admin role checking."""
        regular_user = User(username='user', email='user@example.com', role=UserRole.USER)
        admin_user = User(username='admin', email='admin@example.com', role=UserRole.ADMIN)
        
        assert not regular_user.is_admin()
        assert admin_user.is_admin()
    
    def test_unique_username_constraint(self, db_session, sample_user):
        """Test username uniqueness constraint."""
        duplicate_user = User(
            username='testuser',  # Same as sample_user
            email='different@example.com'
        )
        
        db_session.add(duplicate_user)
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()
    
    def test_unique_email_constraint(self, db_session, sample_user):
        """Test email uniqueness constraint."""
        duplicate_user = User(
            username='differentuser',
            email='test@example.com'  # Same as sample_user
        )
        
        db_session.add(duplicate_user)
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()


@pytest.mark.unit
@pytest.mark.database
class TestVisitModel:
    """Test Visit model functionality."""
    
    def test_visit_creation(self, db_session):
        """Test creating a new visit."""
        visit = Visit(
            ip_address='192.168.1.1',
            visit_date=datetime.datetime.now(),
            path='/test',
            user_agent='Test Browser'
        )
        
        db_session.add(visit)
        db_session.commit()
        
        assert visit.id is not None
        assert visit.ip_address == '192.168.1.1'
        assert visit.user_agent == 'Test Browser'
        assert visit.visit_date is not None
        assert visit.path == '/test'


@pytest.mark.unit
@pytest.mark.database
class TestPanelDownloadModel:
    """Test PanelDownload model functionality."""
    
    def test_panel_download_creation(self, db_session, sample_user):
        """Test creating a new panel download record."""
        download = PanelDownload(
            user_id=sample_user.id,
            ip_address='192.168.1.1',
            download_date=datetime.datetime.now(),
            panel_ids='1,2,3',
            list_types='standard,research',
            gene_count=150
        )
        
        db_session.add(download)
        db_session.commit()
        
        assert download.id is not None
        assert download.user_id == sample_user.id
        assert download.ip_address == '192.168.1.1'
        assert download.panel_ids == '1,2,3'
        assert download.list_types == 'standard,research'
        assert download.gene_count == 150
        assert download.download_date is not None


@pytest.mark.unit
@pytest.mark.database
class TestAuditLogModel:
    """Test AuditLog model functionality."""
    
    def test_audit_log_creation(self, db_session, sample_user):
        """Test creating a new audit log entry."""
        from app.models import AuditActionType
        
        audit_log = AuditLog(
            user_id=sample_user.id,
            username=sample_user.username,
            action_type=AuditActionType.LOGIN,
            action_description='User logged in successfully',
            ip_address='192.168.1.1',
            user_agent='Test Browser',
            resource_type='auth',
            resource_id=str(sample_user.id),
            details={'ip': '192.168.1.1'}
        )
        
        db_session.add(audit_log)
        db_session.commit()
        
        assert audit_log.id is not None
        assert audit_log.user_id == sample_user.id
        assert audit_log.username == sample_user.username
        assert audit_log.action_type == AuditActionType.LOGIN
        assert audit_log.action_description == 'User logged in successfully'
        assert audit_log.ip_address == '192.168.1.1'
        assert audit_log.user_agent == 'Test Browser'
        assert audit_log.resource_type == 'auth'
        assert audit_log.timestamp is not None


@pytest.mark.unit
@pytest.mark.database
class TestAdminMessageModel:
    """Test AdminMessage model functionality."""
    
    def test_admin_message_creation(self, db_session, admin_user):
        """Test creating a new admin message."""
        expires_at = datetime.datetime.now() + timedelta(days=7)
        message = AdminMessage(
            title='System Maintenance',
            message='The system will be down for maintenance.',
            message_type='warning',
            created_by_id=admin_user.id,
            expires_at=expires_at
        )
        
        db_session.add(message)
        db_session.commit()
        
        assert message.id is not None
        assert message.title == 'System Maintenance'
        assert message.message == 'The system will be down for maintenance.'
        assert message.message_type == 'warning'
        assert message.created_by_id == admin_user.id
        assert message.expires_at == expires_at
        assert message.is_active is True
        assert message.created_at is not None
    
    def test_admin_message_repr(self, sample_admin_message):
        """Test admin message string representation."""
        assert repr(sample_admin_message) == f'<AdminMessage {sample_admin_message.id}: {sample_admin_message.title}>'
    
    def test_admin_message_is_expired(self, db_session, admin_user):
        """Test message expiration checking."""
        from unittest.mock import patch
        
        # Create expired message
        expired_message = AdminMessage(
            title='Expired Message',
            message='This message has expired.',
            message_type='info',
            created_by_id=admin_user.id,
            expires_at=datetime.datetime.now() - timedelta(days=1)
        )
        
        # Create active message
        active_message = AdminMessage(
            title='Active Message',
            message='This message is still active.',
            message_type='info',
            created_by_id=admin_user.id,
            expires_at=datetime.datetime.now() + timedelta(days=1)
        )
        
        db_session.add_all([expired_message, active_message])
        db_session.commit()
        
        # Mock datetime.datetime.now() to return timezone-naive datetime
        with patch('app.models.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = datetime.datetime.now()
            assert expired_message.is_expired()
            assert not active_message.is_expired()
    
    def test_get_active_messages(self, db_session, admin_user):
        """Test getting active messages."""
        from unittest.mock import patch
        
        # Create mix of active and expired messages
        active_msg = AdminMessage(
            title='Active',
            message='Active message',
            message_type='info',
            created_by_id=admin_user.id,
            expires_at=datetime.datetime.now() + timedelta(days=1),
            is_active=True
        )
        
        expired_msg = AdminMessage(
            title='Expired',
            message='Expired message',
            message_type='info',
            created_by_id=admin_user.id,
            expires_at=datetime.datetime.now() - timedelta(days=1),
            is_active=True
        )
        
        inactive_msg = AdminMessage(
            title='Inactive',
            message='Inactive message',
            message_type='info',
            created_by_id=admin_user.id,
            expires_at=datetime.datetime.now() + timedelta(days=1),
            is_active=False
        )
        
        db_session.add_all([active_msg, expired_msg, inactive_msg])
        db_session.commit()
        
        # Mock datetime.datetime.now() to return timezone-naive datetime
        with patch('app.models.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = datetime.datetime.now()
            mock_datetime.or_ = db.or_  # Keep SQLAlchemy's or_ function
            
            active_messages = AdminMessage.get_active_messages()
            
            assert len(active_messages) == 1
            assert active_messages[0] == active_msg
    
    def test_admin_message_creator_relationship(self, sample_admin_message, admin_user):
        """Test admin message creator relationship."""
        assert sample_admin_message.created_by == admin_user
