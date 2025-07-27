#!/usr/bin/env python3
"""
Test script to verify all AuditActionType implementations
"""
import sys
import os

# Add the parent directory to the path to import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, AuditLog, AuditActionType
from app.audit_service import AuditService

def test_all_audit_implementations():
    """Test that all AuditActionType values have working implementations"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing all AuditActionType implementations...")
        
        # Count before
        count_before = AuditLog.query.count()
        print(f"📊 Audit logs before tests: {count_before}")
        
        test_results = {}
        
        # Test each action type
        try:
            # LOGIN
            result = AuditService.log_login("test_user", success=True)
            test_results['LOGIN'] = result is not None
            
            # LOGOUT  
            result = AuditService.log_logout("test_user")
            test_results['LOGOUT'] = result is not None
            
            # REGISTER
            result = AuditService.log_registration("test_user", "test@example.com", success=True)
            test_results['REGISTER'] = result is not None
            
            # PASSWORD_CHANGE
            result = AuditService.log_password_change("test_user", success=True)
            test_results['PASSWORD_CHANGE'] = result is not None
            
            # PROFILE_UPDATE
            old_data = {"name": "Old Name"}
            new_data = {"name": "New Name"}
            result = AuditService.log_profile_update(1, "test_user", old_data, new_data)
            test_results['PROFILE_UPDATE'] = result is not None
            
            # PANEL_DOWNLOAD
            result = AuditService.log_panel_download("123,456", "diagnostic", 100)
            test_results['PANEL_DOWNLOAD'] = result is not None
            
            # PANEL_UPLOAD
            result = AuditService.log_panel_upload("test_panel.csv", 50, success=True)
            test_results['PANEL_UPLOAD'] = result is not None
            
            # PANEL_DELETE
            result = AuditService.log_panel_delete("test_panel_123", "Test Panel")
            test_results['PANEL_DELETE'] = result is not None
            
            # SEARCH
            result = AuditService.log_search("BRCA1", results_count=10)
            test_results['SEARCH'] = result is not None
            
            # VIEW
            result = AuditService.log_view("panel", "123", "Viewed panel details")
            test_results['VIEW'] = result is not None
            
            # CACHE_CLEAR
            result = AuditService.log_cache_clear("panel_cache")
            test_results['CACHE_CLEAR'] = result is not None
            
            # ADMIN_ACTION
            result = AuditService.log_admin_action("Test admin action", target_user_id=1)
            test_results['ADMIN_ACTION'] = result is not None
            
            # USER_CREATE
            result = AuditService.log_user_create("new_user", "new@example.com", "USER", created_by_admin=True)
            test_results['USER_CREATE'] = result is not None
            
            # USER_UPDATE
            changes = {"role": "ADMIN"}
            old_values = {"role": "USER"}
            result = AuditService.log_user_update(1, "test_user", changes, old_values)
            test_results['USER_UPDATE'] = result is not None
            
            # USER_DELETE
            result = AuditService.log_user_delete(1, "test_user")
            test_results['USER_DELETE'] = result is not None
            
            # ROLE_CHANGE
            result = AuditService.log_role_change(1, "test_user", "USER", "ADMIN")
            test_results['ROLE_CHANGE'] = result is not None
            
            # DATA_EXPORT
            result = AuditService.log_data_export("audit_logs", 100, "export.csv")
            test_results['DATA_EXPORT'] = result is not None
            
            # CONFIG_CHANGE
            result = AuditService.log_config_change("max_panels", 10, 20)
            test_results['CONFIG_CHANGE'] = result is not None
            
            # ERROR
            result = AuditService.log_error("Test error", "This is a test error")
            test_results['ERROR'] = result is not None
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Count after
        count_after = AuditLog.query.count()
        new_logs = count_after - count_before
        
        print(f"📊 Audit logs after tests: {count_after}")
        print(f"📈 New logs created: {new_logs}")
        
        # Report results
        print("\n📋 Implementation Status:")
        all_action_types = [action.value for action in AuditActionType]
        
        passed = 0
        failed = 0
        
        for action_type in all_action_types:
            status = "✅" if test_results.get(action_type, False) else "❌"
            result_text = "PASS" if test_results.get(action_type, False) else "FAIL"
            print(f"   {status} {action_type}: {result_text}")
            
            if test_results.get(action_type, False):
                passed += 1
            else:
                failed += 1
        
        print(f"\n📊 Summary:")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📈 Total Tests: {len(all_action_types)}")
        print(f"   🎯 Success Rate: {(passed/len(all_action_types)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 All AuditActionType implementations are working!")
            return True
        else:
            print(f"\n💥 {failed} AuditActionType implementations need attention!")
            return False

if __name__ == "__main__":
    print("🔬 Comprehensive Audit Implementation Test")
    print("=" * 60)
    
    success = test_all_audit_implementations()
    
    if success:
        print("\n🎉 All audit implementations are complete and working!")
    else:
        print("\n💥 Some audit implementations need to be fixed.")
        sys.exit(1)
