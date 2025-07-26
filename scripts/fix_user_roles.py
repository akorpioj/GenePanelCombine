#!/usr/bin/env python3
"""
Fix user roles in the database to ensure proper enum handling.
"""

import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app
from app.models import User, UserRole, db
from sqlalchemy import text

def fix_user_roles():
    """Fix user roles to ensure they match the enum values."""
    
    app = create_app()
    with app.app_context():
        print("🔧 Fixing user roles in database...")
        
        try:
            # Query users directly from database to see raw role values
            raw_users = db.session.execute(text('SELECT id, username, role FROM "user"')).fetchall()
            
            print(f"Found {len(raw_users)} users in database:")
            for user in raw_users:
                user_id, username, role = user
                print(f"  User '{username}': role = '{role}' (type: {type(role)})")
            
            # Update users to ensure roles are properly set
            for user in raw_users:
                user_id, username, role = user
                
                # Map lowercase role values to uppercase PostgreSQL ENUM values
                role_mapping = {
                    'admin': 'ADMIN',
                    'editor': 'EDITOR', 
                    'user': 'USER',
                    'viewer': 'VIEWER',
                    'ADMIN': 'ADMIN',
                    'EDITOR': 'EDITOR',
                    'USER': 'USER',
                    'VIEWER': 'VIEWER'
                }
                
                if role in role_mapping:
                    correct_role = role_mapping[role]
                    if role != correct_role:
                        print(f"  🔧 Fixing user '{username}' role from '{role}' to '{correct_role}'")
                        db.session.execute(
                            text('UPDATE "user" SET role = :new_role WHERE id = :user_id'),
                            {'new_role': correct_role, 'user_id': user_id}
                        )
                    else:
                        print(f"  ✅ User '{username}' role '{role}' is already correct")
                else:
                    print(f"  🔧 Unknown role '{role}' for user '{username}', setting to 'USER'")
                    db.session.execute(
                        text('UPDATE "user" SET role = :new_role WHERE id = :user_id'),
                        {'new_role': 'USER', 'user_id': user_id}
                    )
            
            db.session.commit()
            print("✅ Database roles updated")
            
            # Now try to query using the ORM
            print("\n🔍 Testing ORM queries...")
            users = User.query.all()
            print(f"Successfully queried {len(users)} users via ORM:")
            
            for user in users:
                print(f"  User '{user.username}': role = {user.role.value} ({user.role})")
                print(f"    - Can upload: {user.can_upload()}")
                print(f"    - Can moderate: {user.can_moderate()}")
                print(f"    - Is admin: {user.is_admin()}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()
            return False
        
        return True

if __name__ == '__main__':
    print("🔧 PanelMerge Role Fix Script")
    print("=" * 40)
    
    if fix_user_roles():
        print("\n✅ Role fix completed successfully!")
    else:
        print("\n❌ Role fix failed!")
