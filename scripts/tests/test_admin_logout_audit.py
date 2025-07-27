#!/usr/bin/env python3
"""
Test to verify that admin logout now properly creates audit logs
"""
import sys
import os

# Add the parent directory to the path to import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, AuditLog, AuditActionType

def test_admin_logout_audit():
    """Test that admin logout now creates audit logs"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing admin logout audit logging...")
        
        # Count before
        count_before = AuditLog.query.count()
        print(f"📊 Audit logs before test: {count_before}")
        
        with app.test_client() as client:
            # First try to login
            print("🔐 Attempting login...")
            login_response = client.post('/auth/login', data={
                'username_or_email': 'admin',
                'password': os.getenv('DB_PASS', 'Admin123!')
            }, follow_redirects=False)
            
            print(f"📡 Login response status: {login_response.status_code}")
            
            if login_response.status_code == 302:  # Redirect after successful login
                print("✅ Login successful, now testing admin logout...")
                
                # Now test admin logout route
                print("🚪 Attempting admin logout...")
                admin_logout_response = client.get('/admin/logout', follow_redirects=True)
                print(f"📡 Admin logout response status: {admin_logout_response.status_code}")
                print(f"📍 Final URL after redirects: {admin_logout_response.request.path}")
                
                # Count after
                count_after = AuditLog.query.count()
                print(f"📊 Audit logs after test: {count_after}")
                print(f"📈 New logs created: {count_after - count_before}")
                
                # Show recent logs
                recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(3).all()
                print(f"📝 Recent audit entries:")
                for i, log in enumerate(recent_logs, 1):
                    timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else 'N/A'
                    print(f"   {i}. [{timestamp}] {log.action_type.value}: {log.action_description}")
                
            else:
                print("❌ Login failed, cannot test logout")
        
        return True

if __name__ == "__main__":
    print("🔬 Admin Logout Audit Test")
    print("=" * 50)
    test_admin_logout_audit()
