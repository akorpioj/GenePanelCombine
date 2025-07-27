#!/usr/bin/env python3
"""
Database migration script to add missing columns to existing user table.
This script will safely add the new authentication system columns.
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models import User, UserRole
from sqlalchemy import text, inspect

def migrate_user_schema():
    """Add missing columns to the existing user table."""
    
    app = create_app()
    
    with app.app_context():
        print("🔄 Migrating user table schema for authentication system...")
        
        try:
            # Check existing columns
            inspector = inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('user')]
            print(f"📊 Existing columns: {existing_columns}")
            
            # Add missing columns to the user table
            missing_columns = {
                'email': 'VARCHAR(120)',
                'first_name': 'VARCHAR(50)',
                'last_name': 'VARCHAR(50)',
                'organization': 'VARCHAR(100)',
                'role': "VARCHAR(20) DEFAULT 'user'",
                'is_active': 'BOOLEAN DEFAULT TRUE',
                'is_verified': 'BOOLEAN DEFAULT FALSE',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'last_login': 'TIMESTAMP',
                'login_count': 'INTEGER DEFAULT 0'
            }
            
            print("🔄 Adding missing columns to user table...")
            
            for column_name, column_type in missing_columns.items():
                if column_name not in existing_columns:
                    print(f"  Adding column '{column_name}' to table 'user'...")
                    try:
                        # Quote the table name since 'user' is a reserved keyword
                        alter_query = text(f'ALTER TABLE "user" ADD COLUMN {column_name} {column_type}')
                        db.session.execute(alter_query)
                        db.session.commit()
                        print(f"    ✅ Column '{column_name}' added successfully")
                    except Exception as e:
                        print(f"    ❌ Failed to add column '{column_name}': {e}")
                        db.session.rollback()
                        return False
                else:
                    print(f"  ✅ Column '{column_name}' already exists")
            
            # Add unique constraints
            print("🔄 Adding unique constraints...")
            try:
                # Check if email constraint already exists
                constraints = inspector.get_unique_constraints('user')
                email_constraint_exists = any('email' in constraint['column_names'] for constraint in constraints)
                
                if not email_constraint_exists and 'email' not in existing_columns:
                    db.session.execute(text('ALTER TABLE "user" ADD CONSTRAINT user_email_unique UNIQUE (email)'))
                    db.session.commit()
                    print("  ✅ Email unique constraint added")
                else:
                    print("  ✅ Email unique constraint already exists or email column didn't exist")
                    
            except Exception as e:
                print(f"  ⚠️  Could not add unique constraints: {e}")
                db.session.rollback()
                # Continue anyway, this is not critical
            
            # Update existing users with default values
            print("🔄 Updating existing users with default values...")
            try:
                # Get all users and update them with proper defaults
                users = db.session.execute(text('SELECT id, username FROM "user"')).fetchall()
                
                for user_row in users:
                    user_id, username = user_row
                    
                    # Create a default email if none exists
                    default_email = f"{username}@panelmerge.local"
                    
                    update_query = text('''
                        UPDATE "user" 
                        SET email = :email,
                            role = :role,
                            is_active = :is_active,
                            is_verified = :is_verified,
                            created_at = :created_at,
                            login_count = :login_count
                        WHERE id = :user_id AND (email IS NULL OR role IS NULL)
                    ''')
                    
                    db.session.execute(update_query, {
                        'email': default_email,
                        'role': 'user',
                        'is_active': True,
                        'is_verified': False,
                        'created_at': datetime.utcnow(),
                        'login_count': 0,
                        'user_id': user_id
                    })
                
                db.session.commit()
                print(f"  ✅ Updated {len(users)} existing users with default values")
                
            except Exception as e:
                print(f"  ❌ Failed to update existing users: {e}")
                db.session.rollback()
                return False
            
            # Create admin user if none exists
            print("🔄 Checking for admin user...")
            try:
                admin_exists = db.session.execute(
                    text('SELECT COUNT(*) FROM "user" WHERE role = :role'),
                    {'role': 'admin'}
                ).scalar()
                
                if admin_exists == 0:
                    print("  Creating default admin user...")
                    admin_password_hash = generate_password_hash('Admin123!')
                    
                    insert_query = text('''
                        INSERT INTO "user" (username, email, password_hash, first_name, last_name, 
                                          role, is_active, is_verified, created_at, login_count)
                        VALUES (:username, :email, :password_hash, :first_name, :last_name,
                                :role, :is_active, :is_verified, :created_at, :login_count)
                    ''')
                    
                    db.session.execute(insert_query, {
                        'username': 'admin',
                        'email': 'admin@panelmerge.local',
                        'password_hash': admin_password_hash,
                        'first_name': 'Admin',
                        'last_name': 'User',
                        'role': 'admin',
                        'is_active': True,
                        'is_verified': True,
                        'created_at': datetime.utcnow(),
                        'login_count': 0
                    })
                    
                    db.session.commit()
                    print("  ✅ Admin user created")
                    print("     Username: admin")
                    print("     Password: Admin123!")
                    print("     ⚠️  Please change the password after first login!")
                else:
                    print("  ✅ Admin user already exists")
                    
            except Exception as e:
                print(f"  ❌ Failed to create admin user: {e}")
                db.session.rollback()
                return False
            
            print("\n🎉 Database migration completed successfully!")
            print("📊 User authentication system is ready!")
            
            # Display final statistics
            total_users = db.session.execute(text('SELECT COUNT(*) FROM "user"')).scalar()
            active_users = db.session.execute(text('SELECT COUNT(*) FROM "user" WHERE is_active = TRUE')).scalar()
            admin_users = db.session.execute(text('SELECT COUNT(*) FROM "user" WHERE role = \'admin\'')).scalar()
            
            print(f"\n📈 Final Statistics:")
            print(f"   Total users: {total_users}")
            print(f"   Active users: {active_users}")
            print(f"   Administrators: {admin_users}")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("🔧 PanelMerge User Schema Migration")
    print("=" * 50)
    
    success = migrate_user_schema()
    if success:
        print("\n✅ Migration completed successfully!")
        print("🚀 You can now use the authentication system!")
    else:
        print("\n❌ Migration failed!")
        print("Please check the errors above and try again.")
