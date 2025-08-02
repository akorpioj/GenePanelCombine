#!/usr/bin/env python3
"""
Database migration to add new security audit action types
Run this script to update the database schema for comprehensive security logging
"""

import sys
import os
from datetime import datetime, timezone
from sqlalchemy import text

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, AuditActionType

def migrate_audit_action_types():
    """Add new security audit action types to the database"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("Starting audit action types migration...")
            
            # Get current enum values from database
            result = db.session.execute(
                text("SELECT unnest(enum_range(NULL::auditactiontype));")
            ).fetchall()
            
            current_values = [row[0] for row in result]
            print(f"Current audit action types: {len(current_values)} values")
            
            # Define new security audit types
            new_audit_types = [
                'SECURITY_VIOLATION',
                'ACCESS_DENIED', 
                'PRIVILEGE_ESCALATION',
                'SUSPICIOUS_ACTIVITY',
                'BRUTE_FORCE_ATTEMPT',
                'ACCOUNT_LOCKOUT',
                'PASSWORD_RESET',
                'MFA_EVENT',
                'API_ACCESS',
                'FILE_ACCESS',
                'DATA_BREACH_ATTEMPT',
                'COMPLIANCE_EVENT',
                'SYSTEM_SECURITY'
            ]
            
            # Check which values need to be added
            values_to_add = [value for value in new_audit_types if value not in current_values]
            
            if not values_to_add:
                print("All security audit types already exist in database.")
                return True
            
            print(f"Adding {len(values_to_add)} new audit action types...")
            
            # Add new enum values to the database
            for value in values_to_add:
                try:
                    sql = text(f"ALTER TYPE auditactiontype ADD VALUE '{value}';")
                    db.session.execute(sql)
                    print(f"✓ Added: {value}")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"✓ Already exists: {value}")
                    else:
                        print(f"✗ Error adding {value}: {e}")
                        raise
            
            # Commit the changes
            db.session.commit()
            
            # Verify the migration
            result = db.session.execute(
                text("SELECT unnest(enum_range(NULL::auditactiontype));")
            ).fetchall()
            
            final_values = [row[0] for row in result]
            print(f"\nMigration completed successfully!")
            print(f"Total audit action types: {len(final_values)}")
            print(f"Added: {len(values_to_add)} new security types")
            
            # Log successful migration
            from app.audit_service import AuditService
            AuditService.log_system_security(
                event_type="DATABASE_MIGRATION",
                description=f"Added {len(values_to_add)} new security audit action types",
                severity="INFO",
                system_component="database",
                details={
                    "migration_type": "audit_action_types",
                    "values_added": values_to_add,
                    "total_types": len(final_values),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Migration failed: {e}")
            db.session.rollback()
            
            # Log failed migration
            try:
                from app.audit_service import AuditService
                AuditService.log_system_security(
                    event_type="DATABASE_MIGRATION_FAILED",
                    description=f"Failed to add security audit action types: {str(e)}",
                    severity="ERROR",
                    system_component="database",
                    details={
                        "migration_type": "audit_action_types",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except:
                pass  # Don't fail on logging error
            
            return False

def check_audit_types():
    """Check current audit action types in the database"""
    
    app = create_app()
    
    with app.app_context():
        try:
            result = db.session.execute(
                text("SELECT unnest(enum_range(NULL::auditactiontype));")
            ).fetchall()
            
            values = [row[0] for row in result]
            
            print("Current Audit Action Types:")
            print("=" * 40)
            for i, value in enumerate(sorted(values), 1):
                print(f"{i:2d}. {value}")
            
            print(f"\nTotal: {len(values)} audit action types")
            
            # Check for security types
            security_types = [v for v in values if any(keyword in v for keyword in 
                            ['SECURITY', 'ACCESS', 'PRIVILEGE', 'SUSPICIOUS', 'BRUTE', 
                             'ACCOUNT', 'PASSWORD', 'MFA', 'API', 'FILE', 'BREACH', 
                             'COMPLIANCE', 'SYSTEM'])]
            
            print(f"Security-related types: {len(security_types)}")
            
            return values
            
        except Exception as e:
            print(f"Error checking audit types: {e}")
            return []

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate audit action types")
    parser.add_argument('--check', action='store_true', 
                       help='Check current audit types without migrating')
    parser.add_argument('--migrate', action='store_true',
                       help='Run the migration to add new security audit types')
    
    args = parser.parse_args()
    
    if args.check:
        check_audit_types()
    elif args.migrate:
        success = migrate_audit_action_types()
        sys.exit(0 if success else 1)
    else:
        print("Usage:")
        print("  python migrate_audit_types.py --check     # Check current types")
        print("  python migrate_audit_types.py --migrate   # Run migration")
        print("\nTo see all audit types:")
        check_audit_types()
