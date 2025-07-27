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

def check_audit_logging():
    """Test the audit logging functionality"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🧪 Checking audit logging system...")
                        
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
            print(f"❌ Error checking audit system: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    check_audit_logging()
    