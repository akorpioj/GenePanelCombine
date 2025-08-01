# PanelMerge Migration Guide

This guide provides step-by-step instructions for migrating between different versions of PanelMerge, including database migrations, configuration updates, and deployment procedures.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Pre-Migration Checklist](#pre-migration-checklist)
3. [Version-Specific Migrations](#version-specific-migrations)
4. [Database Migrations](#database-migrations)
5. [Configuration Updates](#configuration-updates)
6. [Data Migration](#data-migration)
7. [Post-Migration Verification](#post-migration-verification)
8. [Rollback Procedures](#rollback-procedures)
9. [Troubleshooting](#troubleshooting)

---

## 🔍 Overview

### Migration Types

- **Major Version Migration** (1.x.x → 2.x.x): May include breaking changes
- **Minor Version Migration** (1.3.x → 1.4.x): New features, backward compatible
- **Patch Version Migration** (1.4.0 → 1.4.1): Bug fixes, security patches

### Migration Complexity

| From → To | Complexity | Database Changes | Config Changes | Downtime |
|-----------|------------|------------------|----------------|----------|
| 1.3.x → 1.4.x | Medium | Yes | Yes | ~5-10 min |
| 1.2.x → 1.4.x | High | Yes | Yes | ~15-30 min |
| 1.1.x → 1.4.x | High | Yes | Yes | ~30-60 min |

---

## ✅ Pre-Migration Checklist

### 🔒 Backup Requirements

- [ ] **Database Backup**: Create full database backup
- [ ] **Configuration Backup**: Save current `.env` and config files
- [ ] **File System Backup**: Backup uploaded files and logs
- [ ] **Application Code Backup**: Backup current application version
- [ ] **Redis Backup**: Export Redis data if using persistent storage

### 📊 Environment Assessment

- [ ] **Current Version**: Document current PanelMerge version
- [ ] **Dependencies**: List current Python/Node.js dependencies
- [ ] **Database Schema**: Document current database structure
- [ ] **Configuration**: Review current environment variables
- [ ] **Custom Modifications**: Document any customizations made

### 🔧 System Requirements

- [ ] **Python Version**: Ensure Python 3.8+ is installed
- [ ] **Node.js Version**: Ensure Node.js 16+ is installed
- [ ] **Database Version**: PostgreSQL 12+ or SQLite 3.35+
- [ ] **Redis Version**: Redis 6.0+ recommended
- [ ] **Disk Space**: Ensure sufficient space for migration
- [ ] **Memory**: Minimum 2GB RAM recommended

---

## 🚀 Version-Specific Migrations

### Migrating to v1.4.x (Security Enhanced)

#### From v1.3.x to v1.4.x

**Major Changes**:
- Enhanced security audit logging system
- New AdminMessage system for site announcements
- Comprehensive security monitoring
- Updated session management with Redis

**Migration Steps**:

1. **Backup Current System**
   ```bash
   # Create backup directory
   mkdir -p backups/v1.3-$(date +%Y%m%d-%H%M%S)
   
   # Backup database
   pg_dump panelmerge > backups/v1.3-$(date +%Y%m%d-%H%M%S)/database.sql
   
   # Backup application
   cp -r . backups/v1.3-$(date +%Y%m%d-%H%M%S)/application/
   ```

2. **Update Application Code**
   ```bash
   # Pull latest code
   git fetch origin
   git checkout v1.4.0
   
   # Update dependencies
   pip install -r requirements.txt
   npm install
   
   # Build CSS
   npm run build:css
   ```

3. **Update Configuration**
   ```bash
   # Add new environment variables to .env
   echo "ENCRYPTION_KEY=$(python -c 'import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())')" >> .env
   echo "SECURITY_MONITORING_ENABLED=True" >> .env
   echo "AUDIT_RETENTION_DAYS=365" >> .env
   echo "SESSION_TIMEOUT=3600" >> .env
   ```

4. **Run Database Migrations**
   ```bash
   # Run audit action types migration
   python scripts/migrations/add_audit_action_types.py migrate
   
   # Run admin messages migration
   python scripts/migrations/create_admin_messages_table.py migrate
   
   # Verify migrations
   python scripts/db/check_db.py
   ```

5. **Restart Services**
   ```bash
   # Restart application
   systemctl restart panelmerge
   
   # Restart Redis (if system service)
   systemctl restart redis
   ```

#### From v1.2.x to v1.4.x

**Additional Steps** (complete v1.3.x migration first):

1. **User Panel Upload Migration**
   ```bash
   # Migrate uploaded panel data structure
   python scripts/migrations/migrate_user_panels_v1.2_to_v1.4.py
   ```

2. **Session Data Migration**
   ```bash
   # Clear old session data (users will need to re-login)
   redis-cli FLUSHDB
   ```

#### From v1.1.x to v1.4.x

**Additional Steps** (complete all previous migrations):

1. **PanelApp Australia Integration**
   ```bash
   # Update cache structure for dual API support
   python scripts/migrations/migrate_cache_structure_v1.1_to_v1.4.py
   ```

2. **User Interface Migration**
   ```bash
   # Clear browser cache (notify users)
   # No automatic migration needed
   ```

---

## 🗃️ Database Migrations

### Automatic Migration Scripts

#### v1.4.x Migration Scripts

1. **Audit Action Types Migration**
   ```bash
   # Location: scripts/migrations/add_audit_action_types.py
   python scripts/migrations/add_audit_action_types.py migrate
   
   # Verify
   python scripts/migrations/add_audit_action_types.py info
   
   # Rollback if needed
   python scripts/migrations/add_audit_action_types.py rollback
   ```

2. **Admin Messages Table**
   ```bash
   # Location: scripts/migrations/create_admin_messages_table.py
   python scripts/migrations/create_admin_messages_table.py migrate
   
   # Verify
   python scripts/migrations/create_admin_messages_table.py info
   ```

#### Manual Database Migration

If automatic scripts fail, use manual SQL migration:

```sql
-- Add new audit action types (v1.4.x)
ALTER TYPE auditactiontype ADD VALUE IF NOT EXISTS 'SECURITY_VIOLATION';
ALTER TYPE auditactiontype ADD VALUE IF NOT EXISTS 'ACCESS_DENIED';
ALTER TYPE auditactiontype ADD VALUE IF NOT EXISTS 'PRIVILEGE_ESCALATION';
-- ... (see full SQL in migration scripts)

-- Create admin_message table (v1.4.x)
CREATE TABLE IF NOT EXISTS admin_message (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    message_type VARCHAR(20) NOT NULL DEFAULT 'info',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    created_by_id INTEGER NOT NULL,
    FOREIGN KEY (created_by_id) REFERENCES user(id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_admin_message_active ON admin_message(is_active);
CREATE INDEX IF NOT EXISTS idx_admin_message_expires ON admin_message(expires_at);
```

### Database Migration Verification

```bash
# Check database schema
python -c "
from app import create_app, db
from sqlalchemy import inspect
app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print('Tables:', tables)
    if 'admin_message' in tables:
        print('✅ admin_message table exists')
    else:
        print('❌ admin_message table missing')
"

# Check audit action types
python -c "
from app.models import AuditActionType
for action in AuditActionType:
    print(f'✅ {action.value}')
"
```

---

## ⚙️ Configuration Updates

### Environment Variables Migration

#### New Variables in v1.4.x

Add these variables to your `.env` file:

```bash
# Security Configuration
ENCRYPTION_KEY=your-encryption-key-here
SECURITY_MONITORING_ENABLED=True
THREAT_DETECTION_SENSITIVITY=medium
IP_BLOCKING_ENABLED=True
BRUTE_FORCE_THRESHOLD=5

# Audit Configuration
AUDIT_RETENTION_DAYS=365
AUDIT_ENCRYPTION=True
AUDIT_COMPRESSION=True

# Session Security
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=900

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/panelmerge.log
MAX_LOG_SIZE=10485760
LOG_BACKUP_COUNT=5
```

#### Configuration Migration Script

```bash
#!/bin/bash
# migrate_config_v1.3_to_v1.4.sh

# Backup current .env
cp .env .env.backup.$(date +%Y%m%d-%H%M%S)

# Generate encryption key if not exists
if ! grep -q "ENCRYPTION_KEY" .env; then
    echo "ENCRYPTION_KEY=$(python -c 'import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())')" >> .env
fi

# Add security settings
echo "SECURITY_MONITORING_ENABLED=True" >> .env
echo "AUDIT_RETENTION_DAYS=365" >> .env
echo "SESSION_TIMEOUT=3600" >> .env
echo "RATE_LIMIT_PER_MINUTE=60" >> .env

echo "✅ Configuration migration completed"
```

### Updated Configuration Validation

```python
# validate_v1.4_config.py
import os
import sys

V1_4_REQUIRED_VARS = [
    'SECRET_KEY',
    'ENCRYPTION_KEY',
    'FLASK_ENV',
    'DATABASE_URL',
    'REDIS_URL',
    'SECURITY_MONITORING_ENABLED',
    'AUDIT_RETENTION_DAYS'
]

def validate_migration():
    missing = []
    for var in V1_4_REQUIRED_VARS:
        if not os.getenv(var):
            if var == 'DATABASE_URL' and os.getenv('WITHOUT_DB') == 'True':
                continue
            missing.append(var)
    
    if missing:
        print(f"❌ Missing required variables for v1.4: {', '.join(missing)}")
        return False
    
    print("✅ v1.4 configuration validation passed")
    return True

if __name__ == "__main__":
    if not validate_migration():
        sys.exit(1)
```

---

## 📦 Data Migration

### User Data Migration

#### Session Data Migration (v1.4.x)

```python
# migrate_sessions_v1.3_to_v1.4.py
import redis
from app import create_app
from app.session_service import session_service

def migrate_sessions():
    """Migrate sessions to new v1.4 format"""
    app = create_app()
    
    with app.app_context():
        # Clear old session format
        redis_client = session_service.redis_client
        
        # Get all old session keys
        old_keys = redis_client.keys("session:*")
        
        if old_keys:
            print(f"Clearing {len(old_keys)} old session keys")
            redis_client.delete(*old_keys)
        
        # Clear user session sets
        user_keys = redis_client.keys("user_sessions:*")
        if user_keys:
            redis_client.delete(*user_keys)
        
        print("✅ Session migration completed - users will need to re-login")

if __name__ == "__main__":
    migrate_sessions()
```

#### File Upload Data Migration

```python
# migrate_uploads_v1.3_to_v1.4.py
import os
import shutil
from pathlib import Path

def migrate_upload_structure():
    """Migrate upload directory structure"""
    old_upload_dir = Path("instance/uploads")
    new_upload_dir = Path("instance/uploads")
    
    if not old_upload_dir.exists():
        print("No upload directory found - skipping migration")
        return
    
    # Ensure proper permissions
    os.chmod(old_upload_dir, 0o755)
    
    # Create session subdirectories if needed
    for session_dir in old_upload_dir.glob("session_*"):
        if session_dir.is_dir():
            os.chmod(session_dir, 0o755)
    
    print("✅ Upload directory migration completed")

if __name__ == "__main__":
    migrate_upload_structure()
```

### Cache Migration

```python
# migrate_cache_v1.3_to_v1.4.py
from app.main.cache_utils import cache_manager

def migrate_cache():
    """Clear old cache to force rebuild with new structure"""
    try:
        # Clear all panel cache
        cache_manager.clear_panel_cache('uk')
        cache_manager.clear_panel_cache('aus')
        
        # Clear gene search cache
        cache_manager.redis_client.delete('gene_search:*')
        
        print("✅ Cache migration completed")
    except Exception as e:
        print(f"⚠️ Cache migration warning: {e}")

if __name__ == "__main__":
    migrate_cache()
```

---

## ✅ Post-Migration Verification

### Automated Verification Script

```python
# verify_migration_v1.4.py
from app import create_app, db
from app.models import User, AuditLog, AdminMessage, AuditActionType
from app.session_service import session_service
from app.audit_service import AuditService
import sys

def verify_migration():
    """Verify v1.4 migration completed successfully"""
    app = create_app()
    errors = []
    
    with app.app_context():
        # 1. Check database tables
        try:
            # Test AdminMessage model
            AdminMessage.query.first()
            print("✅ AdminMessage table accessible")
        except Exception as e:
            errors.append(f"AdminMessage table error: {e}")
        
        # 2. Check audit action types
        try:
            security_violation = AuditActionType.SECURITY_VIOLATION
            print("✅ New audit action types available")
        except Exception as e:
            errors.append(f"Audit action types error: {e}")
        
        # 3. Check Redis connection
        try:
            session_service.redis_client.ping()
            print("✅ Redis connection working")
        except Exception as e:
            errors.append(f"Redis connection error: {e}")
        
        # 4. Test audit logging
        try:
            AuditService.log_admin_action("Migration verification test")
            print("✅ Audit logging working")
        except Exception as e:
            errors.append(f"Audit logging error: {e}")
        
        # 5. Check encryption service
        try:
            from app.encryption_service import EncryptionService
            enc_service = EncryptionService()
            test_data = "test"
            encrypted = enc_service.encrypt(test_data)
            decrypted = enc_service.decrypt(encrypted)
            assert decrypted == test_data
            print("✅ Encryption service working")
        except Exception as e:
            errors.append(f"Encryption service error: {e}")
    
    if errors:
        print("\n❌ Migration verification failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\n✅ Migration verification passed!")
        return True

if __name__ == "__main__":
    if not verify_migration():
        sys.exit(1)
```

### Manual Verification Steps

1. **Web Interface Test**
   ```bash
   # Start application
   python run.py
   
   # Test main page
   curl -I http://localhost:5000/
   
   # Test admin login
   curl -I http://localhost:5000/admin/users
   ```

2. **Database Query Test**
   ```sql
   -- Check admin_message table
   SELECT COUNT(*) FROM admin_message;
   
   -- Check audit_log table
   SELECT action_type, COUNT(*) FROM audit_log 
   GROUP BY action_type 
   ORDER BY COUNT(*) DESC;
   
   -- Check user table
   SELECT role, COUNT(*) FROM "user" GROUP BY role;
   ```

3. **Functionality Test**
   - [ ] User registration and login
   - [ ] Panel search and selection
   - [ ] File upload functionality
   - [ ] Admin user management
   - [ ] Admin message creation
   - [ ] Audit log viewing

---

## 🔄 Rollback Procedures

### Database Rollback

#### Automated Rollback

```bash
# Rollback admin messages table
python scripts/migrations/create_admin_messages_table.py rollback

# Rollback audit action types
python scripts/migrations/add_audit_action_types.py rollback
```

#### Manual Database Rollback

```sql
-- Remove admin_message table
DROP TABLE IF EXISTS admin_message;

-- Remove new audit action types (PostgreSQL)
-- Note: PostgreSQL doesn't support removing enum values easily
-- You may need to recreate the enum type
```

### Application Rollback

```bash
# Restore from backup
git checkout v1.3.x

# Restore configuration
cp .env.backup.20250727-120000 .env

# Restore database
psql panelmerge < backups/v1.3-20250727-120000/database.sql

# Reinstall old dependencies
pip install -r requirements.txt
npm install
npm run build:css

# Restart services
systemctl restart panelmerge
```

### Emergency Rollback Script

```bash
#!/bin/bash
# emergency_rollback_v1.4_to_v1.3.sh

set -e

BACKUP_DIR="$1"
if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

echo "🚨 Emergency rollback initiated..."

# Stop services
systemctl stop panelmerge

# Rollback database
echo "📦 Restoring database..."
psql panelmerge < "$BACKUP_DIR/database.sql"

# Rollback application code
echo "💻 Restoring application..."
git checkout v1.3.x

# Restore configuration
echo "⚙️ Restoring configuration..."
cp "$BACKUP_DIR/.env" .env

# Reinstall dependencies
echo "📦 Reinstalling dependencies..."
pip install -r requirements.txt
npm install
npm run build:css

# Start services
systemctl start panelmerge

echo "✅ Emergency rollback completed"
```

---

## 🔧 Troubleshooting

### Common Migration Issues

#### Database Connection Errors

**Issue**: Cannot connect to database after migration
```bash
# Check database service
systemctl status postgresql

# Verify connection string
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    print('✅ Database connection successful')
"
```

#### Redis Connection Errors

**Issue**: Redis connection fails after migration
```bash
# Check Redis service
systemctl status redis

# Test connection
redis-cli ping

# Check Redis configuration
python -c "
from app.extensions import redis_client
redis_client.ping()
print('✅ Redis connection successful')
"
```

#### Permission Errors

**Issue**: File permission errors after migration
```bash
# Fix upload directory permissions
chmod -R 755 instance/uploads/

# Fix log directory permissions  
mkdir -p logs/
chmod 755 logs/

# Fix cache permissions
chmod -R 755 __pycache__/
```

#### Migration Script Failures

**Issue**: Automatic migration scripts fail
```bash
# Check database connection first
python scripts/db/check_db.py

# Run migrations with verbose output
python scripts/migrations/create_admin_messages_table.py migrate --verbose

# Check migration status
python scripts/migrations/create_admin_messages_table.py info
```

### Recovery Procedures

#### Partial Migration Recovery

If migration partially fails:

1. **Identify Failed Step**
   ```bash
   # Check database state
   python scripts/db/check_db.py
   
   # Check application logs
   tail -f logs/panelmerge.log
   ```

2. **Complete Missing Steps**
   ```bash
   # Re-run specific migration
   python scripts/migrations/[failed_migration].py migrate
   
   # Verify completion
   python verify_migration_v1.4.py
   ```

3. **Clean Up Partial Changes**
   ```bash
   # Clear Redis cache
   redis-cli FLUSHALL
   
   # Restart services
   systemctl restart panelmerge
   ```

#### Data Corruption Recovery

If data corruption occurs:

1. **Stop Services Immediately**
   ```bash
   systemctl stop panelmerge
   ```

2. **Restore from Backup**
   ```bash
   psql panelmerge < backups/latest/database.sql
   ```

3. **Verify Data Integrity**
   ```bash
   python scripts/db/check_db.py --verify-integrity
   ```

### Performance Issues Post-Migration

#### Database Performance

```sql
-- Reindex tables after migration
REINDEX TABLE audit_log;
REINDEX TABLE admin_message;
REINDEX TABLE "user";

-- Update table statistics
ANALYZE audit_log;
ANALYZE admin_message;
ANALYZE "user";

-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE tablename IN ('audit_log', 'admin_message', 'user');
```

#### Application Performance

```bash
# Clear all caches
redis-cli FLUSHALL

# Restart application with performance monitoring
python run.py --profile

# Monitor memory usage
top -p $(pgrep -f "python run.py")
```

---

## 📞 Migration Support

### Pre-Migration Consultation

Before starting migration:
- Review this guide completely
- Test migration in staging environment
- Ensure all backups are created
- Schedule maintenance window
- Notify users of potential downtime

### Emergency Contacts

- **Technical Lead**: Primary migration support
- **Database Administrator**: Database-specific issues
- **System Administrator**: Infrastructure and deployment
- **Development Team**: Code-related issues

### Post-Migration Support

After migration completion:
- Monitor application for 24-48 hours
- Check audit logs for anomalies
- Verify all features work correctly
- Gather user feedback
- Document any issues encountered

---

**Last Updated**: 2025-07-27  
**Document Version**: 1.0  
**Maintainer**: Development Team

> This migration guide should be updated with each new version release to ensure accurate migration paths and procedures.
