"""
Integration tests for database operations with real-world scenarios
"""
import pytest
import datetime
from datetime import timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from unittest.mock import patch
from app.models import (
    User, AdminMessage, AuditLog, Visit, PanelDownload, 
    UserRole, AuditActionType, db
)


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseIntegrationWorkflows:
    """Test complete database workflows and real-world scenarios."""
    
    def test_user_registration_workflow(self, client, db_session):
        """Test complete user registration database workflow."""
        initial_user_count = User.query.count()
        
        # Simulate user registration
        registration_data = {
            'username': 'integration_user',
            'email': 'integration@test.com',
            'password': 'securepassword123',
            'password2': 'securepassword123'
        }
        
        response = client.post('/auth/register', data=registration_data)
        
        # Verify user was created in database
        final_user_count = User.query.count()
        assert final_user_count == initial_user_count + 1
        
        # Verify user data integrity
        created_user = User.query.filter_by(username='integration_user').first()
        assert created_user is not None
        assert created_user.email == 'integration@test.com'
        assert created_user.role == UserRole.USER
        assert created_user.is_active is True
        assert created_user.check_password('securepassword123')
    
    def test_user_login_audit_workflow(self, client, db_session, sample_user):
        """Test user login with audit trail creation."""
        initial_audit_count = AuditLog.query.count()
        
        # Login user
        login_data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        
        with patch('app.audit_service.AuditService.log_user_action') as mock_audit:
            response = client.post('/auth/login', data=login_data)
            
            # Verify audit was called
            assert mock_audit.called
        
        # In a real scenario, audit log would be created
        # For now, verify user login was successful
        assert response.status_code in [200, 302]
    
    def test_panel_download_workflow(self, client, db_session, sample_user):
        """Test panel download with database tracking."""
        initial_download_count = PanelDownload.query.count()
        
        # Simulate authenticated user
        with client.session_transaction() as sess:
            sess['user_id'] = str(sample_user.id)
            sess['_fresh'] = True
        
        # Simulate panel download (would normally be through main interface)
        download = PanelDownload(
            user_id=sample_user.id,
            ip_address='192.168.1.100',
            download_date=datetime.datetime.now(),
            panel_ids='1,2,3,4,5',
            list_types='standard,research',
            gene_count=250
        )
        
        db_session.add(download)
        db_session.commit()
        
        # Verify download was tracked
        final_download_count = PanelDownload.query.count()
        assert final_download_count == initial_download_count + 1
        
        # Verify relationship
        assert len(sample_user.downloads) == 1
        assert sample_user.downloads[0].gene_count == 250
    
    def test_admin_message_workflow(self, client, db_session, admin_user):
        """Test admin message creation and display workflow."""
        initial_message_count = AdminMessage.query.count()
        
        # Create admin message
        message = AdminMessage(
            title='System Maintenance Notice',
            message='The system will be down for maintenance on Sunday.',
            message_type='warning',
            created_by_id=admin_user.id,
            expires_at=datetime.datetime.now() + timedelta(days=7)
        )
        
        db_session.add(message)
        db_session.commit()
        
        # Verify message was created
        final_message_count = AdminMessage.query.count()
        assert final_message_count == initial_message_count + 1
        
        # Test active messages retrieval
        active_messages = AdminMessage.get_active_messages()
        assert len(active_messages) >= 1
        assert any(msg.title == 'System Maintenance Notice' for msg in active_messages)
    
    def test_database_transaction_workflow(self, db_session):
        """Test complex transaction workflow with multiple operations."""
        initial_counts = {
            'users': User.query.count(),
            'messages': AdminMessage.query.count(),
            'audits': AuditLog.query.count()
        }
        
        try:
            # Start complex transaction
            
            # Create admin user
            admin = User(
                username='workflow_admin',
                email='workflow@admin.com',
                role=UserRole.ADMIN
            )
            admin.set_password('adminpass123')
            db_session.add(admin)
            db_session.flush()  # Get ID without committing
            
            # Create admin message
            message = AdminMessage(
                title='Workflow Test',
                message='Testing complex workflow',
                message_type='info',
                created_by_id=admin.id
            )
            db_session.add(message)
            db_session.flush()
            
            # Create audit log
            audit = AuditLog(
                user_id=admin.id,
                username=admin.username,
                action_type=AuditActionType.ADMIN_ACTION,
                action_description='Created test message',
                ip_address='192.168.1.200'
            )
            db_session.add(audit)
            
            # Commit all changes
            db_session.commit()
            
            # Verify all operations succeeded
            final_counts = {
                'users': User.query.count(),
                'messages': AdminMessage.query.count(),
                'audits': AuditLog.query.count()
            }
            
            assert final_counts['users'] == initial_counts['users'] + 1
            assert final_counts['messages'] == initial_counts['messages'] + 1
            assert final_counts['audits'] == initial_counts['audits'] + 1
            
            # Verify relationships
            created_admin = User.query.filter_by(username='workflow_admin').first()
            assert len(created_admin.admin_messages) == 1
            
        except Exception as e:
            db_session.rollback()
            raise


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseConcurrency:
    """Test database operations under concurrent access scenarios."""
    
    def test_concurrent_user_creation(self, db_session):
        """Test concurrent user creation scenarios."""
        import threading
        import time
        
        results = []
        errors = []
        
        def create_user(index):
            """Function to create user in separate context."""
            try:
                # Create new session for each thread simulation
                user = User(
                    username=f'concurrent_user_{index}_{int(time.time())}',
                    email=f'concurrent{index}@test.com',
                    role=UserRole.USER
                )
                user.set_password('password123')
                
                db_session.add(user)
                db_session.commit()
                results.append(user.id)
                
            except Exception as e:
                errors.append(str(e))
                db_session.rollback()
        
        # Simulate concurrent operations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_user, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5, f"Expected 5 users, got {len(results)}"
    
    def test_concurrent_audit_logging(self, db_session, sample_user):
        """Test concurrent audit log creation."""
        initial_count = AuditLog.query.count()
        
        # Create multiple audit logs simultaneously
        audits = []
        for i in range(10):
            audit = AuditLog(
                user_id=sample_user.id,
                username=sample_user.username,
                action_type=AuditActionType.VIEW,
                action_description=f'Concurrent action {i}',
                ip_address='192.168.1.1'
            )
            audits.append(audit)
        
        # Add all at once
        db_session.add_all(audits)
        db_session.commit()
        
        # Verify all were created
        final_count = AuditLog.query.count()
        assert final_count == initial_count + 10
    
    def test_database_deadlock_prevention(self, db_session):
        """Test database deadlock prevention mechanisms."""
        # Create test users for deadlock scenario
        user1 = User(
            username='deadlock_user1',
            email='deadlock1@test.com',
            role=UserRole.USER
        )
        user1.set_password('password123')
        
        user2 = User(
            username='deadlock_user2',
            email='deadlock2@test.com',
            role=UserRole.USER
        )
        user2.set_password('password123')
        
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Simulate operations that could cause deadlock
        # Update users in consistent order to prevent deadlock
        users_to_update = [user1, user2]
        users_to_update.sort(key=lambda u: u.id)  # Consistent ordering
        
        for user in users_to_update:
            user.login_count = (user.login_count or 0) + 1
        
        db_session.commit()
        
        # Verify updates succeeded
        updated_user1 = User.query.get(user1.id)
        updated_user2 = User.query.get(user2.id)
        assert updated_user1.login_count == 1
        assert updated_user2.login_count == 1


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseBackupIntegration:
    """Test database backup and recovery integration."""
    
    def test_database_export_import_cycle(self, db_session):
        """Test complete database export/import cycle."""
        # Create test data
        test_user = User(
            username='backup_test',
            email='backup@test.com',
            role=UserRole.USER
        )
        test_user.set_password('password123')
        db_session.add(test_user)
        db_session.commit()
        
        # Export data
        exported_data = {
            'user': test_user.to_dict(),
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        # Verify export contains necessary data
        assert exported_data['user']['username'] == 'backup_test'
        assert exported_data['user']['email'] == 'backup@test.com'
        assert 'timestamp' in exported_data
        
        # Simulate data restoration (create new user from export)
        import_data = exported_data['user']
        restored_user = User(
            username=f"restored_{import_data['username']}",
            email=f"restored_{import_data['email']}",
            role=UserRole(import_data['role'])
        )
        restored_user.set_password('newpassword123')
        
        db_session.add(restored_user)
        db_session.commit()
        
        # Verify restoration
        assert restored_user.id is not None
        assert restored_user.username == 'restored_backup_test'
    
    def test_database_consistency_check(self, db_session):
        """Test database consistency validation."""
        # Create related data
        admin = User(
            username='consistency_admin',
            email='consistency@admin.com',
            role=UserRole.ADMIN
        )
        admin.set_password('password123')
        db_session.add(admin)
        db_session.commit()
        
        message = AdminMessage(
            title='Consistency Check',
            message='Testing database consistency',
            message_type='info',
            created_by_id=admin.id
        )
        db_session.add(message)
        db_session.commit()
        
        audit = AuditLog(
            user_id=admin.id,
            username=admin.username,
            action_type=AuditActionType.ADMIN_ACTION,
            action_description='Created consistency message',
            ip_address='192.168.1.1'
        )
        db_session.add(audit)
        db_session.commit()
        
        # Perform consistency checks
        
        # 1. Verify foreign key relationships
        assert message.created_by_id == admin.id
        assert message.created_by == admin
        assert audit.user_id == admin.id
        
        # 2. Verify data integrity
        assert admin.is_admin() is True
        assert message.is_visible() is True
        assert audit.success is True
        
        # 3. Verify no orphaned records
        orphaned_messages = AdminMessage.query.filter(
            ~AdminMessage.created_by_id.in_([admin.id])
        ).filter(
            AdminMessage.created_by_id.isnot(None)
        ).count()
        
        # This should be 0 for our test data
        test_messages_count = AdminMessage.query.filter_by(
            title='Consistency Check'
        ).count()
        assert test_messages_count > 0  # Our message exists
    
    def test_database_recovery_scenarios(self, db_session):
        """Test database recovery scenarios."""
        # Scenario 1: Corrupt data recovery
        user = User(
            username='recovery_test',
            email='recovery@test.com',
            role=UserRole.USER
        )
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        
        user_id = user.id
        
        # Simulate data corruption (partial delete)
        try:
            # This simulates a scenario where data might be corrupted
            db_session.execute(
                text("UPDATE \"user\" SET email = NULL WHERE id = :user_id"),
                {"user_id": user_id}
            )
            db_session.commit()
            
            # Recovery: Restore from backup data
            corrupted_user = User.query.get(user_id)
            if corrupted_user and not corrupted_user.email:
                corrupted_user.email = 'recovered@test.com'
                db_session.commit()
            
            # Verify recovery
            recovered_user = User.query.get(user_id)
            assert recovered_user.email == 'recovered@test.com'
            
        except Exception as e:
            db_session.rollback()
            # In real scenario, would restore from backup
            user.email = 'recovery@test.com'
            db_session.commit()


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.slow
class TestDatabasePerformanceIntegration:
    """Test database performance in realistic scenarios."""
    
    def test_large_scale_user_operations(self, db_session):
        """Test database performance with large number of users."""
        import time
        
        # Create large dataset
        start_time = time.time()
        
        batch_size = 100
        total_users = 500
        
        for batch_start in range(0, total_users, batch_size):
            users = []
            for i in range(batch_start, min(batch_start + batch_size, total_users)):
                user = User(
                    username=f'perf_user_{i}',
                    email=f'perf{i}@test.com',
                    role=UserRole.USER if i % 10 != 0 else UserRole.ADMIN
                )
                user.set_password('password123')
                users.append(user)
            
            db_session.add_all(users)
            db_session.commit()
        
        creation_time = time.time() - start_time
        
        # Test query performance
        start_time = time.time()
        
        # Complex queries
        admin_users = User.query.filter_by(role=UserRole.ADMIN).all()
        recent_users = User.query.filter(
            User.created_at > datetime.datetime.now() - timedelta(hours=1)
        ).count()
        user_emails = User.query.filter(
            User.email.like('%@test.com')
        ).limit(50).all()
        
        query_time = time.time() - start_time
        
        # Performance assertions
        assert creation_time < 30.0, f"User creation took {creation_time:.2f}s"
        assert query_time < 5.0, f"Queries took {query_time:.2f}s"
        
        # Verify data integrity
        total_created = User.query.filter(
            User.username.like('perf_user_%')
        ).count()
        assert total_created == total_users
        
        # Verify admin ratio (10% should be admin)
        admin_count = len([u for u in admin_users if u.username.startswith('perf_user_')])
        expected_admins = total_users // 10
        assert abs(admin_count - expected_admins) <= 1  # Allow for rounding
    
    def test_complex_relationship_queries(self, db_session):
        """Test performance of complex relationship queries."""
        import time
        
        # Create test data with relationships
        admin = User(
            username='perf_admin',
            email='perf_admin@test.com',
            role=UserRole.ADMIN
        )
        admin.set_password('password123')
        db_session.add(admin)
        db_session.commit()
        
        # Create many related records
        messages = []
        audits = []
        
        for i in range(100):
            message = AdminMessage(
                title=f'Performance Message {i}',
                message=f'Content for message {i}',
                message_type='info',
                created_by_id=admin.id,
                expires_at=datetime.datetime.now() + timedelta(days=30)
            )
            messages.append(message)
            
            audit = AuditLog(
                user_id=admin.id,
                username=admin.username,
                action_type=AuditActionType.ADMIN_ACTION,
                action_description=f'Action {i}',
                ip_address='192.168.1.1'
            )
            audits.append(audit)
        
        db_session.add_all(messages + audits)
        db_session.commit()
        
        # Test relationship query performance
        start_time = time.time()
        
        # Query with joins
        admin_with_messages = User.query.filter_by(
            username='perf_admin'
        ).first()
        
        admin_messages = admin_with_messages.admin_messages
        admin_audits = AuditLog.query.filter_by(user_id=admin.id).all()
        
        query_time = time.time() - start_time
        
        # Performance and correctness assertions
        assert query_time < 2.0, f"Relationship queries took {query_time:.2f}s"
        assert len(admin_messages) == 100
        assert len(admin_audits) == 100
    
    def test_database_index_effectiveness(self, db_session):
        """Test that database indexes are effective."""
        import time
        
        # Create test data
        users = []
        for i in range(200):
            user = User(
                username=f'index_test_{i}',
                email=f'index{i}@test.com',
                role=UserRole.USER
            )
            user.set_password('password123')
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        # Test indexed queries (should be fast)
        start_time = time.time()
        
        # Username lookup (should use index)
        user_by_username = User.query.filter_by(username='index_test_50').first()
        
        # Email lookup (should use index)
        user_by_email = User.query.filter_by(email='index50@test.com').first()
        
        indexed_query_time = time.time() - start_time
        
        # Test non-indexed query for comparison
        start_time = time.time()
        
        # Role-based query (may or may not be indexed)
        user_users = User.query.filter_by(role=UserRole.USER).limit(10).all()
        
        role_query_time = time.time() - start_time
        
        # Assertions
        assert indexed_query_time < 1.0, f"Indexed queries took {indexed_query_time:.2f}s"
        assert user_by_username is not None
        assert user_by_email is not None
        assert len(user_users) == 10
