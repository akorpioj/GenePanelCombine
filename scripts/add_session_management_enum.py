#!/usr/bin/env python3
"""
Add SESSION_MANAGEMENT to AuditActionType enum
This script adds the new SESSION_MANAGEMENT action type to support enhanced session security
"""

import sys
import os
from sqlalchemy import text

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def add_session_management_enum():
    """Add SESSION_MANAGEMENT to the AuditActionType enum"""
    try:
        from app import create_app
        from app.models import db
        
        # Create app with development configuration
        app = create_app('development')
        
        with app.app_context():
            print("🔧 Adding SESSION_MANAGEMENT to AuditActionType enum...")
            
            # Add the new enum value using raw SQL
            # Note: PostgreSQL requires this approach for adding enum values
            try:
                db.session.execute(text(
                    "ALTER TYPE auditactiontype ADD VALUE 'SESSION_MANAGEMENT'"
                ))
                db.session.commit()
                print("✅ Successfully added SESSION_MANAGEMENT to AuditActionType enum")
                
            except Exception as e:
                error_str = str(e)
                if "already exists" in error_str or "duplicate key value" in error_str:
                    print("ℹ️  SESSION_MANAGEMENT enum value already exists")
                else:
                    print(f"❌ Failed to add enum value: {e}")
                    db.session.rollback()
                    return False
            
            # Verify the enum value was added
            result = db.session.execute(text(
                "SELECT unnest(enum_range(NULL::auditactiontype)) as action_type"
            ))
            
            enum_values = [row[0] for row in result]
            if 'SESSION_MANAGEMENT' in enum_values:
                print("✅ Verification successful: SESSION_MANAGEMENT is now available")
                print(f"📋 Available enum values: {', '.join(sorted(enum_values))}")
                return True
            else:
                print("❌ Verification failed: SESSION_MANAGEMENT not found in enum")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    print("🗃️  Database Migration: Add SESSION_MANAGEMENT Enum Value")
    print("=" * 60)
    
    success = add_session_management_enum()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("   The SESSION_MANAGEMENT action type is now available for audit logging.")
    else:
        print("\n⚠️  Migration failed. Please check the error messages above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
