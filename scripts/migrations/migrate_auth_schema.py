#!/usr/bin/env python3
"""
Database migration script to add authentication system columns to existing user table.
This script will safely add the new columns needed for the enhanced authentication system.
"""

import os
import sys
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models import User, UserRole
from sqlalchemy import text

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    query = text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = :table_name 
        AND column_name = :column_name
    """)
    result = db.session.execute(query, {'table_name': table_name, 'column_name': column_name})
    return result.fetchone() is not None

def add_column_if_not_exists(table_name, column_name, column_definition):
    """Add a column to a table if it doesn't already exist"""
    if not check_column_exists(table_name, column_name):
        print(f"  Adding column '{column_name}' to table '{table_name}'...")
        query = text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
        db.session.execute(query)
        db.session.commit()
        print(f"  ✅ Column '{column_name}' added successfully")
    else:
        print(f"  ⏭️  Column '{column_name}' already exists")

def migrate_user_table():
    """Add missing columns to the user table"""
    print("🔄 Adding missing columns to user table...")
    
    # Add email column (required, unique)
    add_column_if_not_exists('user', 'email', 'VARCHAR(120)')
    
    # Add profile columns
    add_column_if_not_exists('user', 'first_name', 'VARCHAR(50)')
    add_column_if_not_exists('user', 'last_name', 'VARCHAR(50)')
    add_column_if_not_exists('user', 'organization', 'VARCHAR(100)')
    
    # Add role and status columns
    add_column_if_not_exists('user', 'role', 'VARCHAR(20) DEFAULT \'user\'')
    add_column_if_not_exists('user', 'is_active', 'BOOLEAN DEFAULT TRUE')
    add_column_if_not_exists('user', 'is_verified', 'BOOLEAN DEFAULT FALSE')
    
    # Add timestamp columns
    add_column_if_not_exists('user', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    add_column_if_not_exists('user', 'last_login', 'TIMESTAMP')
    add_column_if_not_exists('user', 'login_count', 'INTEGER DEFAULT 0')

def update_existing_users():
    """Update existing users with default values"""
    print("🔄 Updating existing users with default values...")
    
    try:
        # Get all existing users
        users = db.session.execute(text("SELECT id, username FROM \"user\"")).fetchall()
        
        for user in users:
            user_id, username = user
            
            # Check if email is null and set a default
            email_check = db.session.execute(
                text("SELECT email FROM \"user\" WHERE id = :id"), 
                {'id': user_id}
            ).fetchone()
            
            if not email_check[0]:  # If email is null
                default_email = f"{username}@panelmerge.local"
                db.session.execute(
                    text("UPDATE \"user\" SET email = :email WHERE id = :id"),
                    {'email': default_email, 'id': user_id}
                )
                print(f"  📧 Set default email for user '{username}': {default_email}")
            
            # Set default role if null
            db.session.execute(
                text("UPDATE \"user\" SET role = 'user' WHERE id = :id AND (role IS NULL OR role = '')"),
                {'id': user_id}
            )
            
            # Set default active status
            db.session.execute(
                text("UPDATE \"user\" SET is_active = TRUE WHERE id = :id AND is_active IS NULL"),
                {'id': user_id}
            )
            
            # Set created_at if null
            db.session.execute(
                text("UPDATE \"user\" SET created_at = CURRENT_TIMESTAMP WHERE id = :id AND created_at IS NULL"),
                {'id': user_id}
            )
        
        db.session.commit()
        print("✅ Existing users updated successfully")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error updating existing users: {e}")
        raise

def create_admin_user():
    """Create a default admin user if none exists"""
    print("👤 Checking for admin user...")
    
    try:
        # Check if any admin users exist
        admin_check = db.session.execute(
            text("SELECT COUNT(*) FROM \"user\" WHERE role = 'admin'")
        ).fetchone()
        
        if admin_check[0] == 0:
            # Check if 'admin' username already exists
            existing_admin = db.session.execute(
                text("SELECT id, role FROM \"user\" WHERE username = 'admin'")
            ).fetchone()
            
            if existing_admin:
                # Update existing admin user to have admin role
                print("  Updating existing 'admin' user to have admin role...")
                user_id, current_role = existing_admin
                
                db.session.execute(text("""
                    UPDATE "user" SET 
                        role = 'admin',
                        email = COALESCE(email, 'admin@panelmerge.local'),
                        first_name = COALESCE(first_name, 'Admin'),
                        last_name = COALESCE(last_name, 'User'),
                        is_active = TRUE,
                        is_verified = TRUE
                    WHERE id = :id
                """), {'id': user_id})
                
                db.session.commit()
                print("✅ Existing 'admin' user updated to admin role")
            else:
                # Create new admin user
                print("  Creating default admin user...")
                
                admin_password = generate_password_hash('Admin123!')
                db.session.execute(text("""
                    INSERT INTO "user" (username, email, password_hash, first_name, last_name, 
                                      role, is_active, is_verified, created_at, login_count)
                    VALUES (:username, :email, :password_hash, :first_name, :last_name, 
                            :role, :is_active, :is_verified, :created_at, :login_count)
                """), {
                    'username': 'admin',
                    'email': 'admin@panelmerge.local',
                    'password_hash': admin_password,
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'role': 'admin',
                    'is_active': True,
                    'is_verified': True,
                    'created_at': datetime.now(),
                    'login_count': 0
                })
                
                db.session.commit()
                print("✅ Default admin user created successfully")
            
            print("📝 Admin credentials:")
            print("   Username: admin")
            print("   Password: Admin123!")
            print("   ⚠️  Please change the password after first login!")
        else:
            print("✅ Admin user already exists")
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error with admin user: {e}")
        raise

def add_constraints():
    """Add database constraints for data integrity"""
    print("🔧 Adding database constraints...")
    
    try:
        # Add unique constraint on email if it doesn't exist
        constraint_check = db.session.execute(text("""
            SELECT constraint_name FROM information_schema.table_constraints 
            WHERE table_name = 'user' AND constraint_type = 'UNIQUE' 
            AND constraint_name LIKE '%email%'
        """)).fetchone()
        
        if not constraint_check:
            print("  Adding unique constraint on email...")
            db.session.execute(text("ALTER TABLE \"user\" ADD CONSTRAINT user_email_unique UNIQUE (email)"))
            db.session.commit()
            print("  ✅ Email unique constraint added")
        else:
            print("  ⏭️  Email unique constraint already exists")
            
    except Exception as e:
        db.session.rollback()
        print(f"⚠️  Warning: Could not add constraints: {e}")
        # Don't raise here as constraints might conflict with existing data

def run_migration():
    """Run the complete migration process"""
    app = create_app()
    
    with app.app_context():
        print("🔧 PanelMerge Authentication System Migration")
        print("=" * 60)
        
        try:
            # Step 1: Add missing columns
            migrate_user_table()
            
            # Step 2: Update existing users
            update_existing_users()
            
            # Step 3: Create admin user if needed
            create_admin_user()
            
            # Step 4: Add constraints (optional, may fail with existing data)
            add_constraints()
            
            # Step 5: Display statistics
            print("\n📈 Migration Results:")
            total_users = db.session.execute(text("SELECT COUNT(*) FROM \"user\"")).fetchone()[0]
            active_users = db.session.execute(text("SELECT COUNT(*) FROM \"user\" WHERE is_active = TRUE")).fetchone()[0]
            admin_users = db.session.execute(text("SELECT COUNT(*) FROM \"user\" WHERE role = 'admin'")).fetchone()[0]
            
            print(f"   Total users: {total_users}")
            print(f"   Active users: {active_users}")
            print(f"   Administrators: {admin_users}")
            
            print("\n🎉 Migration completed successfully!")
            print("\n🚀 Authentication system is ready to use!")
            print("   - Users can register at /auth/register")
            print("   - Users can log in at /auth/login")
            print("   - Admin panel available at /auth/admin/users")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("🔧 PanelMerge Authentication System Migration")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        print("⚠️  Force migration requested")
        run_migration()
    else:
        print("This will add authentication system columns to your existing user table.")
        print("⚠️  Make sure you have a backup of your database before proceeding!")
        response = input("\nDo you want to proceed with the migration? (y/N): ")
        if response.lower() in ['y', 'yes']:
            run_migration()
        else:
            print("❌ Migration cancelled")
