#!/usr/bin/env python3
"""
Test script to verify session service fixes
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.session_service import session_service

def test_session_service():
    """Test session service functionality"""
    app = create_app()
    
    with app.app_context():
        print("Testing session service...")
        
        # Test Redis connection
        if session_service.redis_client:
            try:
                session_service.redis_client.ping()
                print("✅ Redis connection successful")
            except Exception as e:
                print(f"❌ Redis connection failed: {e}")
                return False
        else:
            print("⚠️  Redis not configured")
        
        print("✅ Session service test completed")
        return True

if __name__ == '__main__':
    test_session_service()
