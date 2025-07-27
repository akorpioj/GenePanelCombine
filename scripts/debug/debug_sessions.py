#!/usr/bin/env python3
"""
Debug script to check session storage and retrieval
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.session_service import session_service
from flask import session

def debug_sessions():
    """Debug session functionality"""
    app = create_app()
    
    with app.app_context():
        with app.test_request_context():
            print("=== Session Service Debug ===")
            
            # Check Redis connection
            if session_service.redis_client:
                try:
                    session_service.redis_client.ping()
                    print("✅ Redis connection successful")
                    
                    # Check if there are any user sessions in Redis
                    redis_keys = session_service.redis_client.keys("user_sessions:*")
                    print(f"📊 Found {len(redis_keys)} user session keys in Redis")
                    
                    for key in redis_keys[:5]:  # Show first 5 keys
                        user_id = key.split(':')[1]
                        sessions = session_service.redis_client.smembers(key)
                        print(f"   User {user_id}: {len(sessions)} sessions")
                        
                        # Check first session data
                        if sessions:
                            first_session = list(sessions)[0]
                            session_data = session_service._get_session_from_redis(first_session)
                            if session_data:
                                print(f"     Sample session data keys: {list(session_data.keys())}")
                            else:
                                print(f"     Could not retrieve session data for {first_session[:8]}...")
                    
                    # Check general session keys
                    session_keys = session_service.redis_client.keys("session:*")
                    print(f"📊 Found {len(session_keys)} session data keys in Redis")
                    
                except Exception as e:
                    print(f"❌ Redis error: {e}")
                    return False
            else:
                print("⚠️  Redis not configured")
                return False
            
            print("✅ Session debug completed")
            return True

if __name__ == '__main__':
    debug_sessions()
