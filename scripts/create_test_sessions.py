#!/usr/bin/env python3
"""
Test script to create multiple sessions for testing revocation
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.session_service import session_service

def create_test_sessions():
    """Create multiple test sessions for testing revocation"""
    app = create_app()
    
    with app.test_request_context():
        print("=== Creating Test Sessions ===")
        
        # Check if we have a Redis connection
        if not session_service.redis_client:
            print("❌ No Redis connection available")
            return False
        
        try:
            # Create multiple sessions for user ID 7 (adjust as needed)
            test_user_id = 7
            
            # Create session 1
            session1 = session_service.create_session(
                user_id=test_user_id,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome Test 1",
                ip_address="192.168.1.100",
                remember_me=False
            )
            print(f"✅ Created session 1: {session1[:8]}...")
            
            # Create session 2
            session2 = session_service.create_session(
                user_id=test_user_id,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox Test 2",
                ip_address="192.168.1.101",
                remember_me=True
            )
            print(f"✅ Created session 2: {session2[:8]}...")
            
            # Create session 3
            session3 = session_service.create_session(
                user_id=test_user_id,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari Test 3",
                ip_address="192.168.1.102",
                remember_me=False
            )
            print(f"✅ Created session 3: {session3[:8]}...")
            
            # Verify sessions were created
            user_sessions = session_service.get_user_sessions(test_user_id)
            print(f"📊 User {test_user_id} now has {len(user_sessions)} sessions")
            
            for i, session in enumerate(user_sessions, 1):
                print(f"   Session {i}: {session['session_id']} - {session['user_agent'][:50]}...")
            
            print("✅ Test sessions created successfully!")
            print(f"💡 You can now test individual session revocation for user {test_user_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating test sessions: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False

if __name__ == '__main__':
    create_test_sessions()
