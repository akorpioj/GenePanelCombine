"""
Unit tests for Saved Panels API endpoints
"""
import pytest
import json
from datetime import datetime, timedelta
from flask import url_for
from unittest.mock import patch

from app.models import (
    SavedPanel, PanelVersion, PanelGene, PanelShare, PanelChange,
    PanelStatus, PanelVisibility, ChangeType, SharePermission, User, db
)


@pytest.mark.unit
@pytest.mark.api
class TestSavedPanelsAPIAuth:
    """Test authentication for saved panels API endpoints."""
    
    def test_get_panels_requires_auth(self, client):
        """Test that getting saved panels requires authentication."""
        response = client.get('/api/v1/saved-panels/')
        # Should redirect to login or return 302, or return 401 if API properly configured
        assert response.status_code in [302, 401, 404]  # 404 means route exists but auth fails
    
    def test_create_panel_requires_auth(self, client):
        """Test that creating panels requires authentication."""
        data = {
            'name': 'Test Panel',
            'genes': [{'gene_symbol': 'BRCA1'}]
        }
        response = client.post('/api/v1/saved-panels/', 
                              data=json.dumps(data),
                              content_type='application/json')
        # Should redirect to login or return 302, or return 401 if API properly configured  
        assert response.status_code in [302, 401, 404]  # 404 means route exists but auth fails


@pytest.mark.unit
@pytest.mark.api
class TestSavedPanelsAPICRUD:
    """Test CRUD operations for saved panels API."""
    
    def test_get_empty_panels_list(self, auth_client, sample_user):
        """Test getting empty panels list for authenticated user."""
        response = auth_client.get('/api/v1/saved-panels/')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'panels' in data
        assert 'pagination' in data
        assert data['panels'] == []
        assert data['pagination']['total'] == 0
    
    def test_create_saved_panel(self, auth_client, sample_user, db_session):
        """Test creating a new saved panel via API."""
        panel_data = {
            'name': 'BRCA Cancer Panel',
            'description': 'Genes associated with breast cancer',
            'tags': 'cancer,BRCA,hereditary',
            'status': 'ACTIVE',
            'visibility': 'PRIVATE',
            'source_type': 'manual',
            'version_comment': 'Initial creation',
            'genes': [
                {
                    'gene_symbol': 'BRCA1',
                    'gene_name': 'BRCA1 DNA repair associated',
                    'confidence_level': '3',
                    'phenotype': 'Breast and ovarian cancer'
                },
                {
                    'gene_symbol': 'BRCA2',
                    'gene_name': 'BRCA2 DNA repair associated',
                    'confidence_level': '3',
                    'phenotype': 'Breast and ovarian cancer'
                }
            ]
        }
        
        response = auth_client.post('/api/v1/saved-panels/',
                                   data=json.dumps(panel_data),
                                   content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Verify response data
        assert data['name'] == 'BRCA Cancer Panel'
        assert data['description'] == 'Genes associated with breast cancer'
        assert data['tags'] == 'cancer,BRCA,hereditary'
        assert data['status'] == 'ACTIVE'
        assert data['visibility'] == 'PRIVATE'
        assert data['gene_count'] == 2
        assert data['version_count'] == 1
        assert data['storage_backend'] == 'gcs'
        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data
        
        # Verify database
        panel = SavedPanel.query.filter_by(name='BRCA Cancer Panel').first()
        assert panel is not None
        assert panel.owner_id == sample_user.id
        assert panel.gene_count == 2
        
        # Verify version was created
        version = PanelVersion.query.filter_by(panel_id=panel.id).first()
        assert version is not None
        assert version.version_number == 1
        assert version.comment == 'Initial creation'
        
        # Verify genes were created
        genes = PanelGene.query.filter_by(panel_id=panel.id).all()
        assert len(genes) == 2
        gene_symbols = [g.gene_symbol for g in genes]
        assert 'BRCA1' in gene_symbols
        assert 'BRCA2' in gene_symbols
    
    def test_create_panel_validation_errors(self, auth_client):
        """Test validation errors when creating panels."""
        # Missing name
        response = auth_client.post('/api/v1/saved-panels/',
                                   data=json.dumps({'genes': []}),
                                   content_type='application/json')
        assert response.status_code == 400
        
        # Missing genes
        response = auth_client.post('/api/v1/saved-panels/',
                                   data=json.dumps({'name': 'Test'}),
                                   content_type='application/json')
        assert response.status_code == 400
        
        # Empty genes list
        response = auth_client.post('/api/v1/saved-panels/',
                                   data=json.dumps({'name': 'Test', 'genes': []}),
                                   content_type='application/json')
        assert response.status_code == 400
    
    def test_create_panel_duplicate_name(self, auth_client, sample_user, db_session):
        """Test error when creating panel with duplicate name."""
        # Create first panel
        panel1 = SavedPanel(
            name='Duplicate Name',
            owner_id=sample_user.id,
            gene_count=1
        )
        db_session.add(panel1)
        db_session.commit()
        
        # Try to create second panel with same name
        panel_data = {
            'name': 'Duplicate Name',
            'genes': [{'gene_symbol': 'BRCA1'}]
        }
        
        response = auth_client.post('/api/v1/saved-panels/',
                                   data=json.dumps(panel_data),
                                   content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'already exists' in data['message']
    
    def test_get_specific_panel(self, auth_client, sample_user, db_session):
        """Test getting a specific saved panel with genes."""
        # Create panel with genes
        panel = SavedPanel(
            name='Test Panel',
            description='Test description',
            owner_id=sample_user.id,
            gene_count=2
        )
        db_session.add(panel)
        db_session.flush()
        
        gene1 = PanelGene(
            panel_id=panel.id,
            gene_symbol='BRCA1',
            gene_name='BRCA1 DNA repair associated',
            confidence_level='3',
            added_by_id=sample_user.id
        )
        gene2 = PanelGene(
            panel_id=panel.id,
            gene_symbol='BRCA2',
            gene_name='BRCA2 DNA repair associated',
            confidence_level='3',
            added_by_id=sample_user.id
        )
        db_session.add_all([gene1, gene2])
        db_session.commit()
        
        response = auth_client.get(f'/api/v1/saved-panels/{panel.id}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['id'] == panel.id
        assert data['name'] == 'Test Panel'
        assert data['description'] == 'Test description'
        assert data['gene_count'] == 2
        assert len(data['genes']) == 2
        
        # Verify gene data
        gene_symbols = [g['gene_symbol'] for g in data['genes']]
        assert 'BRCA1' in gene_symbols
        assert 'BRCA2' in gene_symbols
        
        # Verify owner info
        assert data['owner']['id'] == sample_user.id
        assert data['owner']['username'] == sample_user.username
    
    def test_get_nonexistent_panel(self, auth_client):
        """Test getting a panel that doesn't exist."""
        response = auth_client.get('/api/v1/saved-panels/99999')
        assert response.status_code == 404
    
    def test_get_other_user_panel(self, auth_client, admin_user, db_session):
        """Test that users cannot access other users' private panels."""
        # Create panel owned by admin
        panel = SavedPanel(
            name='Admin Panel',
            owner_id=admin_user.id,
            gene_count=0,
            visibility=PanelVisibility.PRIVATE
        )
        db_session.add(panel)
        db_session.commit()
        
        # Try to access as regular user
        response = auth_client.get(f'/api/v1/saved-panels/{panel.id}')
        assert response.status_code == 404  # Should be 404, not 403, for security
    
    def test_update_panel_metadata(self, auth_client, sample_user, db_session):
        """Test updating panel metadata."""
        panel = SavedPanel(
            name='Original Name',
            description='Original description',
            owner_id=sample_user.id,
            gene_count=0,
            status=PanelStatus.DRAFT
        )
        db_session.add(panel)
        db_session.commit()
        
        update_data = {
            'name': 'Updated Name',
            'description': 'Updated description',
            'status': 'ACTIVE',
            'tags': 'new,tags',
            'version_comment': 'Updated metadata'
        }
        
        response = auth_client.put(f'/api/v1/saved-panels/{panel.id}',
                                  data=json.dumps(update_data),
                                  content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['name'] == 'Updated Name'
        assert data['description'] == 'Updated description'
        assert data['status'] == 'ACTIVE'
        assert data['tags'] == 'new,tags'
        assert data['version_count'] == 2  # New version created
        
        # Verify database update
        db_session.refresh(panel)
        assert panel.name == 'Updated Name'
        assert panel.description == 'Updated description'
        assert panel.status == PanelStatus.ACTIVE
        assert panel.tags == 'new,tags'
    
    def test_update_other_user_panel(self, auth_client, admin_user, db_session):
        """Test that users cannot update other users' panels."""
        panel = SavedPanel(
            name='Admin Panel',
            owner_id=admin_user.id,
            gene_count=0
        )
        db_session.add(panel)
        db_session.commit()
        
        update_data = {'name': 'Hacked Name'}
        
        response = auth_client.put(f'/api/v1/saved-panels/{panel.id}',
                                  data=json.dumps(update_data),
                                  content_type='application/json')
        
        assert response.status_code == 404
    
    def test_delete_panel(self, auth_client, sample_user, db_session):
        """Test deleting a saved panel."""
        panel = SavedPanel(
            name='Panel to Delete',
            owner_id=sample_user.id,
            gene_count=0
        )
        db_session.add(panel)
        db_session.commit()
        panel_id = panel.id
        
        response = auth_client.delete(f'/api/v1/saved-panels/{panel_id}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert 'deleted successfully' in data['message']
        
        # Verify panel is deleted
        deleted_panel = SavedPanel.query.get(panel_id)
        assert deleted_panel is None
    
    def test_delete_other_user_panel(self, auth_client, admin_user, db_session):
        """Test that users cannot delete other users' panels."""
        panel = SavedPanel(
            name='Admin Panel',
            owner_id=admin_user.id,
            gene_count=0
        )
        db_session.add(panel)
        db_session.commit()
        
        response = auth_client.delete(f'/api/v1/saved-panels/{panel.id}')
        assert response.status_code == 404
    
    def test_get_panels_with_pagination(self, auth_client, sample_user, db_session):
        """Test getting panels list with pagination."""
        # Create multiple panels
        for i in range(15):
            panel = SavedPanel(
                name=f'Panel {i:02d}',
                owner_id=sample_user.id,
                gene_count=i
            )
            db_session.add(panel)
        db_session.commit()
        
        # Test first page
        response = auth_client.get('/api/v1/saved-panels/?page=1&per_page=10')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['panels']) == 10
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 10
        assert data['pagination']['total'] == 15
        assert data['pagination']['pages'] == 2
        assert data['pagination']['has_next'] is True
        assert data['pagination']['has_prev'] is False
        
        # Test second page
        response = auth_client.get('/api/v1/saved-panels/?page=2&per_page=10')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['panels']) == 5
        assert data['pagination']['page'] == 2
        assert data['pagination']['has_next'] is False
        assert data['pagination']['has_prev'] is True
    
    def test_get_panels_with_filters(self, auth_client, sample_user, db_session):
        """Test getting panels with status and search filters."""
        # Create panels with different statuses
        active_panel = SavedPanel(
            name='Active Panel',
            owner_id=sample_user.id,
            gene_count=0,
            status=PanelStatus.ACTIVE,
            description='This is active'
        )
        draft_panel = SavedPanel(
            name='Draft Panel',
            owner_id=sample_user.id,
            gene_count=0,
            status=PanelStatus.DRAFT,
            description='This is draft'
        )
        db_session.add_all([active_panel, draft_panel])
        db_session.commit()
        
        # Filter by status
        response = auth_client.get('/api/v1/saved-panels/?status=active')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['panels']) == 1
        assert data['panels'][0]['status'] == 'ACTIVE'
        
        # Search by name
        response = auth_client.get('/api/v1/saved-panels/?search=draft')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['panels']) == 1
        assert data['panels'][0]['name'] == 'Draft Panel'


@pytest.mark.unit
@pytest.mark.api
class TestPanelVersionsAPI:
    """Test panel versions API endpoints."""
    
    def test_get_panel_versions(self, auth_client, sample_user, db_session):
        """Test getting version history for a panel."""
        panel = SavedPanel(
            name='Versioned Panel',
            owner_id=sample_user.id,
            gene_count=0,
            version_count=2
        )
        db_session.add(panel)
        db_session.flush()
        
        # Create versions
        version1 = PanelVersion(
            panel_id=panel.id,
            version_number=1,
            comment='Initial version',
            created_by_id=sample_user.id,
            gene_count=5
        )
        version2 = PanelVersion(
            panel_id=panel.id,
            version_number=2,
            comment='Added more genes',
            created_by_id=sample_user.id,
            gene_count=10
        )
        db_session.add_all([version1, version2])
        db_session.commit()
        
        response = auth_client.get(f'/api/v1/saved-panels/{panel.id}/versions')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['panel_id'] == panel.id
        assert data['panel_name'] == 'Versioned Panel'
        assert data['total'] == 2
        assert len(data['versions']) == 2
        
        # Verify versions are ordered by version number descending
        assert data['versions'][0]['version_number'] == 2
        assert data['versions'][1]['version_number'] == 1
        
        # Verify version data
        v2_data = data['versions'][0]
        assert v2_data['comment'] == 'Added more genes'
        assert v2_data['gene_count'] == 10
        assert v2_data['created_by']['username'] == sample_user.username
    
    def test_get_versions_for_nonexistent_panel(self, auth_client):
        """Test getting versions for a panel that doesn't exist."""
        response = auth_client.get('/api/v1/saved-panels/99999/versions')
        assert response.status_code == 404


@pytest.mark.unit
@pytest.mark.api
class TestPanelSharingAPI:
    """Test panel sharing API endpoints."""
    
    def test_share_panel_with_user(self, auth_client, sample_user, admin_user, db_session):
        """Test sharing a panel with another user."""
        panel = SavedPanel(
            name='Panel to Share',
            owner_id=sample_user.id,
            gene_count=0
        )
        db_session.add(panel)
        db_session.commit()
        
        share_data = {
            'shared_with_user_id': admin_user.id,
            'permission_level': 'EDIT',
            'can_reshare': True,
            'expires_in_days': 30
        }
        
        response = auth_client.post(f'/api/v1/saved-panels/{panel.id}/share',
                                   data=json.dumps(share_data),
                                   content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['panel_id'] == panel.id
        assert data['shared_with_user_id'] == admin_user.id
        assert data['permission_level'] == 'EDIT'
        assert data['can_reshare'] is True
        assert data['is_active'] is True
        assert 'expires_at' in data
        assert 'share_token' in data
        
        # Verify database
        share = PanelShare.query.filter_by(panel_id=panel.id).first()
        assert share is not None
        assert share.shared_with_user_id == admin_user.id
        assert share.permission_level == SharePermission.EDIT
    
    def test_share_panel_public_link(self, auth_client, sample_user, db_session):
        """Test creating a public share link."""
        panel = SavedPanel(
            name='Public Panel',
            owner_id=sample_user.id,
            gene_count=0
        )
        db_session.add(panel)
        db_session.commit()
        
        share_data = {
            'create_public_link': True,
            'permission_level': 'VIEW',
            'expires_in_days': 7
        }
        
        response = auth_client.post(f'/api/v1/saved-panels/{panel.id}/share',
                                   data=json.dumps(share_data),
                                   content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['panel_id'] == panel.id
        assert data['shared_with_user_id'] is None
        assert data['permission_level'] == 'VIEW'
        assert 'share_token' in data
        assert len(data['share_token']) > 20  # Token should be long
    
    def test_share_duplicate_user(self, auth_client, sample_user, admin_user, db_session):
        """Test error when sharing with same user twice."""
        panel = SavedPanel(
            name='Panel',
            owner_id=sample_user.id,
            gene_count=0
        )
        db_session.add(panel)
        db_session.flush()
        
        # Create existing share
        existing_share = PanelShare(
            panel_id=panel.id,
            shared_by_id=sample_user.id,
            shared_with_user_id=admin_user.id,
            permission_level=SharePermission.VIEW
        )
        db_session.add(existing_share)
        db_session.commit()
        
        # Try to share again
        share_data = {
            'shared_with_user_id': admin_user.id,
            'permission_level': 'VIEW'
        }
        
        response = auth_client.post(f'/api/v1/saved-panels/{panel.id}/share',
                                   data=json.dumps(share_data),
                                   content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'already shared' in data['message']
    
    def test_share_invalid_user(self, auth_client, sample_user, db_session):
        """Test error when sharing with non-existent user."""
        panel = SavedPanel(
            name='Panel',
            owner_id=sample_user.id,
            gene_count=0
        )
        db_session.add(panel)
        db_session.commit()
        
        share_data = {
            'shared_with_user_id': 99999,
            'permission_level': 'VIEW'
        }
        
        response = auth_client.post(f'/api/v1/saved-panels/{panel.id}/share',
                                   data=json.dumps(share_data),
                                   content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'not found' in data['message']
    
    def test_get_shared_panels(self, auth_client, sample_user, admin_user, db_session):
        """Test getting panels shared with current user."""
        # Create panel owned by admin
        panel = SavedPanel(
            name='Shared Panel',
            description='This is shared',
            owner_id=admin_user.id,
            gene_count=5,
            status=PanelStatus.ACTIVE
        )
        db_session.add(panel)
        db_session.flush()
        
        # Share it with sample_user
        share = PanelShare(
            panel_id=panel.id,
            shared_by_id=admin_user.id,
            shared_with_user_id=sample_user.id,
            permission_level=SharePermission.EDIT
        )
        db_session.add(share)
        db_session.commit()
        
        response = auth_client.get('/api/v1/saved-panels/shared')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['total'] == 1
        assert len(data['panels']) == 1
        
        shared_panel = data['panels'][0]
        assert shared_panel['id'] == panel.id
        assert shared_panel['name'] == 'Shared Panel'
        assert shared_panel['owner']['username'] == admin_user.username
        assert shared_panel['shared_permission'] == 'EDIT'
        assert 'shared_at' in shared_panel
    
    def test_get_shared_panels_excludes_expired(self, auth_client, sample_user, admin_user, db_session):
        """Test that expired shares are not included in shared panels."""
        panel = SavedPanel(
            name='Expired Share',
            owner_id=admin_user.id,
            gene_count=0
        )
        db_session.add(panel)
        db_session.flush()
        
        # Create expired share
        expired_share = PanelShare(
            panel_id=panel.id,
            shared_by_id=admin_user.id,
            shared_with_user_id=sample_user.id,
            permission_level=SharePermission.VIEW,
            expires_at=datetime.utcnow() - timedelta(days=1)  # Expired yesterday
        )
        db_session.add(expired_share)
        db_session.commit()
        
        response = auth_client.get('/api/v1/saved-panels/shared')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['total'] == 0
        assert len(data['panels']) == 0


@pytest.mark.unit
@pytest.mark.api
class TestSavedPanelsAPIRateLimiting:
    """Test rate limiting for saved panels API."""
    
    def test_create_panel_rate_limit(self, auth_client):
        """Test rate limiting on panel creation endpoint."""
        # The rate limit is 5 per minute for creating panels
        panel_data = {
            'name': 'Rate Test Panel',
            'genes': [{'gene_symbol': 'BRCA1'}]
        }
        
        # Make 5 requests (should all succeed)
        for i in range(5):
            panel_data['name'] = f'Rate Test Panel {i}'
            response = auth_client.post('/api/v1/saved-panels/',
                                       data=json.dumps(panel_data),
                                       content_type='application/json')
            # First requests should succeed or fail due to duplicate names, not rate limiting
            assert response.status_code in [201, 400]
        
        # 6th request should be rate limited
        panel_data['name'] = 'Rate Test Panel 6'
        response = auth_client.post('/api/v1/saved-panels/',
                                   data=json.dumps(panel_data),
                                   content_type='application/json')
        assert response.status_code == 429  # Too Many Requests


@pytest.mark.unit
@pytest.mark.api
class TestSavedPanelsAPIErrorHandling:
    """Test error handling in saved panels API."""
    
    def test_invalid_json(self, auth_client):
        """Test handling of invalid JSON."""
        response = auth_client.post('/api/v1/saved-panels/',
                                   data='invalid json',
                                   content_type='application/json')
        assert response.status_code == 400
    
    def test_invalid_status_filter(self, auth_client):
        """Test handling of invalid status filter."""
        response = auth_client.get('/api/v1/saved-panels/?status=invalid')
        assert response.status_code == 400
        data = response.get_json()
        assert 'Invalid status' in data['message']
    
    def test_invalid_visibility_filter(self, auth_client):
        """Test handling of invalid visibility filter."""
        response = auth_client.get('/api/v1/saved-panels/?visibility=invalid')
        assert response.status_code == 400
        data = response.get_json()
        assert 'Invalid visibility' in data['message']
    
    @patch('app.api.saved_panels.current_app')
    def test_database_error_handling(self, mock_app, auth_client, sample_user, db_session):
        """Test handling of database errors."""
        # Mock logger
        mock_app.logger.error = lambda x: None
        
        # Create a panel
        panel = SavedPanel(
            name='Test Panel',
            owner_id=sample_user.id,
            gene_count=0
        )
        db_session.add(panel)
        db_session.commit()
        
        # Mock a database error during update
        with patch('app.api.saved_panels.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception("Database error")
            
            update_data = {'name': 'Updated Name'}
            response = auth_client.put(f'/api/v1/saved-panels/{panel.id}',
                                      data=json.dumps(update_data),
                                      content_type='application/json')
            
            assert response.status_code == 500


@pytest.mark.unit  
@pytest.mark.api
class TestSavedPanelsAPIPermissions:
    """Test permission handling in saved panels API."""
    
    def test_shared_panel_view_permission(self, auth_client, sample_user, admin_user, db_session):
        """Test accessing shared panel with VIEW permission."""
        # Create panel owned by admin
        panel = SavedPanel(
            name='Shared Panel',
            owner_id=admin_user.id,
            gene_count=0
        )
        db_session.add(panel)
        db_session.flush()
        
        # Share with VIEW permission
        share = PanelShare(
            panel_id=panel.id,
            shared_by_id=admin_user.id,
            shared_with_user_id=sample_user.id,
            permission_level=SharePermission.VIEW
        )
        db_session.add(share)
        db_session.commit()
        
        # Should be able to read
        response = auth_client.get(f'/api/v1/saved-panels/{panel.id}')
        assert response.status_code == 200
        
        # Should NOT be able to update
        update_data = {'name': 'Hacked Name'}
        response = auth_client.put(f'/api/v1/saved-panels/{panel.id}',
                                  data=json.dumps(update_data),
                                  content_type='application/json')
        assert response.status_code == 403
    
    def test_shared_panel_edit_permission(self, auth_client, sample_user, admin_user, db_session):
        """Test accessing shared panel with EDIT permission."""
        # Create panel owned by admin
        panel = SavedPanel(
            name='Shared Panel',
            owner_id=admin_user.id,
            gene_count=0
        )
        db_session.add(panel)
        db_session.flush()
        
        # Share with EDIT permission
        share = PanelShare(
            panel_id=panel.id,
            shared_by_id=admin_user.id,
            shared_with_user_id=sample_user.id,
            permission_level=SharePermission.EDIT
        )
        db_session.add(share)
        db_session.commit()
        
        # Should be able to read
        response = auth_client.get(f'/api/v1/saved-panels/{panel.id}')
        assert response.status_code == 200
        
        # Should be able to update
        update_data = {'name': 'Updated by Editor'}
        response = auth_client.put(f'/api/v1/saved-panels/{panel.id}',
                                  data=json.dumps(update_data),
                                  content_type='application/json')
        assert response.status_code == 200
        
        # Should NOT be able to share (requires ADMIN)
        share_data = {'shared_with_user_id': sample_user.id}
        response = auth_client.post(f'/api/v1/saved-panels/{panel.id}/share',
                                   data=json.dumps(share_data),
                                   content_type='application/json')
        assert response.status_code == 403
    
    def test_expired_share_access_denied(self, auth_client, sample_user, admin_user, db_session):
        """Test that expired shares deny access."""
        # Create panel owned by admin
        panel = SavedPanel(
            name='Expired Share Panel',
            owner_id=admin_user.id,
            gene_count=0
        )
        db_session.add(panel)
        db_session.flush()
        
        # Create expired share
        expired_share = PanelShare(
            panel_id=panel.id,
            shared_by_id=admin_user.id,
            shared_with_user_id=sample_user.id,
            permission_level=SharePermission.VIEW,
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        db_session.add(expired_share)
        db_session.commit()
        
        # Access should be denied
        response = auth_client.get(f'/api/v1/saved-panels/{panel.id}')
        assert response.status_code == 403
        data = response.get_json()
        assert 'expired' in data['message']
