#!/usr/bin/env python3
"""
Test script to trigger a real logout and see debug logs
"""
import sys
import os

# Add the parent directory to the path to import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

def test_real_logout():
    """Test a real logout process"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing real logout with debug logging...")
        
        # Create a test client
        client = app.test_client()
        
        print("🔐 Attempting login...")
        # Login first
        login_response = client.post('/auth/login', data={
            'username_or_email': 'admin',
            'password': 'Admin123!'
        }, follow_redirects=False)
        
        print(f"📡 Login response status: {login_response.status_code}")
        
        if login_response.status_code in [200, 302]:
            print("✅ Login successful, now testing logout...")
            
            # Now logout
            logout_response = client.get('/auth/logout', follow_redirects=False)
            print(f"📡 Logout response status: {logout_response.status_code}")
            
            if logout_response.status_code == 302:
                print("✅ Logout completed successfully")
            else:
                print(f"❌ Unexpected logout response: {logout_response.status_code}")
        else:
            print("❌ Login failed, cannot test logout")

if __name__ == "__main__":
    print("🔬 Real Logout Audit Test")
    print("=" * 50)
    test_real_logout()
