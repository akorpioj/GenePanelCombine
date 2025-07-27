#!/usr/bin/env python3
"""
Test real login and logout with test credentials to verify audit logging
"""
import sys
import os

# Add the parent directory to the path to import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, AuditLog, AuditActionType

def test_real_login_logout():
    """Test real login and logout with test credentials"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing real login/logout with test credentials...")
        
        # Count before
        count_before = AuditLog.query.count()
        print(f"📊 Audit logs before test: {count_before}")
        
        with app.test_client() as client:
            # Test login with test credentials
            print("🔐 Attempting login with testuser/Abc123!@...")
            login_response = client.post('/auth/login', data={
                'username_or_email': 'testuser',
                'password': 'Abc123!@'
            }, follow_redirects=False)
            
            print(f"📡 Login response status: {login_response.status_code}")
            
            # Count after login
            count_after_login = AuditLog.query.count()
            print(f"📊 Audit logs after login: {count_after_login}")
            print(f"📈 New logs from login: {count_after_login - count_before}")
            
            if login_response.status_code == 302:  # Redirect after successful login
                print("✅ Login successful!")
                
                # Show login audit entries
                login_logs = AuditLog.query.filter(
                    AuditLog.id > count_before
                ).order_by(AuditLog.timestamp.desc()).all()
                
                print(f"📝 Login audit entries:")
                for i, log in enumerate(login_logs, 1):
                    timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else 'N/A'
                    print(f"   {i}. [{timestamp}] {log.action_type.value}: {log.action_description}")
                
                # Now test logout
                print("\n🚪 Attempting logout...")
                logout_response = client.get('/auth/logout', follow_redirects=False)
                print(f"📡 Logout response status: {logout_response.status_code}")
                
                # Count after logout
                count_after_logout = AuditLog.query.count()
                print(f"📊 Audit logs after logout: {count_after_logout}")
                print(f"📈 New logs from logout: {count_after_logout - count_after_login}")
                
                # Show all new audit entries
                all_new_logs = AuditLog.query.filter(
                    AuditLog.id > count_before
                ).order_by(AuditLog.timestamp.desc()).all()
                
                print(f"\n📝 All new audit entries from this test:")
                for i, log in enumerate(all_new_logs, 1):
                    timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else 'N/A'
                    print(f"   {i}. [{timestamp}] {log.action_type.value}: {log.action_description}")
                
                # Test result summary
                total_new_logs = count_after_logout - count_before
                print(f"\n📊 Summary:")
                print(f"   - Total new audit logs: {total_new_logs}")
                print(f"   - Login logs: {count_after_login - count_before}")
                print(f"   - Logout logs: {count_after_logout - count_after_login}")
                
                if count_after_logout > count_after_login:
                    print("✅ SUCCESS: Logout audit logging is now working!")
                else:
                    print("❌ ISSUE: Logout audit logging still not working")
                
            else:
                print("❌ Login failed - checking if user exists...")
                
                # Check if test user exists
                from app.models import User
                test_user = User.query.filter_by(username='testuser').first()
                if test_user:
                    print(f"✅ Test user exists: {test_user.username} (active: {test_user.is_active})")
                    print("❌ Login failed - check password or other login logic")
                else:
                    print("❌ Test user 'testuser' does not exist in database")
                    print("📝 Available users:")
                    users = User.query.all()
                    for user in users:
                        print(f"   - {user.username} (active: {user.is_active})")
        
        return True

if __name__ == "__main__":
    print("🔬 Real Login/Logout Audit Test")
    print("=" * 50)
    test_real_login_logout()
