#!/usr/bin/env python3
"""
Test script to specifically debug logout audit logging
"""
import sys
import os

# Add the parent directory to the path to import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, AuditLog, AuditActionType, User
from app.audit_service import AuditService

def test_logout_audit():
    """Test logout audit logging specifically"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing logout audit logging specifically...")
        
        # Count before
        count_before = AuditLog.query.count()
        print(f"📊 Audit logs before test: {count_before}")
        
        # Test direct audit logging
        print("🔍 Testing direct audit logging...")
        result1 = AuditService.log_logout("test_user")
        print(f"✅ Direct logout logging result: {result1 is not None}")
        
        # Test with request context
        print("🌐 Testing with request context...")
        with app.test_request_context('/auth/logout', method='GET'):
            result2 = AuditService.log_logout("test_user_with_context")
            print(f"✅ Request context logout logging result: {result2 is not None}")
        
        # Test with full Flask login context
        print("👤 Testing with user authentication context...")
        with app.test_request_context('/auth/logout', method='GET'):
            # Find a user to test with
            test_user = User.query.first()
            if test_user:
                print(f"📝 Testing with user: {test_user.username}")
                result3 = AuditService.log_logout(test_user.username)
                print(f"✅ User context logout logging result: {result3 is not None}")
            else:
                print("❌ No users found in database")
        
        # Count after
        count_after = AuditLog.query.count()
        print(f"📊 Audit logs after test: {count_after}")
        print(f"📈 New logs created: {count_after - count_before}")
        
        # Show recent logs
        recent_logs = AuditLog.query.filter(
            AuditLog.action_type == AuditActionType.LOGOUT
        ).order_by(AuditLog.timestamp.desc()).limit(5).all()
        
        print(f"📝 Recent logout audit entries:")
        for i, log in enumerate(recent_logs, 1):
            timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else 'N/A'
            print(f"   {i}. [{timestamp}] {log.action_description}")
        
        return count_after > count_before

def test_audit_service_error_handling():
    """Test if audit service has any error handling issues"""
    app = create_app()
    
    with app.app_context():
        print("\n🔧 Testing audit service error handling...")
        
        try:
            # Test with various parameters
            result = AuditService.log_action(
                action_type=AuditActionType.LOGOUT,
                action_description="Test logout with explicit parameters",
                resource_type="user",
                resource_id="test_user",
                success=True,
                user_id=None,  # No current user
                ip_address="127.0.0.1"
            )
            print(f"✅ Explicit parameter test: {result is not None}")
            
            # Test if the database transaction works
            if result:
                print(f"✅ Audit log ID: {result.id}")
                
                # Verify it's actually in database
                db_result = AuditLog.query.get(result.id)
                print(f"✅ Database verification: {db_result is not None}")
                
            return True
            
        except Exception as e:
            print(f"❌ Error in audit service test: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🔬 Logout Audit Debug Test")
    print("=" * 50)
    
    success1 = test_logout_audit()
    success2 = test_audit_service_error_handling()
    
    if success1 and success2:
        print("\n🎉 Logout audit tests passed!")
    else:
        print("\n💥 Some logout audit tests failed!")
