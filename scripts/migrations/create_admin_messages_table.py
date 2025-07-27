#!/usr/bin/env python3
"""
Migration: Create admin_messages table
Created: 2024
Description: Creates the admin_messages table for site-wide announcements and messages
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app import create_app, db
from app.models import AdminMessage
from app.audit_service import AuditService

def run_migration():
    """Create the admin_messages table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if table already exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            if 'admin_message' in inspector.get_table_names():
                print("❌ Table 'admin_message' already exists. Migration not needed.")
                return False
            
            print("📋 Creating admin_messages table...")
            
            # Create the table
            db.create_all()
            
            # Verify table was created
            inspector = inspect(db.engine)
            if 'admin_message' in inspector.get_table_names():
                print("✅ Successfully created admin_message table")
                
                # Log the migration in audit trail
                try:
                    audit_service = AuditService()
                    audit_service.log_action(
                        user_id=None,
                        action='database_migration',
                        resource_type='admin_message',
                        resource_id='table_creation',
                        details={
                            'migration': 'create_admin_messages_table',
                            'timestamp': datetime.utcnow().isoformat(),
                            'description': 'Created admin_message table for site announcements'
                        }
                    )
                    print("📝 Migration logged in audit trail")
                except Exception as e:
                    print(f"⚠️  Failed to log migration in audit trail: {e}")
                
                return True
            else:
                print("❌ Failed to create admin_message table")
                return False
                
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            return False

def rollback_migration():
    """Drop the admin_messages table (rollback)"""
    app = create_app()
    
    with app.app_context():
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            if 'admin_message' not in inspector.get_table_names():
                print("❌ Table 'admin_message' does not exist. Nothing to rollback.")
                return False
            
            print("🔄 Rolling back admin_messages table...")
            
            # Drop the table
            AdminMessage.__table__.drop(db.engine)
            
            # Verify table was dropped
            inspector = inspect(db.engine)
            if 'admin_message' not in inspector.get_table_names():
                print("✅ Successfully dropped admin_message table")
                
                # Log the rollback in audit trail
                try:
                    audit_service = AuditService()
                    audit_service.log_action(
                        user_id=None,
                        action='database_rollback',
                        resource_type='admin_message',
                        resource_id='table_deletion',
                        details={
                            'migration': 'create_admin_messages_table',
                            'action': 'rollback',
                            'timestamp': datetime.utcnow().isoformat(),
                            'description': 'Dropped admin_message table (rollback)'
                        }
                    )
                    print("📝 Rollback logged in audit trail")
                except Exception as e:
                    print(f"⚠️  Failed to log rollback in audit trail: {e}")
                
                return True
            else:
                print("❌ Failed to drop admin_message table")
                return False
                
        except Exception as e:
            print(f"❌ Error during rollback: {e}")
            return False

def show_table_info():
    """Show information about the admin_message table"""
    app = create_app()
    
    with app.app_context():
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            if 'admin_message' not in inspector.get_table_names():
                print("❌ Table 'admin_message' does not exist.")
                return
            
            print("📊 Admin Message Table Information:")
            print("=" * 50)
            
            columns = inspector.get_columns('admin_message')
            for column in columns:
                nullable = "NULL" if column['nullable'] else "NOT NULL"
                default = f" DEFAULT {column['default']}" if column['default'] else ""
                print(f"  {column['name']:<20} {column['type']:<20} {nullable}{default}")
            
            # Show any existing messages
            messages = AdminMessage.query.all()
            print(f"\n📝 Current messages: {len(messages)}")
            for msg in messages:
                status = "Active" if msg.is_active else "Inactive"
                expiry = f" (expires: {msg.expires_at})" if msg.expires_at else " (no expiration)"
                print(f"  - {msg.title} [{msg.message_type}] - {status}{expiry}")
            
        except Exception as e:
            print(f"❌ Error showing table info: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Admin Messages Table Migration')
    parser.add_argument('action', choices=['migrate', 'rollback', 'info'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    print("🗃️  Admin Messages Table Migration")
    print("=" * 40)
    
    if args.action == 'migrate':
        success = run_migration()
        if success:
            print("\n✅ Migration completed successfully!")
        else:
            print("\n❌ Migration failed!")
            sys.exit(1)
    
    elif args.action == 'rollback':
        success = rollback_migration()
        if success:
            print("\n✅ Rollback completed successfully!")
        else:
            print("\n❌ Rollback failed!")
            sys.exit(1)
    
    elif args.action == 'info':
        show_table_info()
