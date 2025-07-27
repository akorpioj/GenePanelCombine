#!/usr/bin/env python3
"""
Test script to debug audit logging integration issues
"""
import sys
import os

# Add the parent directory to the path to import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, AuditLog, AuditActionType
from app.audit_service import AuditService

def test_audit_in_request_context():
    """Test audit logging within a request context"""
    app = create_app()
    
    with app.app_context():
        with app.test_request_context('/', base_url='http://localhost'):
            try:
                print("🧪 Testing audit logging in request context...")
                
                # Count before
                count_before = AuditLog.query.count()
                print(f"📊 Audit logs before test: {count_before}")
                
                # Test login logging
                print("🔐 Testing login audit logging...")
                result = AuditService.log_login("test_user", success=True)
                
                if result:
                    print("✅ Login audit log created successfully")
                else:
                    print("❌ Failed to create login audit log")
                
                # Test logout logging
                print("🚪 Testing logout audit logging...")
                result = AuditService.log_logout("test_user")
                
                if result:
                    print("✅ Logout audit log created successfully")
                else:
                    print("❌ Failed to create logout audit log")
                
                # Count after
                count_after = AuditLog.query.count()
                print(f"📊 Audit logs after test: {count_after}")
                print(f"📈 New logs created: {count_after - count_before}")
                
                # Show recent logs
                recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(5).all()
                print(f"📝 Recent audit entries:")
                for i, log in enumerate(recent_logs, 1):
                    timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else 'N/A'
                    print(f"   {i}. [{timestamp}] {log.action_type.value}: {log.action_description}")
                
                return True
                
            except Exception as e:
                print(f"❌ Error testing audit in request context: {e}")
                import traceback
                traceback.print_exc()
                return False

def check_audit_service_logs():
    """Check if there are any logging errors in the audit service"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n🔍 Checking audit service error handling...")
            
            # Test with invalid data to see error handling
            print("🧪 Testing error scenarios...")
            
            # This should work
            result1 = AuditService.log_action(
                action_type=AuditActionType.LOGIN,
                action_description="Debug test login",
                success=True
            )
            print(f"✅ Normal log action result: {result1 is not None}")
            
            # Test edge cases
            result2 = AuditService.log_action(
                action_type=AuditActionType.LOGOUT,
                action_description="Debug test logout",
                success=True,
                user_id=None,  # No user ID
                ip_address="127.0.0.1"
            )
            print(f"✅ No user ID log action result: {result2 is not None}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in audit service check: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🔬 Debug Audit Integration Test")
    print("=" * 50)
    
    success1 = test_audit_in_request_context()
    success2 = check_audit_service_logs()
    
    if success1 and success2:
        print("\n🎉 All audit integration tests passed!")
    else:
        print("\n💥 Some audit integration tests failed!")
