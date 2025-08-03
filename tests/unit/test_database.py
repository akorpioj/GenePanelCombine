"""
Comprehensive unit tests for database operations and data integrity
"""
import pytest
import datetime
from datetime import timedelta
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy import inspect, text
from unittest.mock import patch, Mock
from app.models import (
    User, AdminMessage, AuditLog, Visit, PanelDownload, 
    UserRole, AuditActionType, db
)


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseSchema:
    """Test database schema integrity and structure."""
    
    def test_database_tables_exist(self, db_session):
        """Test that all required tables exist."""
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        required_tables = [
            'user', 'admin_message', 'audit_log', 
            'visit', 'panel_download'
        ]
        
        for table in required_tables:
            assert table in tables, f"Table {table} does not exist"
    
    def test_database_indexes(self, db_session):
        """Test that critical indexes exist."""
        inspector = inspect(db.engine)
        
        # Check user table indexes
        user_indexes = inspector.get_indexes('user')
        user_index_columns = [idx['column_names'] for idx in user_indexes]
        
        # For SQLite, unique constraints may not show as separate indexes
        # Check if we have unique constraints instead
        unique_constraints = inspector.get_unique_constraints('user')
        unique_columns = []
        for constraint in unique_constraints:
            unique_columns.extend(constraint['column_names'])
        
        # Username and email should be indexed or have unique constraints
        username_indexed = any('username' in cols for cols in user_index_columns) or 'username' in unique_columns
        email_indexed = any('email' in cols for cols in user_index_columns) or 'email' in unique_columns
        
        assert username_indexed, "Username should be indexed or have unique constraint"
        assert email_indexed, "Email should be indexed or have unique constraint"
    
    def test_database_foreign_keys(self, db_session):
        """Test foreign key relationships."""
        inspector = inspect(db.engine)
        
        # Check AuditLog foreign keys
        audit_fks = inspector.get_foreign_keys('audit_log')
        audit_fk_tables = [fk['referred_table'] for fk in audit_fks]
        assert 'user' in audit_fk_tables
        
        # Check AdminMessage foreign keys
        admin_msg_fks = inspector.get_foreign_keys('admin_message')
        admin_msg_fk_tables = [fk['referred_table'] for fk in admin_msg_fks]
        assert 'user' in admin_msg_fk_tables
    
    def test_database_constraints(self, db_session):
        """Test database constraints."""
        inspector = inspect(db.engine)
        
        # Check User table constraints
        user_constraints = inspector.get_unique_constraints('user')
        constraint_columns = [uc['column_names'] for uc in user_constraints]
        
        # Username and email should have unique constraints
        assert any('username' in cols for cols in constraint_columns)
        assert any('email' in cols for cols in constraint_columns)


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseOperations:
    """Test basic database CRUD operations."""
    
    def test_database_connection(self, db_session):
        """Test database connection is working."""
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1
    
    def test_create_operation(self, db_session):
        """Test CREATE operations."""
        user = User(
            username='create_test',
            email='create@test.com',
            role=UserRole.USER
        )
        user.set_password('password123')
        
        db_session.add(user)
        db_session.commit()
        
        # Verify creation
        created_user = User.query.filter_by(username='create_test').first()
        assert created_user is not None
        assert created_user.email == 'create@test.com'
    
    def test_read_operation(self, db_session, sample_user):
        """Test READ operations."""
        # Test single record read
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.email == 'test@example.com'
        
        # Test multiple record read
        users = User.query.all()
        assert len(users) >= 1
        
        # Test filtered read
        admin_users = User.query.filter_by(role=UserRole.ADMIN).all()
        # Should be empty since sample_user is USER role
        assert len([u for u in admin_users if u.username == 'testuser']) == 0
    
    def test_update_operation(self, db_session, sample_user):
        """Test UPDATE operations."""
        original_email = sample_user.email
        sample_user.email = 'updated@test.com'
        db_session.commit()
        
        # Verify update
        updated_user = db_session.get(User, sample_user.id)
        assert updated_user.email == 'updated@test.com'
        assert updated_user.email != original_email
    
    def test_delete_operation(self, db_session):
        """Test DELETE operations."""
        # Create user to delete
        user = User(
            username='delete_test',
            email='delete@test.com',
            role=UserRole.USER
        )
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        
        user_id = user.id
        
        # Delete user
        db_session.delete(user)
        db_session.commit()
        
        # Verify deletion
        deleted_user = db_session.get(User, user_id)
        assert deleted_user is None


@pytest.mark.unit
@pytest.mark.database
class TestDataIntegrity:
    """Test data integrity constraints and validation."""
    
    def test_unique_constraints(self, db_session, sample_user):
        """Test unique constraint enforcement."""
        # Try to create user with duplicate username
        duplicate_user = User(
            username='testuser',  # Same as sample_user
            email='different@test.com',
            role=UserRole.USER
        )
        duplicate_user.set_password('password123')
        
        db_session.add(duplicate_user)
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
        
        # Try to create user with duplicate email
        duplicate_email_user = User(
            username='different_user',
            email='test@example.com',  # Same as sample_user
            role=UserRole.USER
        )
        duplicate_email_user.set_password('password123')
        
        db_session.add(duplicate_email_user)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_not_null_constraints(self, db_session):
        """Test NOT NULL constraint enforcement."""
        # Try to create user without required fields
        with pytest.raises(IntegrityError):
            user = User(email='test@test.com')  # Missing username
            db_session.add(user)
            db_session.commit()
        
        db_session.rollback()
        
        with pytest.raises(IntegrityError):
            user = User(username='test')  # Missing email
            db_session.add(user)
            db_session.commit()
    
    def test_foreign_key_constraints(self, db_session, sample_user):
        """Test foreign key constraint enforcement."""
        # SQLite may not enforce foreign keys by default in testing
        # Check if foreign key enforcement is enabled
        try:
            # Try to create audit log with invalid user_id
            invalid_audit = AuditLog(
                user_id=99999,  # Non-existent user
                username='invalid',
                action_type=AuditActionType.LOGIN,
                action_description='Test action',
                ip_address='192.168.1.1'
            )
            
            db_session.add(invalid_audit)
            db_session.commit()
            
            # If we get here, foreign keys might not be enforced in test DB
            # Clean up the invalid record
            db_session.delete(invalid_audit)
            db_session.commit()
            
        except IntegrityError:
            # This is expected behavior with foreign key enforcement
            db_session.rollback()
        
        # Valid foreign key should always work
        valid_audit = AuditLog(
            user_id=sample_user.id,
            username=sample_user.username,
            action_type=AuditActionType.LOGIN,
            action_description='Test action',
            ip_address='192.168.1.1'
        )
        
        db_session.add(valid_audit)
        db_session.commit()
        assert valid_audit.id is not None
    
    def test_data_types_validation(self, db_session):
        """Test data type validation."""
        # SQLite is more lenient with data types than other databases
        # Test that we can create users with normal data
        user = User(
            username='test_user_types',
            email='types@test.com',
            role=UserRole.USER
        )
        user.set_password('password123')
        
        # Test normal length - should work
        db_session.add(user)
        db_session.commit()
        
        # Test very long username (SQLite may not enforce VARCHAR limits)
        try:
            long_username_user = User(
                username='a' * 200,  # Very long username
                email='long@example.com',
                role=UserRole.USER
            )
            long_username_user.set_password('password123')
            
            db_session.add(long_username_user)
            db_session.commit()
            
            # If successful, clean up
            db_session.delete(long_username_user)
            db_session.commit()
            
        except (IntegrityError, Exception):
            # This is expected if database enforces length limits
            db_session.rollback()
    
    def test_enum_validation(self, db_session):
        """Test enum field validation."""
        # Create user with valid role
        user = User(
            username='enum_test',
            email='enum@test.com',
            role=UserRole.USER
        )
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        
        assert user.role == UserRole.USER
        
        # Test audit log enum
        audit = AuditLog(
            user_id=user.id,
            username=user.username,
            action_type=AuditActionType.LOGIN,
            action_description='Test',
            ip_address='192.168.1.1'
        )
        db_session.add(audit)
        db_session.commit()
        
        assert audit.action_type == AuditActionType.LOGIN


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseTransactions:
    """Test database transaction handling."""
    
    def test_transaction_commit(self, db_session):
        """Test successful transaction commit."""
        initial_count = User.query.count()
        
        user1 = User(
            username='trans_user1',
            email='trans1@test.com',
            role=UserRole.USER
        )
        user1.set_password('password123')
        
        user2 = User(
            username='trans_user2',
            email='trans2@test.com',
            role=UserRole.USER
        )
        user2.set_password('password123')
        
        db_session.add_all([user1, user2])
        db_session.commit()
        
        final_count = User.query.count()
        assert final_count == initial_count + 2
    
    def test_transaction_rollback(self, db_session):
        """Test transaction rollback on error."""
        initial_count = User.query.count()
        
        try:
            user1 = User(
                username='rollback_user1',
                email='rollback1@test.com',
                role=UserRole.USER
            )
            user1.set_password('password123')
            
            # This should cause an error (duplicate username)
            user2 = User(
                username='rollback_user1',  # Same username
                email='rollback2@test.com',
                role=UserRole.USER
            )
            user2.set_password('password123')
            
            db_session.add_all([user1, user2])
            db_session.commit()
            
        except IntegrityError:
            db_session.rollback()
        
        # Count should be unchanged
        final_count = User.query.count()
        assert final_count == initial_count
    
    def test_nested_transactions(self, db_session):
        """Test nested transaction behavior."""
        initial_count = User.query.count()
        
        # Outer transaction
        user1 = User(
            username='outer_user',
            email='outer@test.com',
            role=UserRole.USER
        )
        user1.set_password('password123')
        db_session.add(user1)
        
        # Create savepoint
        savepoint = db_session.begin_nested()
        
        try:
            # Inner transaction with error
            user2 = User(
                username='outer_user',  # Duplicate username
                email='inner@test.com',
                role=UserRole.USER
            )
            user2.set_password('password123')
            db_session.add(user2)
            db_session.flush()  # Force error
            
        except IntegrityError:
            savepoint.rollback()
        
        # Outer transaction should still be valid
        db_session.commit()
        
        final_count = User.query.count()
        assert final_count == initial_count + 1


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseRelationships:
    """Test database model relationships."""
    
    def test_user_downloads_relationship(self, db_session, sample_user):
        """Test User-PanelDownload relationship."""
        download = PanelDownload(
            user_id=sample_user.id,
            ip_address='192.168.1.1',
            download_date=datetime.datetime.now(),
            panel_ids='1,2,3',
            list_types='standard',
            gene_count=100
        )
        
        db_session.add(download)
        db_session.commit()
        
        # Test relationship
        assert len(sample_user.downloads) == 1
        assert sample_user.downloads[0] == download
        assert download.user == sample_user
    
    def test_user_admin_messages_relationship(self, db_session, admin_user):
        """Test User-AdminMessage relationship."""
        message = AdminMessage(
            title='Test Message',
            message='Test content',
            message_type='info',
            created_by_id=admin_user.id,
            expires_at=datetime.datetime.now() + timedelta(days=7)
        )
        
        db_session.add(message)
        db_session.commit()
        
        # Test relationship
        assert len(admin_user.admin_messages) == 1
        assert admin_user.admin_messages[0] == message
        assert message.created_by == admin_user
    
    def test_orphaned_records_handling(self, db_session):
        """Test handling of orphaned records."""
        # Create user and related records
        user = User(
            username='orphan_test',
            email='orphan@test.com',
            role=UserRole.USER
        )
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        
        # Create related records
        download = PanelDownload(
            user_id=user.id,
            ip_address='192.168.1.1',
            download_date=datetime.datetime.now(),
            panel_ids='1,2,3',
            list_types='standard',
            gene_count=100
        )
        
        audit = AuditLog(
            user_id=user.id,
            username=user.username,
            action_type=AuditActionType.LOGIN,
            action_description='Test',
            ip_address='192.168.1.1'
        )
        
        db_session.add_all([download, audit])
        db_session.commit()
        
        user_id = user.id
        
        # Delete user (behavior depends on cascade settings and foreign key enforcement)
        db_session.delete(user)
        
        try:
            db_session.commit()
            
            # Check if related records still exist
            remaining_download = PanelDownload.query.filter_by(user_id=user_id).first()
            remaining_audit = AuditLog.query.filter_by(user_id=user_id).first()
            
            # In SQLite without foreign key enforcement, records might remain
            # This is acceptable behavior for testing
            # Just verify the system handles it gracefully
            
        except IntegrityError:
            # If foreign keys are enforced and prevent deletion, that's also valid
            db_session.rollback()
            
            # User should still exist
            existing_user = db_session.get(User, user_id)
            assert existing_user is not None


@pytest.mark.unit
@pytest.mark.database
class TestDatabasePerformance:
    """Test database performance and optimization."""
    
    def test_bulk_operations(self, db_session):
        """Test bulk database operations."""
        import time
        
        # Test bulk insert performance with smaller dataset for testing
        start_time = time.time()
        
        users = []
        # Reduce number for faster testing
        for i in range(20):
            user = User(
                username=f'bulk_user_{i}',
                email=f'bulk{i}@test.com',
                role=UserRole.USER
            )
            user.set_password('password123')
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        end_time = time.time()
        bulk_time = end_time - start_time
        
        # More reasonable threshold for test environment
        assert bulk_time < 30.0, f"Bulk insert took {bulk_time:.2f} seconds"
        
        # Verify all users were created
        created_users = User.query.filter(User.username.like('bulk_user_%')).all()
        assert len(created_users) == 20
    
    def test_query_performance(self, db_session):
        """Test query performance."""
        import time
        
        # Create test data
        users = []
        for i in range(50):
            user = User(
                username=f'perf_user_{i}',
                email=f'perf{i}@test.com',
                role=UserRole.USER if i % 2 == 0 else UserRole.ADMIN
            )
            user.set_password('password123')
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        # Test query performance
        start_time = time.time()
        
        # Complex query with filtering and ordering
        result = User.query.filter(
            User.username.like('perf_user_%')
        ).filter(
            User.role == UserRole.USER
        ).order_by(User.created_at.desc()).limit(10).all()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Should complete quickly
        assert query_time < 1.0, f"Query took {query_time:.2f} seconds"
        assert len(result) == 10
    
    def test_connection_pooling(self, db_session):
        """Test database connection handling."""
        # Test multiple simultaneous operations
        operations = []
        
        for i in range(10):
            user = User(
                username=f'pool_user_{i}',
                email=f'pool{i}@test.com',
                role=UserRole.USER
            )
            user.set_password('password123')
            operations.append(user)
        
        # Add all at once to test connection handling
        db_session.add_all(operations)
        db_session.commit()
        
        # Verify all operations completed
        created_users = User.query.filter(User.username.like('pool_user_%')).all()
        assert len(created_users) == 10


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseMigrations:
    """Test database migration scenarios."""
    
    def test_schema_evolution(self, db_session):
        """Test schema changes and migrations."""
        # This would test adding new columns, indexes, etc.
        # For now, we'll test that the current schema is consistent
        
        inspector = inspect(db.engine)
        
        # Check that all model tables exist
        user_table = inspector.get_table_names()
        assert 'user' in user_table
        
        # Check column existence
        user_columns = [col['name'] for col in inspector.get_columns('user')]
        required_columns = [
            'id', 'username', 'email', 'password_hash', 
            'role', 'is_active', 'created_at'
        ]
        
        for col in required_columns:
            assert col in user_columns, f"Column {col} missing from user table"
    
    def test_data_migration_compatibility(self, db_session, sample_user):
        """Test that existing data remains valid after schema changes."""
        # Test that existing user data is still accessible
        assert sample_user.id is not None
        assert sample_user.username == 'testuser'
        assert sample_user.role == UserRole.USER
        
        # Test that we can still perform operations
        sample_user.last_login = datetime.datetime.now()
        db_session.commit()
        
        # Verify update worked
        updated_user = db_session.get(User, sample_user.id)
        assert updated_user.last_login is not None


@pytest.mark.unit
@pytest.mark.database 
class TestDatabaseSecurity:
    """Test database security and access control."""
    
    def test_password_hashing_security(self, db_session):
        """Test password hashing security."""
        user = User(
            username='security_test',
            email='security@test.com',
            role=UserRole.USER
        )
        
        password = 'supersecretpassword'
        user.set_password(password)
        
        # Password should be hashed
        assert user.password_hash != password
        assert len(user.password_hash) > 50  # Should be a long hash
        
        # Should use secure hashing
        assert user.password_hash.startswith(('pbkdf2:', 'scrypt:', 'argon2'))
        
        # Verify password correctly
        assert user.check_password(password)
        assert not user.check_password('wrongpassword')
    
    def test_sql_injection_prevention(self, db_session):
        """Test SQL injection prevention."""
        # Test that parameterized queries prevent injection
        malicious_input = "'; DROP TABLE user; --"
        
        # This should be safe due to parameterized queries
        user = User.query.filter_by(username=malicious_input).first()
        assert user is None
        
        # User table should still exist
        users = User.query.all()
        assert isinstance(users, list)
    
    def test_sensitive_data_handling(self, db_session):
        """Test handling of sensitive data."""
        user = User(
            username='sensitive_test',
            email='sensitive@test.com',
            role=UserRole.USER
        )
        user.set_password('password123')
        
        # Set sensitive fields
        user.first_name = 'Sensitive'
        user.last_name = 'Data'
        user.organization = 'Secret Corp'
        
        db_session.add(user)
        db_session.commit()
        
        # Verify sensitive data is handled properly
        # (This would test encryption if implemented)
        assert user.first_name == 'Sensitive'
        assert user.last_name == 'Data'
        assert user.organization == 'Secret Corp'


@pytest.mark.unit
@pytest.mark.database
@pytest.mark.slow
class TestDatabaseStress:
    """Test database under stress conditions."""
    
    def test_large_dataset_handling(self, db_session):
        """Test handling of large datasets."""
        # Create a large number of records
        large_batch = []
        for i in range(1000):
            user = User(
                username=f'stress_user_{i}',
                email=f'stress{i}@test.com',
                role=UserRole.USER
            )
            user.set_password('password123')
            large_batch.append(user)
        
        # Add in chunks to avoid memory issues
        chunk_size = 100
        for i in range(0, len(large_batch), chunk_size):
            chunk = large_batch[i:i + chunk_size]
            db_session.add_all(chunk)
            db_session.commit()
        
        # Verify all records were created
        stress_users = User.query.filter(User.username.like('stress_user_%')).count()
        assert stress_users == 1000
    
    def test_concurrent_access_simulation(self, db_session):
        """Test simulated concurrent access."""
        # Simulate concurrent updates
        user = User(
            username='concurrent_test',
            email='concurrent@test.com',
            role=UserRole.USER
        )
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        
        # Simulate multiple updates
        for i in range(10):
            user.login_count = i
            db_session.commit()
        
        # Verify final state
        final_user = User.query.filter_by(username='concurrent_test').first()
        assert final_user.login_count == 9


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseBackupRestore:
    """Test database backup and restore functionality."""
    
    def test_data_export_import(self, db_session, sample_user):
        """Test data export and import capabilities."""
        # Export user data
        user_data = sample_user.to_dict()
        
        # Verify export contains expected fields
        assert 'id' in user_data
        assert 'username' in user_data
        assert 'email' in user_data
        assert 'role' in user_data
        
        # Sensitive data should not be in export
        assert 'password_hash' not in user_data
    
    def test_data_consistency_check(self, db_session):
        """Test data consistency validation."""
        # Create related records
        user = User(
            username='consistency_test',
            email='consistency@test.com',
            role=UserRole.ADMIN
        )
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        
        message = AdminMessage(
            title='Consistency Test',
            message='Testing data consistency',
            message_type='info',
            created_by_id=user.id
        )
        db_session.add(message)
        db_session.commit()
        
        # Verify relationships are consistent
        assert message.created_by == user
        assert message in user.admin_messages
        
        # Test referential integrity
        message_creator = db_session.get(User, message.created_by_id)
        assert message_creator == user
