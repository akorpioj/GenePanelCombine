#!/usr/bin/env python3
"""
Enhanced Session Security Test Suite
Tests all aspects of the enhanced session management system
"""

import sys
import os
import time
import json
import requests

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_session_security():
    """Test enhanced session security features"""
    
    print("🔐 Enhanced Session Security Test Suite")
    print("=" * 60)
    
    # Test configuration
    base_url = "http://127.0.0.1:5000"  # Adjust if needed
    test_results = []
    
    def log_test(test_name, status, details=""):
        """Log test results"""
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {test_name}")
        if details:
            print(f"   {details}")
        test_results.append({
            'test': test_name,
            'status': status,
            'details': details
        })
    
    try:
        # Import Flask app for direct testing
        from app import create_app
        from app.session_service import session_service
        from app.models import User, db
        
        # Create test app
        app = create_app('testing')
        
        with app.app_context():
            # Test 1: Session Service Initialization
            try:
                assert session_service is not None, "Session service not initialized"
                log_test("Session Service Initialization", True, "Service properly initialized")
            except Exception as e:
                log_test("Session Service Initialization", False, str(e))
            
            # Test 2: Session Token Generation
            try:
                token1 = session_service._generate_session_token()
                token2 = session_service._generate_session_token()
                
                assert len(token1) == 64, f"Token length should be 64, got {len(token1)}"
                assert token1 != token2, "Tokens should be unique"
                assert session_service._is_valid_token_format(token1), "Token format should be valid"
                
                log_test("Session Token Generation", True, f"Generated unique 64-character tokens")
            except Exception as e:
                log_test("Session Token Generation", False, str(e))
            
            # Test 3: Session Creation (requires test user)
            try:
                # Create test user if not exists
                test_user = User.query.filter_by(username='test_session_user').first()
                if not test_user:
                    test_user = User(
                        username='test_session_user',
                        email='test_session@example.com',
                        first_name='Test',
                        last_name='User'
                    )
                    test_user.set_password('TestPassword123!')
                    db.session.add(test_user)
                    db.session.commit()
                
                # Test session creation with Flask request context
                with app.test_request_context('/', headers={'User-Agent': 'Test Agent'}):
                    from flask import session
                    
                    session_token = session_service.create_session(
                        user_id=test_user.id,
                        user_agent='Test Agent',
                        ip_address='127.0.0.1',
                        remember_me=False
                    )
                    
                    assert session_token is not None, "Session token should be created"
                    assert 'user_id' in session, "User ID should be in session"
                    assert session['user_id'] == test_user.id, "User ID should match"
                    
                    log_test("Session Creation", True, "Successfully created secure session")
            except Exception as e:
                log_test("Session Creation", False, str(e))
            
            # Test 4: Session Validation
            try:
                with app.test_request_context('/', headers={'User-Agent': 'Test Agent'}):
                    from flask import session
                    
                    # Set up a valid session
                    session['user_id'] = test_user.id
                    session['session_token'] = session_service._generate_session_token()
                    session['created_at'] = time.time()
                    session['last_activity'] = time.time()
                    session['user_agent_hash'] = session_service._hash_user_agent('Test Agent')
                    session['ip_address'] = '127.0.0.1'
                    
                    is_valid = session_service._validate_session()
                    assert is_valid, "Valid session should pass validation"
                    
                    log_test("Session Validation", True, "Session validation works correctly")
            except Exception as e:
                log_test("Session Validation", False, str(e))
            
            # Test 5: Session Hijacking Detection
            try:
                with app.test_request_context('/', headers={'User-Agent': 'Different Agent'}):
                    from flask import session
                    
                    # Set up session with different user agent
                    session['user_id'] = test_user.id
                    session['user_agent_hash'] = session_service._hash_user_agent('Original Agent')
                    session['ip_address'] = '127.0.0.1'
                    
                    hijacking_detected = not session_service._check_session_hijacking()
                    assert hijacking_detected, "Should detect user agent change"
                    
                    log_test("Session Hijacking Detection", True, "Successfully detects user agent changes")
            except Exception as e:
                log_test("Session Hijacking Detection", False, str(e))
            
            # Test 6: Session Timeout Check
            try:
                with app.test_request_context('/'):
                    from flask import session
                    
                    # Set up expired session
                    session['last_activity'] = time.time() - (session_service.session_timeout + 1)
                    
                    is_expired = session_service._is_session_expired()
                    assert is_expired, "Old session should be expired"
                    
                    # Set up active session
                    session['last_activity'] = time.time()
                    is_expired = session_service._is_session_expired()
                    assert not is_expired, "Current session should not be expired"
                    
                    log_test("Session Timeout Check", True, "Timeout detection works correctly")
            except Exception as e:
                log_test("Session Timeout Check", False, str(e))
            
            # Test 7: Session Rotation
            try:
                with app.test_request_context('/'):
                    from flask import session
                    
                    # Set up session that needs rotation
                    session['session_rotated_at'] = time.time() - (session_service.session_rotation_interval + 1)
                    
                    should_rotate = session_service._should_rotate_session()
                    assert should_rotate, "Old session should need rotation"
                    
                    log_test("Session Rotation Logic", True, "Rotation timing works correctly")
            except Exception as e:
                log_test("Session Rotation Logic", False, str(e))
            
            # Test 8: Privilege Escalation
            try:
                with app.test_request_context('/'):
                    from flask import session
                    
                    # Set up session
                    session['user_id'] = test_user.id
                    session['session_token'] = session_service._generate_session_token()
                    session['privilege_level'] = 'user'
                    session['session_rotated_at'] = time.time()
                    
                    result = session_service.escalate_privileges('admin')
                    assert result, "Privilege escalation should succeed"
                    assert session['privilege_level'] == 'admin', "Privilege level should be updated"
                    
                    log_test("Privilege Escalation", True, "Successfully handles privilege changes")
            except Exception as e:
                log_test("Privilege Escalation", False, str(e))
            
            # Test 9: Session Destruction
            try:
                with app.test_request_context('/'):
                    from flask import session
                    
                    # Set up session
                    session['user_id'] = test_user.id
                    session['session_token'] = session_service._generate_session_token()
                    
                    session_service.destroy_session()
                    
                    assert 'user_id' not in session, "Session should be cleared"
                    
                    log_test("Session Destruction", True, "Successfully destroys sessions")
            except Exception as e:
                log_test("Session Destruction", False, str(e))
            
            # Test 10: Configuration Validation
            try:
                assert hasattr(session_service, 'session_timeout'), "Should have session timeout"
                assert hasattr(session_service, 'max_concurrent_sessions'), "Should have concurrent session limit"
                assert hasattr(session_service, 'session_rotation_interval'), "Should have rotation interval"
                
                log_test("Configuration Validation", True, "All configuration parameters present")
            except Exception as e:
                log_test("Configuration Validation", False, str(e))
    
    except ImportError as e:
        log_test("App Import", False, f"Failed to import app: {e}")
        print("\n❌ Cannot run tests - app import failed")
        print("Make sure you're running this from the project root directory")
        return
    
    # Print summary
    print("\n" + "=" * 60)
    passed = sum(1 for result in test_results if result['status'])
    total = len(test_results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"📊 Test Results Summary:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {total - passed}")
    print(f"   📈 Total Tests: {total}")
    print(f"   🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 All enhanced session security tests passed! Your session management")
        print("   system is working correctly with enterprise-grade security features.")
    else:
        print(f"\n⚠️  Some tests failed. Please review the implementation.")
        
        # Show failed tests
        failed_tests = [r for r in test_results if not r['status']]
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")

def main():
    """Main test function"""
    test_session_security()

if __name__ == "__main__":
    main()
