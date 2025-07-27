#!/usr/bin/env python3
"""
Debug script to test session retrieval for current user
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.session_service import session_service
from flask import session
from flask_login import current_user

def debug_current_user_sessions():
    """Debug session retrieval for current user"""
    app = create_app()
    
    with app.test_request_context():
        with app.test_client() as client:
            print("=== Current User Session Debug ===")
            
            # Check if we have a Redis connection
            if not session_service.redis_client:
                print("❌ No Redis connection available")
                return False
            
            try:
                # Get all user session keys
                user_keys = session_service.redis_client.keys("user_sessions:*")
                print(f"📊 Found {len(user_keys)} user session keys in Redis")
                
                for key in user_keys:
                    user_id = key.split(':')[1]
                    sessions = session_service.redis_client.smembers(key)
                    print(f"   User {user_id}: {len(sessions)} sessions")
                    
                    # Test the get_user_sessions method
                    try:
                        user_sessions = session_service.get_user_sessions(int(user_id))
                        print(f"     get_user_sessions returned: {len(user_sessions)} sessions")
                        if user_sessions:
                            print(f"     Sample session: {user_sessions[0]}")
                        else:
                            print("     ⚠️  No sessions returned by get_user_sessions")
                            
                            # Debug why no sessions are returned
                            for token in sessions:
                                session_data = session_service._get_session_from_redis(token)
                                if session_data:
                                    created_at = session_data.get('created_at')
                                    last_activity = session_data.get('last_activity')
                                    print(f"       Token {token[:8]}...: created_at={created_at}, last_activity={last_activity}")
                                    if not created_at or not last_activity:
                                        print(f"       ❌ Missing timestamp data")
                                else:
                                    print(f"       ❌ Could not retrieve session data for {token[:8]}...")
                                    
                    except Exception as e:
                        print(f"     ❌ Error calling get_user_sessions: {e}")
                        import traceback
                        print(f"     Traceback: {traceback.format_exc()}")
                
                return True
                
            except Exception as e:
                print(f"❌ Error during debug: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                return False

if __name__ == '__main__':
    debug_current_user_sessions()
