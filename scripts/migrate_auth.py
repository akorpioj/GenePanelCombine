#!/usr/bin/env python3
"""
Database migration script for user authentication system.
This script will create the new User table and migrate any existing data.
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
from sqlalchemy import text

def migrate_database():
    """Migrate the database to include the new User authentication system."""
    
    app = create_app()
    
    with app.app_context():
        print("🔄 Starting database migration for user authentication system...")
        
        try:
            # Create all tables (including the new User table)
            print("📊 Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Check if we need to create a default admin user
            admin_user = User.query.filter_by(role=UserRole.ADMIN).first()
            
            if not admin_user:
                print("👤 Creating default admin user...")
                
                # Create default admin user
                admin_user = User(
                    username='admin',
                    email='admin@panelmerge.local',
                    password_hash=generate_password_hash('Admin123!'),
                    first_name='Admin',
                    last_name='User',
                    role=UserRole.ADMIN,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                
                db.session.add(admin_user)
                db.session.commit()
                
                print("✅ Default admin user created successfully")
                print("📝 Admin credentials:")
                print("   Username: admin")
                print("   Password: Admin123!")
                print("   ⚠️  Please change the password after first login!")
            else:
                print("✅ Admin user already exists")
            
            # Display user statistics
            total_users = User.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            admins = User.query.filter_by(role=UserRole.ADMIN).count()
            
            print(f"\n📈 User Statistics:")
            print(f"   Total users: {total_users}")
            print(f"   Active users: {active_users}")
            print(f"   Administrators: {admins}")
            
            print("\n🎉 Database migration completed successfully!")
            print("\n🚀 User authentication system is ready to use!")
            print("   - Users can register at /auth/register")
            print("   - Users can log in at /auth/login")
            print("   - Admin panel available at /auth/admin/users")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            return False
            
    return True

def check_migration_status():
    """Check if migration is needed."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if User table exists and has the required columns
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'user'
            """))
            columns = [row[0] for row in result.fetchall()]
            
            required_columns = ['email', 'role', 'is_active', 'created_at']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                print(f"🔄 Missing columns in user table: {missing_columns}")
                print("💡 Please run 'python scripts/migrate_auth_schema.py' first to update the existing table schema")
                return False
            else:
                print("✅ User table schema is up to date")
                return False  # No migration needed
                
        except Exception as e:
            print(f"🔄 Cannot check user table schema: {e}")
            print("💡 This might be a new installation. Proceeding with full table creation.")
            return True

if __name__ == '__main__':
    print("🔧 PanelMerge User Authentication Migration")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        print("⚠️  Force migration requested")
        migrate_database()
    elif check_migration_status():
        response = input("Do you want to proceed with the migration? (y/N): ")
        if response.lower() in ['y', 'yes']:
            migrate_database()
        else:
            print("❌ Migration cancelled")
    else:
        print("ℹ️  No migration needed")
