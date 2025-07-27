#!/usr/bin/env python3
"""
Script to create the AuditLog table in the database.
This script is safe to run multiple times - it will only create the table if it doesn't exist.
"""
import sys
import os

# Add the parent directory to the path to import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, AuditLog

def create_audit_table():
    """Create the AuditLog table if it doesn't exist."""
    app = create_app()
    
    with app.app_context():
        try:
            # Create only the AuditLog table
            AuditLog.__table__.create(db.engine, checkfirst=True)
            print("✅ AuditLog table created successfully!")
            
            # Verify the table was created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'audit_log' in tables:
                print("✅ Verified: audit_log table exists in database")
                
                # Show the columns
                columns = inspector.get_columns('audit_log')
                print(f"📋 Table has {len(columns)} columns:")
                for col in columns:
                    print(f"   - {col['name']}: {col['type']}")
            else:
                print("❌ Warning: audit_log table not found after creation")
                
        except Exception as e:
            print(f"❌ Error creating AuditLog table: {e}")
            return False
            
    return True

if __name__ == "__main__":
    print("🔧 Creating AuditLog table...")
    success = create_audit_table()
    
    if success:
        print("\n🎉 Audit trail setup complete!")
        print("The audit logging system is now ready to track user actions.")
    else:
        print("\n💥 Failed to create audit table. Please check the error messages above.")
        sys.exit(1)
