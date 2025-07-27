#!/usr/bin/env python3
"""
Simple test to check if logout route is being reached
"""
import sys
import os

# Add the parent directory to the path to import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, AuditLog, User

def test_logout_route_access():
    """Test if logout route is accessible"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing logout route accessibility...")
        
        with app.test_client() as client:
            # First, try to login
            print("🔐 Attempting login...")
            login_response = client.post('/auth/login', data={
                'username_or_email': 'admin',
                'password': 'Admin123!'
            }, follow_redirects=False)
            
            print(f"📡 Login response status: {login_response.status_code}")
            
            if login_response.status_code == 302:  # Redirect means success
                print("✅ Login appears successful, now testing logout...")
                
                # Count audit logs before logout
                count_before = AuditLog.query.count()
                print(f"📊 Audit logs before logout: {count_before}")
                
                # Now try logout
                print("🚪 Attempting logout...")
                logout_response = client.get('/auth/logout', follow_redirects=False)
                print(f"📡 Logout response status: {logout_response.status_code}")
                
                # Count audit logs after logout
                count_after = AuditLog.query.count()
                print(f"📊 Audit logs after logout: {count_after}")
                print(f"📈 New logs created: {count_after - count_before}")
                
                return True
            else:
                print("❌ Login failed, cannot test logout")
                return False

if __name__ == "__main__":
    print("🔬 Simple Logout Route Test")
    print("=" * 40)
    test_logout_route_access()
