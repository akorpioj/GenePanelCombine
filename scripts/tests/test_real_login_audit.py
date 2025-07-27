#!/usr/bin/env python3
"""
Test script to debug why actual login/logout isn't creating audit logs
"""
import sys
import os

# Add the parent directory to the path to import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, AuditLog, User

def test_actual_login_logout():
    """Test actual login/logout process"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🧪 Testing actual login/logout process...")
            
            # Count logs before
            count_before = AuditLog.query.count()
            print(f"📊 Audit logs before: {count_before}")
            
            # Create test client
            client = app.test_client()
            
            # Test login attempt
            print("🔐 Attempting login via HTTP...")
            response = client.post('/auth/login', data={
                'username_or_email': 'admin',
                'password': 'wrong_password'
            }, follow_redirects=False)
            
            print(f"📡 Login response status: {response.status_code}")
            
            # Check if audit log was created
            count_after_login = AuditLog.query.count()
            print(f"📊 Audit logs after login attempt: {count_after_login}")
            print(f"📈 New logs from login: {count_after_login - count_before}")
            
            # Show any new logs
            if count_after_login > count_before:
                new_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(count_after_login - count_before).all()
                print("📝 New audit entries:")
                for i, log in enumerate(new_logs, 1):
                    timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else 'N/A'
                    print(f"   {i}. [{timestamp}] {log.action_type.value}: {log.action_description}")
            
            # Test with existing user
            print("\n🔍 Checking if admin user exists...")
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                print(f"✅ Admin user found: {admin_user.username} (active: {admin_user.is_active})")
                
                # Try login with correct password (if we know it)
                print("🔐 Attempting login with admin user...")
                response2 = client.post('/auth/login', data={
                    'username_or_email': 'admin',
                    'password': 'Admin123!'  # Default password from setup
                }, follow_redirects=False)
                
                print(f"📡 Admin login response status: {response2.status_code}")
                
                # Check logs again
                count_after_admin = AuditLog.query.count()
                print(f"📊 Audit logs after admin login: {count_after_admin}")
                print(f"📈 New logs from admin login: {count_after_admin - count_after_login}")
                
                if count_after_admin > count_after_login:
                    new_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(count_after_admin - count_after_login).all()
                    print("📝 New audit entries from admin login:")
                    for i, log in enumerate(new_logs, 1):
                        timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else 'N/A'
                        print(f"   {i}. [{timestamp}] {log.action_type.value}: {log.action_description}")
                
                # Test logout
                print("\n🚪 Attempting logout...")
                response3 = client.get('/auth/logout', follow_redirects=False)
                print(f"📡 Logout response status: {response3.status_code}")
                
                # Check logs after logout
                count_after_logout = AuditLog.query.count()
                print(f"📊 Audit logs after logout: {count_after_logout}")
                print(f"📈 New logs from logout: {count_after_logout - count_after_admin}")
                
                if count_after_logout > count_after_admin:
                    new_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(count_after_logout - count_after_admin).all()
                    print("📝 New audit entries from logout:")
                    for i, log in enumerate(new_logs, 1):
                        timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else 'N/A'
                        print(f"   {i}. [{timestamp}] {log.action_type.value}: {log.action_description}")
            else:
                print("❌ No admin user found")
                
                # Show all users
                users = User.query.all()
                print(f"📋 Available users ({len(users)}):")
                for user in users:
                    print(f"   - {user.username} ({user.email}) - Active: {user.is_active}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing actual login/logout: {e}")
            import traceback
            traceback.print_exc()
            return False

def check_audit_route_imports():
    """Check if the audit service is properly imported in auth routes"""
    try:
        print("\n🔍 Checking auth routes imports...")
        
        # Try to import the auth routes module
        from app.auth.routes import AuditService
        print("✅ AuditService successfully imported in auth routes")
        
        # Check if the methods exist
        if hasattr(AuditService, 'log_login'):
            print("✅ log_login method exists")
        else:
            print("❌ log_login method missing")
            
        if hasattr(AuditService, 'log_logout'):
            print("✅ log_logout method exists") 
        else:
            print("❌ log_logout method missing")
            
        return True
        
    except ImportError as e:
        print(f"❌ Import error in auth routes: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking imports: {e}")
        return False

if __name__ == "__main__":
    print("🔬 Debug Actual Login/Logout Audit Logging")
    print("=" * 60)
    
    success1 = check_audit_route_imports()
    success2 = test_actual_login_logout()
    
    if success1 and success2:
        print("\n🎉 Debug test completed!")
    else:
        print("\n💥 Some issues were found!")
