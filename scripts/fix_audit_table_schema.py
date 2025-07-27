#!/usr/bin/env python3
"""
Script to fix the audit_log table schema - extend session_id column length
"""
import sys
import os

# Add the parent directory to the path to import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db

def fix_audit_table_schema():
    """Fix the session_id column length in audit_log table"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Fixing audit_log table schema...")
            
            # Get the database connection
            connection = db.engine.connect()
            
            # Check current column length
            print("📋 Checking current column constraints...")
            result = connection.execute(
                "SELECT character_maximum_length FROM information_schema.columns "
                "WHERE table_name = 'audit_log' AND column_name = 'session_id'"
            )
            current_length = result.fetchone()
            if current_length:
                print(f"📏 Current session_id max length: {current_length[0]}")
            
            # Alter the column to be longer
            print("🔨 Altering session_id column to VARCHAR(200)...")
            connection.execute("ALTER TABLE audit_log ALTER COLUMN session_id TYPE VARCHAR(200)")
            connection.commit()
            
            # Verify the change
            result = connection.execute(
                "SELECT character_maximum_length FROM information_schema.columns "
                "WHERE table_name = 'audit_log' AND column_name = 'session_id'"
            )
            new_length = result.fetchone()
            if new_length:
                print(f"📏 New session_id max length: {new_length[0]}")
            
            connection.close()
            print("✅ Successfully updated audit_log table schema!")
            return True
            
        except Exception as e:
            print(f"❌ Error fixing audit table schema: {e}")
            return False

if __name__ == "__main__":
    print("🔧 Audit Table Schema Fix")
    print("=" * 50)
    success = fix_audit_table_schema()
    
    if success:
        print("\n🎉 Audit table schema fixed successfully!")
        print("The audit logging system should now work properly.")
    else:
        print("\n💥 Failed to fix audit table schema.")
        sys.exit(1)
