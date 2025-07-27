#!/usr/bin/env python3
"""
Test script for the audit logging system
"""
import sys
import os

# Add the parent directory to the path to import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, AuditLog, AuditActionType
from app.audit_service import AuditService

def test_audit_logging():
    """Test the audit logging functionality"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🧪 Testing audit logging system...")
            
            # Test basic logging
            log_entry = AuditService.log_action(
                action_type=AuditActionType.ADMIN_ACTION,
                action_description="Testing audit system - admin test action",
                resource_type="system",
                resource_id="test",
                details={"test": True, "component": "audit_system"},
                success=True
            )
            
            if log_entry:
                print("✅ Basic audit logging test passed!")
                print(f"   Created log entry with ID: {log_entry.id}")
                print(f"   Action: {log_entry.action_type.value}")
                print(f"   Description: {log_entry.action_description}")
                print(f"   Timestamp: {log_entry.timestamp}")
            else:
                print("❌ Basic audit logging test failed!")
                return False
            
            # Test search logging
            search_log = AuditService.log_search("BRCA1", results_count=5)
            if search_log:
                print("✅ Search logging test passed!")
            else:
                print("❌ Search logging test failed!")
                return False
            
            # Test error logging
            error_log = AuditService.log_error(
                error_description="Test error logging",
                error_message="This is a test error message",
                resource_type="test",
                resource_id="error_test"
            )
            if error_log:
                print("✅ Error logging test passed!")
            else:
                print("❌ Error logging test failed!")
                return False
            
            # Check total count
            total_logs = AuditLog.query.count()
            print(f"📊 Total audit logs in database: {total_logs}")
            
            # Show recent logs
            recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(3).all()
            print(f"📝 Recent audit entries:")
            for i, log in enumerate(recent_logs, 1):
                print(f"   {i}. {log.action_type.value}: {log.action_description}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing audit system: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_audit_logging()
    
    if success:
        print("\n🎉 All audit logging tests passed!")
        print("The audit trail system is working correctly.")
    else:
        print("\n💥 Some audit logging tests failed.")
        sys.exit(1)
