#!/usr/bin/env python3
"""
Migration script to add timezone_preference column to User table.
This script adds timezone support to user profiles.
"""

import os
import sys
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app import create_app
from app.models import db, User
import sqlalchemy as sa


def add_timezone_preference_column():
    """Add timezone_preference column to User table."""
    app = create_app('development')
    
    with app.app_context():
        try:
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('user')]
            
            if 'timezone_preference' in columns:
                print("timezone_preference column already exists in User table")
                return True
            
            print("Adding timezone_preference column to User table...")
            
            # Add the column
            with db.engine.connect() as conn:
                # Add column with default value 'UTC'
                # Note: 'user' is a reserved keyword in PostgreSQL, so we need to quote it
                conn.execute(sa.text("""
                    ALTER TABLE "user" 
                    ADD COLUMN timezone_preference VARCHAR(50) DEFAULT 'UTC'
                """))
                conn.commit()
            
            print("Successfully added timezone_preference column")
            
            # Update existing users to have UTC timezone
            users_updated = db.session.query(User).filter(
                User.timezone_preference.is_(None)
            ).update({User.timezone_preference: 'UTC'})
            
            if users_updated > 0:
                db.session.commit()
                print(f"Updated {users_updated} existing users to have UTC timezone preference")
            
            return True
            
        except Exception as e:
            print(f"Error adding timezone_preference column: {e}")
            db.session.rollback()
            return False


def verify_migration():
    """Verify that the migration was successful."""
    app = create_app('development')
    
    with app.app_context():
        try:
            # Check if column exists and has the expected properties
            inspector = db.inspect(db.engine)
            columns = {col['name']: col for col in inspector.get_columns('user')}
            
            if 'timezone_preference' not in columns:
                print("ERROR: timezone_preference column not found!")
                return False
            
            tz_col = columns['timezone_preference']
            print(f"timezone_preference column details:")
            print(f"  Type: {tz_col['type']}")
            print(f"  Nullable: {tz_col['nullable']}")
            print(f"  Default: {tz_col.get('default', 'None')}")
            
            # Test querying users
            user_count = User.query.count()
            users_with_tz = User.query.filter(User.timezone_preference.isnot(None)).count()
            
            print(f"Total users: {user_count}")
            print(f"Users with timezone preference: {users_with_tz}")
            
            # Test creating a new user with timezone
            test_user = User(
                username='test_timezone_user',
                email='test_timezone@example.com',
                timezone_preference='America/New_York'
            )
            test_user.set_password('testpassword')
            
            # Don't actually save the test user
            print("Test user creation successful (not saved)")
            
            return True
            
        except Exception as e:
            print(f"Error verifying migration: {e}")
            return False


def main():
    """Main function to run the migration."""
    print("Starting timezone preference migration...")
    print("=" * 50)
    
    # Run the migration
    if add_timezone_preference_column():
        print("\nMigration completed successfully!")
        
        # Verify the migration
        print("\nVerifying migration...")
        if verify_migration():
            print("Migration verification successful!")
        else:
            print("Migration verification failed!")
            return 1
    else:
        print("Migration failed!")
        return 1
    
    print("\nTimezone preference migration completed.")
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
