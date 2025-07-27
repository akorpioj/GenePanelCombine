#!/usr/bin/env python3
"""
Database Migration Script for Adding Encrypted Columns

This script adds the new encrypted columns to existing tables:
- Adds encrypted columns to User table
- Adds encrypted columns to AuditLog table
- Handles both SQLite (development) and PostgreSQL (production)

Run this before testing the encryption system.
"""

import os
import sys

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_user_encrypted_columns():
    """Add encrypted columns to User table"""
    logger.info("Adding encrypted columns to User table...")
    
    try:
        # Check database type
        if 'sqlite' in str(db.engine.url):
            # SQLite approach - add columns if they don't exist
            with db.engine.connect() as conn:
                try:
                    conn.execute(text("ALTER TABLE user ADD COLUMN first_name_encrypted TEXT"))
                    conn.commit()
                    logger.info("Added first_name_encrypted column")
                except Exception:
                    logger.info("first_name_encrypted column already exists")
                
                try:
                    conn.execute(text("ALTER TABLE user ADD COLUMN last_name_encrypted TEXT"))
                    conn.commit()
                    logger.info("Added last_name_encrypted column")
                except Exception:
                    logger.info("last_name_encrypted column already exists")
                
                try:
                    conn.execute(text("ALTER TABLE user ADD COLUMN organization_encrypted TEXT"))
                    conn.commit()
                    logger.info("Added organization_encrypted column")
                except Exception:
                    logger.info("organization_encrypted column already exists")
                
                try:
                    conn.execute(text("ALTER TABLE user ADD COLUMN last_ip_address VARCHAR(45)"))
                    conn.commit()
                    logger.info("Added last_ip_address column")
                except Exception:
                    logger.info("last_ip_address column already exists")
                
                try:
                    conn.execute(text("ALTER TABLE user ADD COLUMN failed_login_attempts INTEGER DEFAULT 0"))
                    conn.commit()
                    logger.info("Added failed_login_attempts column")
                except Exception:
                    logger.info("failed_login_attempts column already exists")
                
                try:
                    conn.execute(text("ALTER TABLE user ADD COLUMN locked_until TIMESTAMP"))
                    conn.commit()
                    logger.info("Added locked_until column")
                except Exception:
                    logger.info("locked_until column already exists")
                
        else:
            # PostgreSQL approach - check if columns exist first
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'user' 
                    AND column_name IN ('first_name_encrypted', 'last_name_encrypted', 'organization_encrypted', 'last_ip_address', 'failed_login_attempts', 'locked_until')
                """))
                existing_columns = [row[0] for row in result]
                
                if 'first_name_encrypted' not in existing_columns:
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN first_name_encrypted TEXT'))
                    conn.commit()
                    logger.info("Added first_name_encrypted column")
                
                if 'last_name_encrypted' not in existing_columns:
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN last_name_encrypted TEXT'))
                    conn.commit()
                    logger.info("Added last_name_encrypted column")
                
                if 'organization_encrypted' not in existing_columns:
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN organization_encrypted TEXT'))
                    conn.commit()
                    logger.info("Added organization_encrypted column")
                
                if 'last_ip_address' not in existing_columns:
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN last_ip_address VARCHAR(45)'))
                    conn.commit()
                    logger.info("Added last_ip_address column")
                
                if 'failed_login_attempts' not in existing_columns:
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN failed_login_attempts INTEGER DEFAULT 0'))
                    conn.commit()
                    logger.info("Added failed_login_attempts column")
                
                if 'locked_until' not in existing_columns:
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN locked_until TIMESTAMP'))
                    conn.commit()
                    logger.info("Added locked_until column")
            
    except Exception as e:
        logger.error(f"Failed to add User encrypted columns: {e}")
        raise

def add_audit_log_encrypted_columns():
    """Add encrypted columns to AuditLog table"""
    logger.info("Adding encrypted columns to AuditLog table...")
    
    try:
        # Check database type
        if 'sqlite' in str(db.engine.url):
            # SQLite approach
            with db.engine.connect() as conn:
                try:
                    conn.execute(text("ALTER TABLE audit_log ADD COLUMN old_values_encrypted TEXT"))
                    conn.commit()
                    logger.info("Added old_values_encrypted column")
                except Exception:
                    logger.info("old_values_encrypted column already exists")
                
                try:
                    conn.execute(text("ALTER TABLE audit_log ADD COLUMN new_values_encrypted TEXT"))
                    conn.commit()
                    logger.info("Added new_values_encrypted column")
                except Exception:
                    logger.info("new_values_encrypted column already exists")
                
                try:
                    conn.execute(text("ALTER TABLE audit_log ADD COLUMN details_encrypted TEXT"))
                    conn.commit()
                    logger.info("Added details_encrypted column")
                except Exception:
                    logger.info("details_encrypted column already exists")
                
                # Update session_id column length if needed
                try:
                    # SQLite doesn't support ALTER COLUMN, so we'll skip this for SQLite
                    logger.info("Skipping session_id column update for SQLite")
                except Exception:
                    pass
                
        else:
            # PostgreSQL approach
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'audit_log' 
                    AND column_name IN ('old_values_encrypted', 'new_values_encrypted', 'details_encrypted')
                """))
                existing_columns = [row[0] for row in result]
                
                if 'old_values_encrypted' not in existing_columns:
                    conn.execute(text("ALTER TABLE audit_log ADD COLUMN old_values_encrypted TEXT"))
                    conn.commit()
                    logger.info("Added old_values_encrypted column")
                
                if 'new_values_encrypted' not in existing_columns:
                    conn.execute(text("ALTER TABLE audit_log ADD COLUMN new_values_encrypted TEXT"))
                    conn.commit()
                    logger.info("Added new_values_encrypted column")
                
                if 'details_encrypted' not in existing_columns:
                    conn.execute(text("ALTER TABLE audit_log ADD COLUMN details_encrypted TEXT"))
                    conn.commit()
                    logger.info("Added details_encrypted column")
                
                # Update session_id column length
                try:
                    conn.execute(text("ALTER TABLE audit_log ALTER COLUMN session_id TYPE VARCHAR(200)"))
                    conn.commit()
                    logger.info("Updated session_id column length to 200")
                except Exception as e:
                    logger.info(f"session_id column update not needed or failed: {e}")
            
    except Exception as e:
        logger.error(f"Failed to add AuditLog encrypted columns: {e}")
        raise

def verify_columns():
    """Verify that all required columns exist"""
    logger.info("Verifying encrypted columns...")
    
    try:
        if 'sqlite' in str(db.engine.url):
            # SQLite verification
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(user)"))
                user_columns = [row[1] for row in result]
                
                result = conn.execute(text("PRAGMA table_info(audit_log)"))
                audit_columns = [row[1] for row in result]
        else:
            # PostgreSQL verification
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'user'
                """))
                user_columns = [row[0] for row in result]
                
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'audit_log'
                """))
                audit_columns = [row[0] for row in result]
        
        # Check User table columns
        required_user_columns = ['first_name_encrypted', 'last_name_encrypted', 'organization_encrypted', 'last_ip_address', 'failed_login_attempts', 'locked_until']
        for col in required_user_columns:
            if col in user_columns:
                logger.info(f"✅ User.{col} exists")
            else:
                logger.error(f"❌ User.{col} missing")
        
        # Check AuditLog table columns
        required_audit_columns = ['old_values_encrypted', 'new_values_encrypted', 'details_encrypted']
        for col in required_audit_columns:
            if col in audit_columns:
                logger.info(f"✅ AuditLog.{col} exists")
            else:
                logger.error(f"❌ AuditLog.{col} missing")
                
    except Exception as e:
        logger.error(f"Failed to verify columns: {e}")
        raise

def add_panel_download_columns():
    """Add missing columns to PanelDownload table"""
    logger.info("Adding missing columns to PanelDownload table...")
    
    try:
        # Check database type
        if 'sqlite' in str(db.engine.url):
            # SQLite approach
            with db.engine.connect() as conn:
                try:
                    conn.execute(text("ALTER TABLE panel_download ADD COLUMN user_id INTEGER"))
                    conn.commit()
                    logger.info("Added user_id column to panel_download")
                except Exception:
                    logger.info("user_id column already exists in panel_download")
                
                try:
                    conn.execute(text("ALTER TABLE panel_download ADD COLUMN list_types VARCHAR(255)"))
                    conn.commit()
                    logger.info("Added list_types column to panel_download")
                except Exception:
                    logger.info("list_types column already exists in panel_download")
                
                try:
                    conn.execute(text("ALTER TABLE panel_download ADD COLUMN gene_count INTEGER"))
                    conn.commit()
                    logger.info("Added gene_count column to panel_download")
                except Exception:
                    logger.info("gene_count column already exists in panel_download")
        else:
            # PostgreSQL approach
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'panel_download' 
                    AND column_name IN ('user_id', 'list_types', 'gene_count')
                """))
                existing_columns = [row[0] for row in result]
                
                if 'user_id' not in existing_columns:
                    conn.execute(text("ALTER TABLE panel_download ADD COLUMN user_id INTEGER"))
                    logger.info("Added user_id column to panel_download")
                
                if 'list_types' not in existing_columns:
                    conn.execute(text("ALTER TABLE panel_download ADD COLUMN list_types VARCHAR(255)"))
                    logger.info("Added list_types column to panel_download")
                
                if 'gene_count' not in existing_columns:
                    conn.execute(text("ALTER TABLE panel_download ADD COLUMN gene_count INTEGER"))
                    logger.info("Added gene_count column to panel_download")
                
                conn.commit()
        
        logger.info("PanelDownload table migration completed")
        
    except Exception as e:
        logger.error(f"Failed to add PanelDownload columns: {e}")
        raise

def main():
    """Main migration function"""
    logger.info("Starting database migration for encryption columns...")
    
    # Create Flask app
    app = create_app('development')
    
    with app.app_context():
        try:
            # Create tables if they don't exist
            db.create_all()
            
            # Add encrypted columns
            add_user_encrypted_columns()
            add_audit_log_encrypted_columns()
            add_panel_download_columns()
            
            # Verify columns were added
            verify_columns()
            
            logger.info("Database migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
