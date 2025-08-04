#!/usr/bin/env python3
"""
Check current enum values in the database for AuditActionType and ChangeType
This script queries the database to see what enum values are currently available
"""

import sys
import os
from datetime import datetime
from sqlalchemy import text

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, AuditActionType, ChangeType

def check_audit_action_types():
    """Check AuditActionType enum values in the database"""
    print("🔍 Checking AuditActionType enum values...")
    print("=" * 50)
    
    try:
        # Query database enum values
        result = db.session.execute(
            text("SELECT unnest(enum_range(NULL::auditactiontype)) as value ORDER BY value;")
        ).fetchall()
        
        db_values = [row[0] for row in result]
        
        # Get enum values from Python code
        code_values = [action.value for action in AuditActionType]
        
        print(f"📊 Database has {len(db_values)} AuditActionType values:")
        for i, value in enumerate(db_values, 1):
            status = "✅" if value in code_values else "⚠️"
            print(f"  {i:2d}. {status} {value}")
        
        # Check for missing values
        missing_in_db = set(code_values) - set(db_values)
        missing_in_code = set(db_values) - set(code_values)
        
        if missing_in_db:
            print(f"\n❌ Missing in database ({len(missing_in_db)}):")
            for value in sorted(missing_in_db):
                print(f"  - {value}")
        
        if missing_in_code:
            print(f"\n⚠️  In database but not in code ({len(missing_in_code)}):")
            for value in sorted(missing_in_code):
                print(f"  - {value}")
        
        if not missing_in_db and not missing_in_code:
            print("\n✅ All AuditActionType values are synchronized!")
        
        return db_values, code_values
        
    except Exception as e:
        print(f"❌ Error checking AuditActionType: {e}")
        return [], []

def check_change_types():
    """Check ChangeType enum values in the database"""
    print("\n🔍 Checking ChangeType enum values...")
    print("=" * 50)
    
    try:
        # Query database enum values
        result = db.session.execute(
            text("SELECT unnest(enum_range(NULL::changetype)) as value ORDER BY value;")
        ).fetchall()
        
        db_values = [row[0] for row in result]
        
        # Get enum values from Python code
        code_values = [change.value for change in ChangeType]
        
        print(f"📊 Database has {len(db_values)} ChangeType values:")
        for i, value in enumerate(db_values, 1):
            status = "✅" if value in code_values else "⚠️"
            print(f"  {i:2d}. {status} {value}")
        
        # Check for missing values
        missing_in_db = set(code_values) - set(db_values)
        missing_in_code = set(db_values) - set(code_values)
        
        if missing_in_db:
            print(f"\n❌ Missing in database ({len(missing_in_db)}):")
            for value in sorted(missing_in_db):
                print(f"  - {value}")
        
        if missing_in_code:
            print(f"\n⚠️  In database but not in code ({len(missing_in_code)}):")
            for value in sorted(missing_in_code):
                print(f"  - {value}")
        
        if not missing_in_db and not missing_in_code:
            print("\n✅ All ChangeType values are synchronized!")
        
        return db_values, code_values
        
    except Exception as e:
        print(f"❌ Error checking ChangeType: {e}")
        return [], []

def check_recent_audit_logs():
    """Check recent audit log entries to see which action types are being used"""
    print("\n🔍 Checking recent audit log usage...")
    print("=" * 50)
    
    try:
        # Get recent audit logs and their action types
        result = db.session.execute(
            text("""
                SELECT action_type, COUNT(*) as count
                FROM audit_log 
                WHERE timestamp >= NOW() - INTERVAL '7 days'
                GROUP BY action_type 
                ORDER BY count DESC
                LIMIT 10
            """)
        ).fetchall()
        
        if result:
            print("📊 Most used AuditActionTypes (last 7 days):")
            for action_type, count in result:
                print(f"  • {action_type}: {count} entries")
        else:
            print("📊 No audit log entries found in the last 7 days")
        
    except Exception as e:
        print(f"❌ Error checking audit logs: {e}")

def check_recent_panel_changes():
    """Check recent panel changes to see which change types are being used"""
    print("\n🔍 Checking recent panel changes...")
    print("=" * 50)
    
    try:
        # Get recent panel changes and their change types
        result = db.session.execute(
            text("""
                SELECT change_type, COUNT(*) as count
                FROM panel_changes 
                WHERE changed_at >= NOW() - INTERVAL '7 days'
                GROUP BY change_type 
                ORDER BY count DESC
                LIMIT 10
            """)
        ).fetchall()
        
        if result:
            print("📊 Most used ChangeTypes (last 7 days):")
            for change_type, count in result:
                print(f"  • {change_type}: {count} entries")
        else:
            print("📊 No panel changes found in the last 7 days")
        
    except Exception as e:
        print(f"❌ Error checking panel changes: {e}")

def generate_migration_suggestions():
    """Generate suggestions for missing enum values"""
    print("\n💡 Migration Suggestions...")
    print("=" * 50)
    
    app = create_app()
    with app.app_context():
        # Check audit action types
        audit_db, audit_code = check_audit_action_types()
        missing_audit = set(audit_code) - set(audit_db)
        
        # Check change types  
        change_db, change_code = check_change_types()
        missing_change = set(change_code) - set(change_db)
        
        if missing_audit or missing_change:
            print("\n📝 To add missing enum values, create a migration:")
            print("flask db revision -m 'Add missing enum values'")
            print("\nThen add these SQL statements to the upgrade() function:")
            
            if missing_audit:
                print("\n# Add missing AuditActionType values:")
                for value in sorted(missing_audit):
                    print(f"op.execute(\"ALTER TYPE auditactiontype ADD VALUE '{value}'\")")
            
            if missing_change:
                print("\n# Add missing ChangeType values:")
                for value in sorted(missing_change):
                    print(f"op.execute(\"ALTER TYPE changetype ADD VALUE '{value}'\")")
        else:
            print("✅ No migration needed - all enum values are synchronized!")

def main():
    """Main function to run all checks"""
    print("🔧 Database Enum Types Checker")
    print("=" * 50)
    print(f"🕒 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check enum types
            check_audit_action_types()
            check_change_types()
            
            # Check usage
            check_recent_audit_logs()
            check_recent_panel_changes()
            
            # Generate suggestions
            generate_migration_suggestions()
            
            print(f"\n✅ Enum types check completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Error during enum check: {e}")
            return False
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check database enum types")
    parser.add_argument('--audit-only', action='store_true', 
                       help='Check only AuditActionType enum')
    parser.add_argument('--change-only', action='store_true',
                       help='Check only ChangeType enum')
    parser.add_argument('--usage', action='store_true',
                       help='Show recent usage statistics')
    parser.add_argument('--suggest', action='store_true',
                       help='Generate migration suggestions')
    
    args = parser.parse_args()
    
    app = create_app()
    
    with app.app_context():
        if args.audit_only:
            check_audit_action_types()
        elif args.change_only:
            check_change_types()
        elif args.usage:
            check_recent_audit_logs()
            check_recent_panel_changes()
        elif args.suggest:
            generate_migration_suggestions()
        else:
            # Run all checks
            main()
