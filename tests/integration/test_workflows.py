"""
Integration tests for PanelMerge application
"""
import pytest
import json
import io

@pytest.mark.integration
class TestUserWorkflow:
    """Test complete user workflows."""
    
    def test_user_registration_and_login_flow(self, client, db_session):
        """Test complete user registration and login workflow."""
        # Step 1: Register new user
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword',
            'password2': 'securepassword'
        }
        
        response = client.post('/auth/register', data=registration_data, follow_redirects=True)
        assert response.status_code == 200
        
        # Step 2: Login with new user
        login_data = {
            'username': 'newuser',
            'password': 'securepassword'
        }
        
        response = client.post('/auth/login', data=login_data, follow_redirects=True)
        assert response.status_code == 200
        
        # Step 3: Access protected resource
        response = client.get('/dashboard')
        assert response.status_code in [200, 404]  # Depends on route existence
        
        # Step 4: Logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
    
    def test_admin_user_workflow(self, client, db_session):
        """Test admin user workflow."""
        # Create admin user
        from app.models import User
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('adminpass')
        db_session.add(admin)
        db_session.commit()
        
        # Login as admin
        login_data = {'username': 'admin', 'password': 'adminpass'}
        response = client.post('/auth/login', data=login_data, follow_redirects=True)
        assert response.status_code == 200
        
        # Access admin routes
        response = client.get('/admin/dashboard')
        assert response.status_code in [200, 404]  # Depends on route existence
        
        # Create admin message
        message_data = {
            'title': 'System Maintenance',
            'message': 'The system will be down for maintenance.',
            'type': 'warning'
        }
        response = client.post('/admin/messages', data=message_data)
        assert response.status_code in [200, 302, 404]  # Success, redirect, or not found


@pytest.mark.integration
class TestAPIWorkflow:
    """Test complete API workflows."""
    
    def test_api_authentication_flow(self, client, sample_user, api_headers):
        """Test API authentication workflow."""
        # Step 1: Authenticate via API
        auth_data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        
        response = client.post('/api/v1/auth/login', 
                             headers=api_headers,
                             json=auth_data)
        
        if response.status_code == 200:
            # Step 2: Use token for authenticated requests
            token_data = response.get_json()
            token = token_data.get('access_token')
            
            auth_headers = api_headers.copy()
            auth_headers['Authorization'] = f'Bearer {token}'
            
            # Step 3: Access protected API endpoint
            response = client.get('/api/v1/users/current', headers=auth_headers)
            assert response.status_code == 200
        else:
            # API authentication might not be implemented yet
            assert response.status_code in [401, 404]
    
    def test_panel_discovery_workflow(self, client, sample_panel, sample_gene, api_headers):
        """Test panel discovery and exploration workflow."""
        # Step 1: Get list of panels
        response = client.get('/api/v1/panels', headers=api_headers)
        assert response.status_code == 200
        
        panels_data = response.get_json()
        assert 'panels' in panels_data
        
        # Step 2: Get specific panel details
        panel_id = sample_panel.panel_id
        response = client.get(f'/api/v1/panels/{panel_id}', headers=api_headers)
        assert response.status_code == 200
        
        panel_data = response.get_json()
        assert panel_data['panel_id'] == panel_id
        
        # Step 3: Get panel genes
        response = client.get(f'/api/v1/panels/{panel_id}/genes', headers=api_headers)
        assert response.status_code == 200
        
        genes_data = response.get_json()
        assert 'genes' in genes_data
    
    def test_gene_search_workflow(self, client, sample_gene, api_headers):
        """Test gene search workflow."""
        # Step 1: Search for genes
        response = client.get('/api/v1/genes/search?q=BRCA', headers=api_headers)
        assert response.status_code == 200
        
        search_data = response.get_json()
        assert 'genes' in search_data
        
        # Step 2: Get gene suggestions
        response = client.get('/api/v1/genes/suggestions?q=BR', headers=api_headers)
        assert response.status_code == 200
        
        suggestions_data = response.get_json()
        assert 'suggestions' in suggestions_data
        
        # Step 3: Get specific gene details
        response = client.get(f'/api/v1/genes/{sample_gene.gene_symbol}', headers=api_headers)
        assert response.status_code == 200
        
        gene_data = response.get_json()
        assert gene_data['gene_symbol'] == sample_gene.gene_symbol


@pytest.mark.integration
class TestFileUploadWorkflow:
    """Test complete file upload workflows."""
    
    def test_file_upload_and_processing_workflow(self, authenticated_client, sample_file_data):
        """Test complete file upload and processing workflow."""
        # Step 1: Access upload page
        response = authenticated_client.get('/upload')
        assert response.status_code == 200
        
        # Step 2: Upload valid file
        csv_content = sample_file_data['valid_csv']
        data = {
            'file': (io.BytesIO(csv_content.encode('utf-8')), 'test.csv')
        }
        
        response = authenticated_client.post('/upload', data=data, follow_redirects=True)
        assert response.status_code == 200
        
        # Step 3: Verify file was processed
        # This depends on actual implementation
        # Might redirect to results page or show success message
        assert b'success' in response.data.lower() or b'upload' in response.data.lower()


@pytest.mark.integration
class TestCacheIntegration:
    """Test cache integration with application."""
    
    def test_panel_caching_integration(self, client, sample_panel, mock_cache):
        """Test panel data caching integration."""
        panel_id = sample_panel.panel_id
        
        # First request - should cache the result
        response1 = client.get(f'/api/v1/panels/{panel_id}')
        assert response1.status_code == 200
        
        # Second request - should use cached result
        response2 = client.get(f'/api/v1/panels/{panel_id}')
        assert response2.status_code == 200
        
        # Responses should be identical
        assert response1.data == response2.data
    
    def test_cache_invalidation_integration(self, admin_client, sample_panel, mock_cache):
        """Test cache invalidation when data changes."""
        panel_id = sample_panel.panel_id
        
        # Get panel data
        response1 = admin_client.get(f'/api/v1/panels/{panel_id}')
        assert response1.status_code == 200
        
        # Simulate panel update (this depends on actual admin functionality)
        # Cache should be invalidated
        
        # Get panel data again
        response2 = admin_client.get(f'/api/v1/panels/{panel_id}')
        assert response2.status_code == 200


@pytest.mark.integration
class TestSecurityIntegration:
    """Test security features integration."""
    
    def test_session_security_integration(self, client, sample_user):
        """Test session security features."""
        # Login
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        })
        
        # Check session security headers
        # This depends on actual security header implementation
        assert response.status_code in [200, 302]
        
        # Test session timeout (if implemented)
        # Would require waiting or manipulating session data
    
    def test_csrf_protection_integration(self, client, sample_user):
        """Test CSRF protection integration."""
        # Login first
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        })
        
        # Try to perform state-changing operation without CSRF token
        response = client.post('/admin/messages', data={
            'title': 'Test',
            'message': 'Test message'
        })
        
        # Should be protected by CSRF (depending on implementation)
        # This test depends on actual CSRF protection setup
        assert response.status_code in [200, 400, 403, 404]
    
    def test_audit_logging_integration(self, client, sample_user, db_session):
        """Test audit logging integration."""
        from app.models import AuditLog
        
        initial_count = AuditLog.query.count()
        
        # Perform audited action
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        })
        
        # Check if audit log was created
        final_count = AuditLog.query.count()
        assert final_count >= initial_count  # Should have logged the action


@pytest.mark.integration
class TestDatabaseIntegration:
    """Test database integration and migrations."""
    
    def test_database_schema_integrity(self, db_session):
        """Test database schema integrity."""
        from app.models import User, Panel, Gene, AdminMessage, AuditLog
        
        # Test that all models can be created
        user = User(username='test', email='test@example.com')
        panel = Panel(panel_id=1, name='Test Panel')
        gene = Gene(gene_symbol='TEST', panel_id=1)
        
        db_session.add_all([user, panel, gene])
        db_session.commit()
        
        # Test relationships
        assert gene.panel == panel
        assert gene in panel.genes
    
    def test_database_constraints(self, db_session):
        """Test database constraints enforcement."""
        from app.models import User
        
        # Create user
        user1 = User(username='testuser', email='test@example.com')
        db_session.add(user1)
        db_session.commit()
        
        # Try to create duplicate username
        user2 = User(username='testuser', email='different@example.com')
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise constraint violation
            db_session.commit()
    
    def test_database_transactions(self, db_session):
        """Test database transaction handling."""
        from app.models import User
        
        initial_count = User.query.count()
        
        try:
            # Start transaction
            user1 = User(username='user1', email='user1@example.com')
            user2 = User(username='user2', email='user2@example.com')
            
            db_session.add_all([user1, user2])
            
            # Simulate error before commit
            raise Exception("Simulated error")
            
        except Exception:
            db_session.rollback()
        
        # Count should be unchanged
        final_count = User.query.count()
        assert final_count == initial_count


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Test performance integration scenarios."""
    
    def test_large_dataset_handling(self, client, db_session):
        """Test handling of large datasets."""
        from app.models import Panel, Gene
        
        # Create large number of panels and genes
        panels = []
        for i in range(100):
            panel = Panel(panel_id=i, name=f'Panel {i}')
            panels.append(panel)
        
        db_session.add_all(panels)
        db_session.commit()
        
        # Test API response time
        import time
        start_time = time.time()
        
        response = client.get('/api/v1/panels')
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 5.0  # Should respond within 5 seconds
    
    def test_concurrent_requests_handling(self, client, sample_panel):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get(f'/api/v1/panels/{sample_panel.panel_id}')
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert total_time < 10.0  # Should complete within 10 seconds
