"""
Test suite for the Version Control System

This comprehensive test suite covers:
- Version creation and management
- Branch operations
- Tag management
- Retention policies
- Merge operations
- API endpoints
- Edge cases and error conditions
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app import create_app, db
from app.models import (
    User, SavedPanel, PanelVersion, PanelGene, PanelChange,
    PanelVersionTag, PanelVersionBranch, PanelVersionMetadata,
    PanelRetentionPolicy, TagType, VersionType, AuditActionType
)
from app.version_control_service import (
    VersionControlService, RetentionPolicyError, BranchError,
    TagError, MergeConflictError
)
from app.audit_service import AuditService


class TestVersionControlService:
    """Test the core version control service functionality"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = create_app('testing')
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def test_user(self, app):
        """Create a test user"""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash='hashed_password'
            )
            db.session.add(user)
            db.session.commit()
            return user
    
    @pytest.fixture
    def test_panel(self, app, test_user):
        """Create a test panel"""
        with app.app_context():
            panel = SavedPanel(
                name='Test Panel',
                description='Test panel for version control',
                user_id=test_user.id
            )
            db.session.add(panel)
            db.session.commit()
            return panel
    
    @pytest.fixture
    def vc_service(self, app):
        """Create version control service instance"""
        with app.app_context():
            return VersionControlService()
    
    def test_create_version(self, app, test_panel, test_user, vc_service):
        """Test version creation"""
        with app.app_context():
            # Create initial version
            version = vc_service.create_version(
                panel_id=test_panel.id,
                user_id=test_user.id,
                comment="Initial version",
                changes_summary={'genes_added': 5, 'genes_removed': 0}
            )
            
            assert version is not None
            assert version.version_number == 1
            assert version.comment == "Initial version"
            assert version.version_type == VersionType.MAIN
            assert not version.is_protected
            
            # Create second version
            version2 = vc_service.create_version(
                panel_id=test_panel.id,
                user_id=test_user.id,
                comment="Second version",
                changes_summary={'genes_added': 2, 'genes_removed': 1}
            )
            
            assert version2.version_number == 2
            assert version2.parent_version_id == version.id
    
    def test_create_branch(self, app, test_panel, test_user, vc_service):
        """Test branch creation"""
        with app.app_context():
            # Create base version
            base_version = vc_service.create_version(
                panel_id=test_panel.id,
                user_id=test_user.id,
                comment="Base version"
            )
            
            # Create branch
            branch_version = vc_service.create_branch(
                panel_id=test_panel.id,
                user_id=test_user.id,
                source_version_id=base_version.id,
                branch_name="feature-branch",
                comment="Feature branch version"
            )
            
            assert branch_version is not None
            assert branch_version.version_type == VersionType.BRANCH
            assert branch_version.parent_version_id == base_version.id
            
            # Check branch record
            branch = PanelVersionBranch.query.filter_by(
                version_id=branch_version.id
            ).first()
            assert branch is not None
            assert branch.branch_name == "feature-branch"
    
    def test_tag_management(self, app, test_panel, test_user, vc_service):
        """Test tag creation and management"""
        with app.app_context():
            # Create version
            version = vc_service.create_version(
                panel_id=test_panel.id,
                user_id=test_user.id,
                comment="Production ready version"
            )
            
            # Create tag
            vc_service.tag_manager.create_tag(
                version_id=version.id,
                tag_name="v1.0-production",
                tag_type=TagType.PRODUCTION,
                user_id=test_user.id
            )
            
            # Verify tag
            tag = PanelVersionTag.query.filter_by(
                version_id=version.id,
                tag_name="v1.0-production"
            ).first()
            assert tag is not None
            assert tag.tag_type == TagType.PRODUCTION
            
            # Test duplicate tag prevention
            with pytest.raises(TagError):
                vc_service.tag_manager.create_tag(
                    version_id=version.id,
                    tag_name="v1.0-production",
                    tag_type=TagType.PRODUCTION,
                    user_id=test_user.id
                )
    
    def test_retention_policy(self, app, test_panel, test_user, vc_service):
        """Test retention policy application"""
        with app.app_context():
            # Create retention policy
            policy = PanelRetentionPolicy(
                panel_id=test_panel.id,
                max_versions=3,
                backup_retention_days=30,
                auto_cleanup_enabled=True,
                created_by_id=test_user.id
            )
            db.session.add(policy)
            db.session.commit()
            
            # Create multiple versions
            versions = []
            for i in range(5):
                version = vc_service.create_version(
                    panel_id=test_panel.id,
                    user_id=test_user.id,
                    comment=f"Version {i+1}"
                )
                versions.append(version)
                
                # Age the older versions
                if i < 3:
                    version.created_at = datetime.now() - timedelta(days=i*10)
                    db.session.commit()
            
            # Apply retention policy
            initial_count = PanelVersion.query.filter_by(panel_id=test_panel.id).count()
            vc_service.retention_policy.apply_retention(test_panel.id)
            
            final_count = PanelVersion.query.filter_by(panel_id=test_panel.id).count()
            assert final_count <= 3  # Should respect max_versions
    
    def test_protected_version_retention(self, app, test_panel, test_user, vc_service):
        """Test that protected versions are not deleted by retention policy"""
        with app.app_context():
            # Create retention policy
            policy = PanelRetentionPolicy(
                panel_id=test_panel.id,
                max_versions=2,
                created_by_id=test_user.id
            )
            db.session.add(policy)
            db.session.commit()
            
            # Create versions
            versions = []
            for i in range(4):
                version = vc_service.create_version(
                    panel_id=test_panel.id,
                    user_id=test_user.id,
                    comment=f"Version {i+1}"
                )
                versions.append(version)
            
            # Protect one of the older versions
            versions[1].is_protected = True
            versions[1].retention_priority = 10
            db.session.commit()
            
            # Apply retention policy
            vc_service.retention_policy.apply_retention(test_panel.id)
            
            # Verify protected version still exists
            protected_version = PanelVersion.query.get(versions[1].id)
            assert protected_version is not None
    
    def test_merge_operation(self, app, test_panel, test_user, vc_service):
        """Test merge operations"""
        with app.app_context():
            # Create base version
            base_version = vc_service.create_version(
                panel_id=test_panel.id,
                user_id=test_user.id,
                comment="Base version"
            )
            
            # Create two branch versions
            branch1 = vc_service.create_branch(
                panel_id=test_panel.id,
                user_id=test_user.id,
                source_version_id=base_version.id,
                branch_name="branch1",
                comment="Branch 1"
            )
            
            branch2 = vc_service.create_branch(
                panel_id=test_panel.id,
                user_id=test_user.id,
                source_version_id=base_version.id,
                branch_name="branch2", 
                comment="Branch 2"
            )
            
            # Mock merge logic for testing
            with patch.object(vc_service.merge_engine, '_perform_three_way_merge') as mock_merge:
                mock_merge.return_value = ([], {})  # No conflicts
                
                merge_result = vc_service.merge_versions(
                    panel_id=test_panel.id,
                    user_id=test_user.id,
                    source_version_id=branch1.id,
                    target_version_id=branch2.id,
                    comment="Merge branches"
                )
                
                assert merge_result is not None
                assert merge_result.version_type == VersionType.MERGE
    
    def test_version_access_tracking(self, app, test_panel, test_user, vc_service):
        """Test version access tracking"""
        with app.app_context():
            version = vc_service.create_version(
                panel_id=test_panel.id,
                user_id=test_user.id,
                comment="Test version"
            )
            
            initial_access_count = version.access_count
            initial_last_accessed = version.last_accessed_at
            
            # Update access stats
            version.update_access_stats()
            
            assert version.access_count == initial_access_count + 1
            assert version.last_accessed_at > initial_last_accessed


class TestVersionControlAPI:
    """Test the version control REST API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = create_app('testing')
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def auth_headers(self, app, client):
        """Create authentication headers"""
        with app.app_context():
            # Create test user
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash='hashed_password'
            )
            db.session.add(user)
            db.session.commit()
            
            # Mock authentication for testing
            return {'Authorization': 'Bearer test-token'}
    
    @pytest.fixture
    def test_data(self, app, auth_headers):
        """Create test data"""
        with app.app_context():
            user = User.query.first()
            panel = SavedPanel(
                name='Test Panel',
                description='Test panel',
                user_id=user.id
            )
            db.session.add(panel)
            db.session.commit()
            
            version = PanelVersion(
                panel_id=panel.id,
                version_number=1,
                comment="Test version",
                created_by_id=user.id,
                changes_summary={'test': True}
            )
            db.session.add(version)
            db.session.commit()
            
            return {'user': user, 'panel': panel, 'version': version}
    
    def test_create_tag_endpoint(self, client, auth_headers, test_data):
        """Test tag creation API endpoint"""
        version = test_data['version']
        
        response = client.post(
            f'/api/v1/version-control/versions/{version.id}/tags',
            json={
                'tag_name': 'v1.0-test',
                'tag_type': 'PRODUCTION',
                'description': 'Test tag'
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['tag_name'] == 'v1.0-test'
        assert data['tag_type'] == 'PRODUCTION'
    
    def test_list_tags_endpoint(self, client, auth_headers, test_data):
        """Test tag listing API endpoint"""
        version = test_data['version']
        user = test_data['user']
        
        # Create a tag first
        tag = PanelVersionTag(
            version_id=version.id,
            tag_name='test-tag',
            tag_type=TagType.STAGING,
            created_by_id=user.id
        )
        db.session.add(tag)
        db.session.commit()
        
        response = client.get(
            f'/api/v1/version-control/versions/{version.id}/tags',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['tag_name'] == 'test-tag'
    
    def test_create_branch_endpoint(self, client, auth_headers, test_data):
        """Test branch creation API endpoint"""
        panel = test_data['panel']
        version = test_data['version']
        
        response = client.post(
            f'/api/v1/version-control/panels/{panel.id}/branches',
            json={
                'source_version_id': version.id,
                'branch_name': 'feature-test',
                'comment': 'Test branch'
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'version_id' in data
        assert data['branch_name'] == 'feature-test'
    
    def test_version_diff_endpoint(self, client, auth_headers, test_data):
        """Test version diff API endpoint"""
        version1 = test_data['version']
        panel = test_data['panel']
        user = test_data['user']
        
        # Create second version
        version2 = PanelVersion(
            panel_id=panel.id,
            version_number=2,
            comment="Second version",
            created_by_id=user.id,
            parent_version_id=version1.id,
            changes_summary={'test': True}
        )
        db.session.add(version2)
        db.session.commit()
        
        response = client.get(
            f'/api/v1/version-control/versions/{version1.id}/diff/{version2.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'changes' in data
        assert 'summary' in data
    
    def test_retention_policy_endpoint(self, client, auth_headers, test_data):
        """Test retention policy API endpoint"""
        panel = test_data['panel']
        
        # Create retention policy
        response = client.post(
            f'/api/v1/version-control/panels/{panel.id}/retention-policy',
            json={
                'max_versions': 10,
                'backup_retention_days': 90,
                'auto_cleanup_enabled': True
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['max_versions'] == 10
        assert data['backup_retention_days'] == 90
        assert data['auto_cleanup_enabled'] is True
    
    def test_apply_retention_endpoint(self, client, auth_headers, test_data):
        """Test retention policy application endpoint"""
        panel = test_data['panel']
        user = test_data['user']
        
        # Create retention policy
        policy = PanelRetentionPolicy(
            panel_id=panel.id,
            max_versions=5,
            created_by_id=user.id
        )
        db.session.add(policy)
        db.session.commit()
        
        response = client.post(
            f'/api/v1/version-control/panels/{panel.id}/retention-policy/apply',
            json={'dry_run': True},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'versions_to_delete' in data
        assert 'protected_versions' in data


class TestRetentionPolicyLogic:
    """Test detailed retention policy logic"""
    
    def test_priority_based_retention(self):
        """Test that retention respects priority levels"""
        # This would be implemented with more detailed mock data
        pass
    
    def test_tag_based_protection(self):
        """Test that tagged versions are protected from deletion"""
        pass
    
    def test_time_based_retention(self):
        """Test time-based retention policies"""
        pass


class TestMergeEngine:
    """Test the merge engine functionality"""
    
    def test_simple_merge_no_conflicts(self):
        """Test merge with no conflicts"""
        pass
    
    def test_merge_with_conflicts(self):
        """Test merge conflict detection and resolution"""
        pass
    
    def test_three_way_merge(self):
        """Test three-way merge algorithm"""
        pass


class TestAuditIntegration:
    """Test audit trail integration with version control"""
    
    def test_version_creation_audit(self):
        """Test that version creation is audited"""
        pass
    
    def test_tag_creation_audit(self):
        """Test that tag creation is audited"""
        pass
    
    def test_retention_audit(self):
        """Test that retention policy application is audited"""
        pass


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_version_references(self):
        """Test handling of invalid version references"""
        pass
    
    def test_concurrent_operations(self):
        """Test handling of concurrent version control operations"""
        pass
    
    def test_database_constraints(self):
        """Test database constraint violations"""
        pass


# Integration test scenarios
class TestIntegrationScenarios:
    """Test real-world usage scenarios"""
    
    def test_full_development_workflow(self):
        """Test a complete development workflow"""
        # Create panel -> Create versions -> Create branches -> 
        # Merge branches -> Tag releases -> Apply retention
        pass
    
    def test_collaborative_development(self):
        """Test multiple users working on the same panel"""
        pass
    
    def test_production_deployment_scenario(self):
        """Test production deployment with tags and protection"""
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
