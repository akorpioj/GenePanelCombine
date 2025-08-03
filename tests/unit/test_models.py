"""
Unit tests for database models
"""
import pytest
import datetime
from datetime import timedelta
from app.models import (
    User, AdminMessage, AuditLog, Visit, PanelDownload, UserRole, db,
    SavedPanel, PanelVersion, PanelGene, PanelShare, PanelChange,
    PanelStatus, PanelVisibility, ChangeType, SharePermission
)

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


@pytest.mark.unit
@pytest.mark.database
class TestSavedPanelModel:
    """Test SavedPanel model functionality."""
    
    def test_saved_panel_creation(self, db_session, sample_user):
        """Test creating a new saved panel."""
        panel = SavedPanel(
            name='BRCA Cancer Panel',
            description='Genes associated with breast and ovarian cancer',
            tags='cancer,BRCA,hereditary',
            owner_id=sample_user.id,
            status=PanelStatus.ACTIVE,
            visibility=PanelVisibility.PRIVATE,
            gene_count=25,
            source_type='panelapp',
            source_reference='panel_123'
        )
        
        db_session.add(panel)
        db_session.commit()
        
        assert panel.id is not None
        assert panel.name == 'BRCA Cancer Panel'
        assert panel.description == 'Genes associated with breast and ovarian cancer'
        assert panel.tags == 'cancer,BRCA,hereditary'
        assert panel.owner_id == sample_user.id
        assert panel.status == PanelStatus.ACTIVE
        assert panel.visibility == PanelVisibility.PRIVATE
        assert panel.gene_count == 25
        assert panel.source_type == 'panelapp'
        assert panel.source_reference == 'panel_123'
        assert panel.created_at is not None
        assert panel.updated_at is not None
        assert panel.last_accessed_at is not None
        assert panel.storage_backend == 'gcs'  # Default is 'gcs' not 'local'
        assert panel.version_count == 1
    
    def test_saved_panel_repr(self, db_session, sample_user):
        """Test saved panel string representation."""
        panel = SavedPanel(
            name='Test Panel',
            owner_id=sample_user.id,
            gene_count=10
        )
        db_session.add(panel)
        db_session.commit()
        
        assert repr(panel) == f'<SavedPanel {panel.id}: Test Panel by {sample_user.username}>'
    
    def test_saved_panel_owner_relationship(self, db_session, sample_user):
        """Test saved panel owner relationship."""
        panel = SavedPanel(
            name='Test Panel',
            owner_id=sample_user.id,
            gene_count=10
        )
        db_session.add(panel)
        db_session.commit()
        
        assert panel.owner == sample_user
        assert panel in sample_user.saved_panels


@pytest.mark.unit
@pytest.mark.database
class TestPanelVersionModel:
    """Test PanelVersion model functionality."""
    
    def test_panel_version_creation(self, db_session, sample_user):
        """Test creating a new panel version."""
        # Create a saved panel first
        panel = SavedPanel(
            name='Test Panel',
            owner_id=sample_user.id,
            gene_count=10
        )
        db_session.add(panel)
        db_session.commit()
        
        # Create a panel version
        version = PanelVersion(
            panel_id=panel.id,
            version_number=1,
            comment='Initial version',
            created_by_id=sample_user.id,
            gene_count=10,
            changes_summary='Created panel with 10 genes',
            storage_path='/data/panels/v1.json'
        )
        
        db_session.add(version)
        db_session.commit()
        
        assert version.id is not None
        assert version.panel_id == panel.id
        assert version.version_number == 1
        assert version.comment == 'Initial version'
        assert version.created_by_id == sample_user.id
        assert version.gene_count == 10
        assert version.changes_summary == 'Created panel with 10 genes'
        assert version.storage_path == '/data/panels/v1.json'
        assert version.created_at is not None
    
    def test_panel_version_relationships(self, db_session, sample_user):
        """Test panel version relationships."""
        panel = SavedPanel(
            name='Test Panel',
            owner_id=sample_user.id,
            gene_count=10
        )
        db_session.add(panel)
        db_session.commit()
        
        version = PanelVersion(
            panel_id=panel.id,
            version_number=1,
            created_by_id=sample_user.id,
            gene_count=10
        )
        db_session.add(version)
        db_session.commit()
        
        assert version.panel == panel
        assert version.created_by == sample_user
        assert version in panel.versions
    
    def test_unique_panel_version_constraint(self, db_session, sample_user):
        """Test unique constraint on panel_id and version_number."""
        panel = SavedPanel(
            name='Test Panel',
            owner_id=sample_user.id,
            gene_count=10
        )
        db_session.add(panel)
        db_session.commit()
        
        version1 = PanelVersion(
            panel_id=panel.id,
            version_number=1,
            created_by_id=sample_user.id
        )
        db_session.add(version1)
        db_session.commit()
        
        # Try to create duplicate version
        version2 = PanelVersion(
            panel_id=panel.id,
            version_number=1,  # Same version number
            created_by_id=sample_user.id
        )
        db_session.add(version2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()


@pytest.mark.unit
@pytest.mark.database
class TestPanelGeneModel:
    """Test PanelGene model functionality."""
    
    def test_panel_gene_creation(self, db_session, sample_user):
        """Test creating a new panel gene."""
        panel = SavedPanel(
            name='Test Panel',
            owner_id=sample_user.id,
            gene_count=1
        )
        db_session.add(panel)
        db_session.commit()
        
        gene = PanelGene(
            panel_id=panel.id,
            gene_symbol='BRCA1',
            gene_name='BRCA1 DNA repair associated',
            ensembl_id='ENSG00000012048',
            hgnc_id='HGNC:1100',
            confidence_level='3',
            mode_of_inheritance='Autosomal Dominant',
            phenotype='Breast and ovarian cancer',
            evidence_level='Expert Review Green',
            source_panel_id='137',
            source_list_type='green',
            added_by_id=sample_user.id,
            user_notes='High penetrance gene',
            custom_confidence='High'
        )
        
        db_session.add(gene)
        db_session.commit()
        
        assert gene.id is not None
        assert gene.panel_id == panel.id
        assert gene.gene_symbol == 'BRCA1'
        assert gene.gene_name == 'BRCA1 DNA repair associated'
        assert gene.ensembl_id == 'ENSG00000012048'
        assert gene.hgnc_id == 'HGNC:1100'
        assert gene.confidence_level == '3'
        assert gene.mode_of_inheritance == 'Autosomal Dominant'
        assert gene.phenotype == 'Breast and ovarian cancer'
        assert gene.evidence_level == 'Expert Review Green'
        assert gene.source_panel_id == '137'
        assert gene.source_list_type == 'green'
        assert gene.is_active is True
        assert gene.added_by_id == sample_user.id
        assert gene.added_at is not None
        assert gene.user_notes == 'High penetrance gene'
        assert gene.custom_confidence == 'High'
        assert gene.is_modified is False
    
    def test_panel_gene_relationships(self, db_session, sample_user):
        """Test panel gene relationships."""
        panel = SavedPanel(
            name='Test Panel',
            owner_id=sample_user.id,
            gene_count=1
        )
        db_session.add(panel)
        db_session.commit()
        
        gene = PanelGene(
            panel_id=panel.id,
            gene_symbol='BRCA1',
            added_by_id=sample_user.id
        )
        db_session.add(gene)
        db_session.commit()
        
        assert gene.panel == panel
        assert gene.added_by == sample_user
        assert gene in panel.genes
    
    def test_unique_panel_gene_constraint(self, db_session, sample_user):
        """Test unique constraint on panel_id and gene_symbol."""
        panel = SavedPanel(
            name='Test Panel',
            owner_id=sample_user.id,
            gene_count=1
        )
        db_session.add(panel)
        db_session.commit()
        
        gene1 = PanelGene(
            panel_id=panel.id,
            gene_symbol='BRCA1',
            added_by_id=sample_user.id
        )
        db_session.add(gene1)
        db_session.commit()
        
        # Try to create duplicate gene symbol in same panel
        gene2 = PanelGene(
            panel_id=panel.id,
            gene_symbol='BRCA1',  # Same gene symbol
            added_by_id=sample_user.id
        )
        db_session.add(gene2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()


@pytest.mark.unit
@pytest.mark.database
class TestPanelShareModel:
    """Test PanelShare model functionality."""
    
    def test_panel_share_creation(self, db_session, sample_user, admin_user):
        """Test creating a new panel share."""
        panel = SavedPanel(
            name='Shared Panel',
            owner_id=sample_user.id,
            gene_count=10,
            visibility=PanelVisibility.SHARED
        )
        db_session.add(panel)
        db_session.commit()
        
        share = PanelShare(
            panel_id=panel.id,
            shared_by_id=sample_user.id,
            shared_with_user_id=admin_user.id,
            permission_level=SharePermission.VIEW,
            can_reshare=False,
            expires_at=datetime.datetime.now() + timedelta(days=30),
            share_token='abc123def456'
        )
        
        db_session.add(share)
        db_session.commit()
        
        assert share.id is not None
        assert share.panel_id == panel.id
        assert share.shared_by_id == sample_user.id
        assert share.shared_with_user_id == admin_user.id
        assert share.permission_level == SharePermission.VIEW
        assert share.can_reshare is False
        assert share.is_active is True
        assert share.expires_at is not None
        assert share.created_at is not None
        assert share.share_token == 'abc123def456'
    
    def test_panel_share_relationships(self, db_session, sample_user, admin_user):
        """Test panel share relationships."""
        panel = SavedPanel(
            name='Shared Panel',
            owner_id=sample_user.id,
            gene_count=10
        )
        db_session.add(panel)
        db_session.commit()
        
        share = PanelShare(
            panel_id=panel.id,
            shared_by_id=sample_user.id,
            shared_with_user_id=admin_user.id,
            permission_level=SharePermission.EDIT
        )
        db_session.add(share)
        db_session.commit()
        
        assert share.panel == panel
        assert share.shared_by == sample_user
        assert share.shared_with_user == admin_user
        assert share in panel.shares
    
    def test_panel_share_token_only(self, db_session, sample_user):
        """Test panel share with token only (no specific user)."""
        panel = SavedPanel(
            name='Token Shared Panel',
            owner_id=sample_user.id,
            gene_count=5
        )
        db_session.add(panel)
        db_session.commit()
        
        share = PanelShare(
            panel_id=panel.id,
            shared_by_id=sample_user.id,
            permission_level=SharePermission.VIEW,
            share_token='public_link_token_123'
        )
        
        db_session.add(share)
        db_session.commit()
        
        assert share.shared_with_user_id is None
        assert share.shared_with_team_id is None
        assert share.share_token == 'public_link_token_123'


@pytest.mark.unit
@pytest.mark.database
class TestPanelChangeModel:
    """Test PanelChange model functionality."""
    
    def test_panel_change_creation(self, db_session, sample_user):
        """Test creating a new panel change record."""
        panel = SavedPanel(
            name='Test Panel',
            owner_id=sample_user.id,
            gene_count=10
        )
        db_session.add(panel)
        db_session.commit()
        
        version = PanelVersion(
            panel_id=panel.id,
            version_number=1,
            created_by_id=sample_user.id
        )
        db_session.add(version)
        db_session.commit()
        
        change = PanelChange(
            panel_id=panel.id,
            version_id=version.id,
            change_type=ChangeType.GENE_ADDED,
            target_type='gene',
            target_id='BRCA1',
            changed_by_id=sample_user.id,
            change_reason='Added high-confidence gene'
        )
        
        # Set values using the encrypted fields
        change.old_value = None
        change.new_value = {'gene_symbol': 'BRCA1', 'confidence': '3'}
        
        db_session.add(change)
        db_session.commit()
        
        assert change.id is not None
        assert change.panel_id == panel.id
        assert change.version_id == version.id
        assert change.change_type == ChangeType.GENE_ADDED
        assert change.target_type == 'gene'
        assert change.target_id == 'BRCA1'
        assert change.old_value is None
        assert change.new_value == {'gene_symbol': 'BRCA1', 'confidence': '3'}
        assert change.changed_by_id == sample_user.id
        assert change.changed_at is not None
        assert change.change_reason == 'Added high-confidence gene'
    
    def test_panel_change_relationships(self, db_session, sample_user):
        """Test panel change relationships."""
        panel = SavedPanel(
            name='Test Panel',
            owner_id=sample_user.id,
            gene_count=10
        )
        db_session.add(panel)
        db_session.commit()
        
        version = PanelVersion(
            panel_id=panel.id,
            version_number=1,
            created_by_id=sample_user.id
        )
        db_session.add(version)
        db_session.commit()
        
        change = PanelChange(
            panel_id=panel.id,
            version_id=version.id,
            change_type=ChangeType.METADATA_CHANGED,
            target_type='panel',
            changed_by_id=sample_user.id
        )
        db_session.add(change)
        db_session.commit()
        
        # Test relationships that do exist
        assert change.changed_by == sample_user
        assert change.version == version  # This should work from the backref
        
        # Test reverse relationships
        assert change in version.changes


@pytest.mark.unit
@pytest.mark.database
class TestSavedPanelsIntegration:
    """Test integration between saved panels models."""
    
    def test_complete_panel_workflow(self, db_session, sample_user, admin_user):
        """Test a complete workflow with all saved panel models."""
        # Create a saved panel
        panel = SavedPanel(
            name='Complete Workflow Panel',
            description='Testing full workflow',
            owner_id=sample_user.id,
            gene_count=2
        )
        db_session.add(panel)
        db_session.commit()
        
        # Create first version
        version1 = PanelVersion(
            panel_id=panel.id,
            version_number=1,
            comment='Initial version',
            created_by_id=sample_user.id,
            gene_count=2
        )
        db_session.add(version1)
        db_session.commit()
        
        # Set current version
        panel.current_version_id = version1.id
        db_session.commit()
        
        # Add genes
        gene1 = PanelGene(
            panel_id=panel.id,
            gene_symbol='BRCA1',
            gene_name='BRCA1 DNA repair associated',
            added_by_id=sample_user.id
        )
        gene2 = PanelGene(
            panel_id=panel.id,
            gene_symbol='BRCA2',
            gene_name='BRCA2 DNA repair associated',
            added_by_id=sample_user.id
        )
        db_session.add_all([gene1, gene2])
        db_session.commit()
        
        # Share panel
        share = PanelShare(
            panel_id=panel.id,
            shared_by_id=sample_user.id,
            shared_with_user_id=admin_user.id,
            permission_level=SharePermission.EDIT
        )
        db_session.add(share)
        db_session.commit()
        
        # Record changes
        change1 = PanelChange(
            panel_id=panel.id,
            version_id=version1.id,
            change_type=ChangeType.GENE_ADDED,
            target_type='gene',
            target_id='BRCA1',
            changed_by_id=sample_user.id
        )
        change2 = PanelChange(
            panel_id=panel.id,
            version_id=version1.id,
            change_type=ChangeType.GENE_ADDED,
            target_type='gene',
            target_id='BRCA2',
            changed_by_id=sample_user.id
        )
        db_session.add_all([change1, change2])
        db_session.commit()
        
        # Verify relationships
        assert len(list(panel.versions)) == 1
        assert len(list(panel.genes)) == 2
        assert len(list(panel.shares)) == 1
        assert len(list(version1.changes)) == 2  # Changes are related to version, not panel directly
        assert panel.current_version == version1
        assert panel.owner == sample_user
        
        # Verify gene relationships
        assert gene1.panel == panel
        assert gene2.panel == panel
        assert gene1.added_by == sample_user
        
        # Verify share relationships
        assert share.panel == panel
        assert share.shared_by == sample_user
        assert share.shared_with_user == admin_user
        
        # Verify change relationships
        assert change1.version == version1
        assert change1.changed_by == sample_user
    
    def test_panel_versioning(self, db_session, sample_user):
        """Test panel versioning workflow."""
        # Create panel
        panel = SavedPanel(
            name='Versioning Test Panel',
            owner_id=sample_user.id,
            gene_count=1
        )
        db_session.add(panel)
        db_session.commit()
        
        # Create version 1
        version1 = PanelVersion(
            panel_id=panel.id,
            version_number=1,
            comment='Initial version',
            created_by_id=sample_user.id,
            gene_count=1
        )
        db_session.add(version1)
        db_session.commit()
        
        # Create version 2
        version2 = PanelVersion(
            panel_id=panel.id,
            version_number=2,
            comment='Added more genes',
            created_by_id=sample_user.id,
            gene_count=3
        )
        db_session.add(version2)
        db_session.commit()
        
        # Update panel version count and current version
        panel.version_count = 2
        panel.current_version_id = version2.id
        db_session.commit()
        
        # Verify versioning
        assert len(list(panel.versions)) == 2
        assert panel.version_count == 2
        assert panel.current_version == version2
        assert panel.current_version.version_number == 2
        assert panel.current_version.comment == 'Added more genes'
    
    def test_enum_values(self, db_session, sample_user):
        """Test enum values for saved panels system."""
        panel = SavedPanel(
            name='Enum Test Panel',
            owner_id=sample_user.id,
            gene_count=0,
            status=PanelStatus.DRAFT,
            visibility=PanelVisibility.PUBLIC
        )
        db_session.add(panel)
        db_session.commit()
        
        share = PanelShare(
            panel_id=panel.id,
            shared_by_id=sample_user.id,
            permission_level=SharePermission.ADMIN,
            share_token='test_token'
        )
        db_session.add(share)
        db_session.commit()
        
        version = PanelVersion(
            panel_id=panel.id,
            version_number=1,
            created_by_id=sample_user.id
        )
        db_session.add(version)
        db_session.commit()
        
        change = PanelChange(
            panel_id=panel.id,
            version_id=version.id,
            change_type=ChangeType.CONFIDENCE_CHANGED,
            target_type='gene',
            changed_by_id=sample_user.id
        )
        db_session.add(change)
        db_session.commit()
        
        # Verify enum values
        assert panel.status == PanelStatus.DRAFT
        assert panel.visibility == PanelVisibility.PUBLIC
        assert share.permission_level == SharePermission.ADMIN
        assert change.change_type == ChangeType.CONFIDENCE_CHANGED
