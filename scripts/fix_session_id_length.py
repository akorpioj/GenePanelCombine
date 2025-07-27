#!/usr/bin/env python3
"""
Script to fix the audit_log table session_id column length issue.
This script increases the session_id column from VARCHAR(100) to VARCHAR(200)
to accommodate longer Flask session IDs.
"""
import sys
import os

# Add the parent directory to the path to import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db

def fix_session_id_length():
    """Fix the session_id column length in audit_log table"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Fixing audit_log table session_id column length...")
            
            # Use raw SQL to alter the column with proper SQLAlchemy 2.x syntax
            from sqlalchemy import text
            
            sql = "ALTER TABLE audit_log ALTER COLUMN session_id TYPE VARCHAR(200);"
            print(f"📝 Executing SQL: {sql}")
            
            with db.engine.connect() as connection:
                connection.execute(text(sql))
                connection.commit()
            
            print("✅ Successfully updated session_id column to VARCHAR(200)")
            
            # Verify the change
            verify_sql = """
                SELECT character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'audit_log' 
                AND column_name = 'session_id'
            """
            
            with db.engine.connect() as connection:
                result = connection.execute(text(verify_sql)).fetchone()
            
            if result:
                print(f"✅ Verified: session_id column is now VARCHAR({result[0]})")
            else:
                print("⚠️  Could not verify column length, but command executed successfully")
                
            return True
            
        except Exception as e:
            print(f"❌ Error fixing session_id column: {e}")
            return False

if __name__ == "__main__":
    print("🔧 Audit Table Schema Fix")
    print("=" * 50)
    
    success = fix_session_id_length()
    
    if success:
        print("\n🎉 Audit table schema fix completed!")
        print("You can now test login/logout audit logging again.")
    else:
        print("\n💥 Failed to fix audit table schema.")
        sys.exit(1)
