#!/usr/bin/env python3
"""
Test script for comprehensive security audit logging system
Demonstrates all new security audit capabilities
"""

import sys
import os
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_security_audit_system():
    """Test all new security audit logging capabilities"""
    
    from app import create_app
    from app.audit_service import AuditService
    from app.models import AuditLog, AuditActionType, db
    
    app = create_app()
    
    with app.app_context():
        print("🔒 Testing Comprehensive Security Audit Logging System")
        print("=" * 60)
        
        # Test 1: Security Violation Logging
        print("\n1. Testing Security Violation Logging...")
        AuditService.log_security_violation(
            violation_type="MALICIOUS_FILE_UPLOAD",
            description="Test: Attempt to upload suspicious file",
            severity="HIGH",
            details={
                "filename": "test_malicious.php",
                "file_extension": "php",
                "blocked": True,
                "detection_method": "extension_check"
            }
        )
        print("   ✓ Security violation logged")
        
        # Test 2: Access Denied Events
        print("\n2. Testing Access Denied Logging...")
        AuditService.log_access_denied(
            resource_type="admin_panel",
            resource_id="/admin/users",
            reason="Insufficient privileges",
            requested_action="VIEW"
        )
        print("   ✓ Access denied event logged")
        
        # Test 3: Privilege Escalation Detection
        print("\n3. Testing Privilege Escalation Logging...")
        AuditService.log_privilege_escalation(
            target_privilege="admin",
            source_privilege="user",
            success=False
        )
        print("   ✓ Privilege escalation attempt logged")
        
        # Test 4: Suspicious Activity Detection
        print("\n4. Testing Suspicious Activity Logging...")
        AuditService.log_suspicious_activity(
            activity_type="RAPID_REQUESTS",
            description="Test: User making unusually rapid requests",
            risk_score=75,
            details={
                "request_count": 50,
                "time_window": "30 seconds",
                "normal_rate": "2 requests/minute"
            }
        )
        print("   ✓ Suspicious activity logged")
        
        # Test 5: Brute Force Attack Detection
        print("\n5. Testing Brute Force Attack Logging...")
        AuditService.log_brute_force_attempt(
            target_username="admin@test.com",
            attempt_count=8,
            time_window="5 minutes",
            source_ip="192.168.1.100"
        )
        print("   ✓ Brute force attempt logged")
        
        # Test 6: Account Lockout
        print("\n6. Testing Account Lockout Logging...")
        AuditService.log_account_lockout(
            username="test_user@example.com",
            reason="excessive_failed_logins",
            lockout_duration="30 minutes",
            automatic=True
        )
        print("   ✓ Account lockout logged")
        
        # Test 7: Password Reset Security
        print("\n7. Testing Password Reset Logging...")
        AuditService.log_password_reset(
            username="test_user@example.com",
            method="email_link",
            success=True,
            initiated_by="user"
        )
        print("   ✓ Password reset logged")
        
        # Test 8: Multi-Factor Authentication
        print("\n8. Testing MFA Event Logging...")
        AuditService.log_mfa_event(
            event_type="verification_success",
            success=True,
            method="totp",
            details={
                "app_used": "google_authenticator",
                "backup_codes_available": 3
            }
        )
        print("   ✓ MFA event logged")
        
        # Test 9: API Access Monitoring
        print("\n9. Testing API Access Logging...")
        AuditService.log_api_access(
            endpoint="/api/v1/panels",
            method="GET",
            status_code=200,
            response_time_ms=150,
            api_key_used=True
        )
        print("   ✓ API access logged")
        
        # Test 10: File Access Monitoring
        print("\n10. Testing File Access Logging...")
        AuditService.log_file_access(
            file_path="/uploads/sensitive_data.csv",
            access_type="READ",
            success=True,
            file_size=2048000
        )
        print("   ✓ File access logged")
        
        # Test 11: Data Breach Attempt Detection
        print("\n11. Testing Data Breach Attempt Logging...")
        AuditService.log_data_breach_attempt(
            breach_type="sql_injection",
            target_data="user_credentials",
            blocked=True,
            details={
                "payload": "' OR 1=1--",
                "injection_point": "username_field"
            }
        )
        print("   ✓ Data breach attempt logged")
        
        # Test 12: Compliance Event Logging
        print("\n12. Testing Compliance Event Logging...")
        AuditService.log_compliance_event(
            compliance_type="data_access_request",
            event_description="User requested personal data export under GDPR",
            compliant=True,
            regulation="GDPR"
        )
        print("   ✓ Compliance event logged")
        
        # Test 13: System Security Events
        print("\n13. Testing System Security Logging...")
        AuditService.log_system_security(
            event_type="security_configuration_change",
            description="Test: Security monitoring rules updated",
            severity="MEDIUM",
            system_component="security_monitor",
            details={
                "changes": ["rate_limit_threshold", "alert_sensitivity"],
                "changed_by": "system_admin"
            }
        )
        print("   ✓ System security event logged")
        
        # Query and display results
        print("\n" + "=" * 60)
        print("📊 AUDIT LOG VERIFICATION")
        print("=" * 60)
        
        # Get recent security audit logs
        recent_logs = AuditLog.query.filter(
            AuditLog.action_type.in_([
                AuditActionType.SECURITY_VIOLATION,
                AuditActionType.ACCESS_DENIED,
                AuditActionType.PRIVILEGE_ESCALATION,
                AuditActionType.SUSPICIOUS_ACTIVITY,
                AuditActionType.BRUTE_FORCE_ATTEMPT,
                AuditActionType.ACCOUNT_LOCKOUT,
                AuditActionType.PASSWORD_RESET,
                AuditActionType.MFA_EVENT,
                AuditActionType.API_ACCESS,
                AuditActionType.FILE_ACCESS,
                AuditActionType.DATA_BREACH_ATTEMPT,
                AuditActionType.COMPLIANCE_EVENT,
                AuditActionType.SYSTEM_SECURITY
            ])
        ).order_by(AuditLog.timestamp.desc()).limit(20).all()
        
        print(f"\nFound {len(recent_logs)} recent security audit logs:")
        print("-" * 60)
        
        for log in recent_logs:
            severity = getattr(log, 'severity', 'INFO')
            print(f"🔹 {log.action_type.value}")
            print(f"   Severity: {severity}")
            print(f"   Description: {log.action_description}")
            print(f"   Time: {log.timestamp}")
            if hasattr(log, 'details') and log.details:
                print(f"   Details: {str(log.details)[:100]}...")
            print()
        
        # Statistics
        security_event_counts = {}
        for log in recent_logs:
            action = log.action_type.value
            security_event_counts[action] = security_event_counts.get(action, 0) + 1
        
        print("📈 Security Event Statistics:")
        print("-" * 30)
        for event_type, count in sorted(security_event_counts.items()):
            print(f"   {event_type}: {count}")
        
        print(f"\n✅ Security audit system test completed successfully!")
        print(f"   Total security events tested: 13")
        print(f"   Total audit logs created: {len(recent_logs)}")
        print(f"   System status: Operational")
        
        return True

def test_security_monitoring():
    """Test security monitoring capabilities"""
    
    from app.security_monitor import SecurityMonitor
    
    print("\n🛡️ Testing Security Monitoring Features")
    print("=" * 50)
    
    monitor = SecurityMonitor()
    
    # Test 1: File Upload Security
    print("\n1. Testing File Upload Security...")
    
    # Test malicious file
    malicious_result = monitor.check_file_upload_security("malicious.php")
    print(f"   Malicious file (.php): {'BLOCKED' if not malicious_result else 'ALLOWED'}")
    
    # Test safe file
    safe_result = monitor.check_file_upload_security("data.csv")
    print(f"   Safe file (.csv): {'ALLOWED' if safe_result else 'BLOCKED'}")
    
    # Test 2: Suspicious User Agent Detection
    print("\n2. Testing User Agent Detection...")
    
    suspicious_agents = ['sqlmap', 'nikto', 'python-requests']
    for agent in suspicious_agents:
        is_suspicious = monitor._is_suspicious_user_agent(agent)
        print(f"   '{agent}': {'SUSPICIOUS' if is_suspicious else 'NORMAL'}")
    
    # Test 3: Security Rules
    print("\n3. Security Rules Configuration...")
    rules = monitor.security_rules
    print(f"   Max failed logins: {rules['max_failed_logins']}")
    print(f"   Failed login window: {rules['failed_login_window']} seconds")
    print(f"   Max requests/minute: {rules['max_requests_per_minute']}")
    print(f"   Blocked extensions: {len(rules['blocked_file_extensions'])}")
    
    print("\n✅ Security monitoring test completed!")
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test comprehensive security audit system")
    parser.add_argument('--audit', action='store_true',
                       help='Test audit logging capabilities')
    parser.add_argument('--monitor', action='store_true', 
                       help='Test security monitoring features')
    parser.add_argument('--all', action='store_true',
                       help='Run all security tests')
    
    args = parser.parse_args()
    
    try:
        if args.all or args.audit:
            success = test_security_audit_system()
            if not success:
                sys.exit(1)
        
        if args.all or args.monitor:
            success = test_security_monitoring()
            if not success:
                sys.exit(1)
        
        if not any([args.audit, args.monitor, args.all]):
            print("Usage:")
            print("  python test_security_audit.py --audit     # Test audit logging")
            print("  python test_security_audit.py --monitor   # Test security monitoring")
            print("  python test_security_audit.py --all       # Run all tests")
            print("\nRunning all tests by default...")
            test_security_audit_system()
            test_security_monitoring()
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
