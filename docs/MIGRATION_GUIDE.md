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
- **Feature Version Migration** (1.4.x → 1.5.x): Major new features (Saved Panels System)
- **Patch Version Migration** (1.4.0 → 1.4.1): Bug fixes, security patches

### Migration Complexity

| From → To | Complexity | Database Changes | Config Changes | Downtime |
|-----------|------------|------------------|----------------|----------|
| 1.5.4 → 1.5.5 | Low | 5 new tables | No | ~2-5 min |
| 1.5.3 → 1.5.4 | Low | 1 nullable column | No | ~2-5 min |
| 1.5.2 → 1.5.3 | Low | No DB changes | No | ~2-5 min |
| 1.5.1 → 1.5.2 | Low | 2 new tables, 2 FK cols | No | ~2-5 min |
| 1.5.0 → 1.5.1 | Low | 4 new tables | No | ~2-5 min |
| 1.4.x → 1.5.x | High | Major (5 new tables) | Minimal | ~10-20 min |
| 1.4.0 → 1.4.1 | Low | Yes | No | ~2-5 min |
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

## v1.5.5 Migration (KnowHow Reactions, Tags, Bookmarks, Print & New Badge)

#### From v1.5.4 to v1.5.5

**Major Changes**:
- Five new DB tables: `knowhow_bookmarks`, `knowhow_reactions`, `knowhow_tags`, `knowhow_article_tags`, `knowhow_last_visits`
- No new Python dependencies
- No configuration changes required

**Migration Steps**:

1. **Update Application Code**
   ```bash
   git fetch origin
   git checkout v1.5.5
   pip install -r requirements.txt
   ```

2. **Run Database Migrations**
   ```bash
   flask db upgrade
   # Applies: 0bd52c3d4e36, 9d38c69c3c02, a63cbbd8ad61, b7c8d9e0f1a2
   ```

3. **Restart Application**
   ```bash
   systemctl restart panelmerge
   ```

**Rollback (if needed)**:
```bash
flask db downgrade 0bd52c3d4e36-1
git checkout v1.5.4
```

---

## v1.5.4 Migration (KnowHow Search & Article Summary)

#### From v1.5.3 to v1.5.4

**Major Changes**:
- One new nullable DB column: `summary VARCHAR(512)` on `knowhow_articles`
- No new Python dependencies
- No configuration changes required

**Migration Steps**:

1. **Update Application Code**
   ```bash
   git fetch origin
   git checkout v1.5.4
   pip install -r requirements.txt
   ```

2. **Run Database Migration**
   ```bash
   flask db upgrade
   # Applies: b25d3df6625c_add_knowhow_article_summary
   ```

3. **Verify the column exists**
   ```bash
   python -c "
   from app import create_app, db
   from sqlalchemy import inspect
   app = create_app()
   with app.app_context():
       inspector = inspect(db.engine)
       cols = [c['name'] for c in inspector.get_columns('knowhow_articles')]
       print('OK' if 'summary' in cols else 'MISSING', 'summary column')
   "
   ```

4. **Restart Application**
   ```bash
   systemctl restart panelmerge
   ```

**Rollback (if needed)**:
```bash
flask db downgrade b25d3df6625c-1
# Drops the summary column — existing summaries will be lost
git checkout v1.5.3
```

---

## v1.5.3 Migration (GDPR Compliance & Retention Controls)

#### From v1.5.2 to v1.5.3

**Major Changes**:
- No database schema changes
- New Python dependency: `nh3>=0.2.14` (HTML sanitizer for KnowHow)
- New admin routes for GDPR data retention purging
- Privacy Policy updated to v1.2

**Migration Steps**:

1. **Update Application Code**
   ```bash
   git fetch origin
   git checkout v1.5.3
   pip install -r requirements.txt
   ```

2. **Verify nh3 installed**
   ```bash
   python -c "import nh3; print(nh3.__version__)"
   # Should print 0.3.3 or later
   ```

3. **No database migration required**
   - Skip `flask db upgrade` — no schema changes in this release

4. **Restart Application**
   ```bash
   # Restart your WSGI server, e.g.:
   systemctl restart panelmerge
   ```

**Rollback (if needed)**:
```bash
git checkout v1.5.2
pip install -r requirements.txt
# No DB rollback needed — no schema was changed
```

---

## v1.5.2 Migration (Dynamic KnowHow & Session Fix)

#### From v1.5.1 to v1.5.2

**Major Changes**:
- Dynamic KnowHow category system (replaces 10 hardcoded sections)
- New `KnowhowCategory` and `KnowhowSubcategory` models
- `subcategory_id` FK added to `knowhow_articles` and `knowhow_links`
- Logout session ordering fix (no config changes required)

**Migration Steps**:

1. **Backup Current System**
   ```bash
   mkdir -p backups/v1.5.1-$(date +%Y%m%d-%H%M%S)
   pg_dump panelmerge > backups/v1.5.1-$(date +%Y%m%d-%H%M%S)/database.sql
   ```

2. **Update Application Code**
   ```bash
   git fetch origin
   git checkout v1.5.2
   pip install -r requirements.txt
   npm run build:css
   ```

3. **Run Database Migration**
   ```bash
   flask db upgrade
   # Should show: (head)
   ```

4. **Verify New Tables**
   ```bash
   python -c "
   from app import create_app, db
   from sqlalchemy import inspect
   app = create_app()
   with app.app_context():
       inspector = inspect(db.engine)
       tables = inspector.get_table_names()
       for t in ['knowhow_categories', 'knowhow_subcategories']:
           print('OK' if t in tables else 'MISSING', t)
   "
   ```

5. **First-visit auto-seed**
   - Navigate to `/knowhow/` while logged in — the 10 default categories are created automatically if the table is empty.

6. **Restart Services**
   ```bash
   systemctl restart panelmerge
   ```

---

## v1.5.1 Migration (Literature Review Foundation)

#### From v1.5.0 to v1.5.1

**Major Changes**:
- New `litreview` Flask blueprint at `/litreview` (login required)
- 4 new database tables for the LitReview Phase 1 schema
- New Python dependencies: `biopython>=1.81`, `xmltodict>=0.13.0`

**Migration Steps**:

1. **Backup Current System**
   ```bash
   mkdir -p backups/v1.5.0-$(date +%Y%m%d-%H%M%S)
   pg_dump panelmerge > backups/v1.5.0-$(date +%Y%m%d-%H%M%S)/database.sql
   ```

2. **Update Application Code**
   ```bash
   git fetch origin
   git checkout v1.5.1
   
   # Install new LitReview dependencies
   pip install -r requirements.txt
   
   npm run build:css
   ```

3. **Run Database Migration**
   ```bash
   # Apply LitReview tables migration
   flask db upgrade
   
   # Verify migration status
   flask db current
   # Should show: a1b2c3d4e5f6 (head)
   
   # Verify all 4 LitReview tables
   python -c "
   from app import create_app, db
   from sqlalchemy import inspect
   app = create_app()
   with app.app_context():
       inspector = inspect(db.engine)
       tables = inspector.get_table_names()
       litreview_tables = ['literature_searches', 'literature_articles', 'search_results', 'user_article_actions']
       print('LitReview Tables:')
       for table in litreview_tables:
           if table in tables:
               cols = len(inspector.get_columns(table))
               idxs = len(inspector.get_indexes(table))
               print(f'  ✅ {table} ({cols} columns, {idxs} indexes)')
           else:
               print(f'  ❌ {table} - MISSING')
   "
   ```

4. **Verify LitReview Models and Blueprint**
   ```bash
   python -c "
   from app import create_app
   from app.models import LiteratureSearch, LiteratureArticle, SearchResult, UserArticleAction
   app = create_app()
   with app.app_context():
       print('✅ LitReview Models:', LiteratureSearch.__tablename__, LiteratureArticle.__tablename__)
       print('✅ Blueprint registered at /litreview')
   "
   ```

5. **Restart Services**
   ```bash
   systemctl restart panelmerge
   # No Redis restart needed
   ```

---

## v1.5.0 Migration (Saved Panels System)

#### From v1.4.x to v1.5.0

**Major Changes**:
- Complete saved panels system with 5 new database tables
- Full CRUD API with authentication and audit trail
- Panel versioning and change tracking system
- Panel sharing and collaboration features
- New audit action types for panel operations (PANEL_CREATE, PANEL_UPDATE, PANEL_SHARE, PANEL_LIST)
- Enhanced change tracking with PANEL_CREATED type
- Database enum migrations using Flask-Migrate
- User time format preference (12h/24h clock display)
- Enhanced timezone and time display system with user preferences
- JavaScript-based dynamic time format rendering
- **Export Templates System** (13/10/2025) - Save and reuse export format preferences
  - New `export_templates` table with user-specific templates
  - Template management API endpoints
  - Quick template selection in export wizard
  - Usage tracking and default template support

**Migration Steps**:

1. **Backup Current System**
   ```bash
   # Create backup directory
   mkdir -p backups/v1.4.x-$(date +%Y%m%d-%H%M%S)
   
   # Backup database
   pg_dump panelmerge > backups/v1.4.x-$(date +%Y%m%d-%H%M%S)/database.sql
   
   # Backup application
   cp -r . backups/v1.4.x-$(date +%Y%m%d-%H%M%S)/application/
   ```

2. **Update Application Code**
   ```bash
   # Pull latest code
   git fetch origin
   git checkout v1.5.0
   
   # Update dependencies (no new dependencies for this version)
   pip install -r requirements.txt
   
   # Build CSS (no changes needed)
   npm run build:css
   ```

3. **Run Database Migration**
   ```bash
   # Generate migration for new enum values and time format preference
   flask db migrate -m "Add new PANEL_* to AuditActionType and PANEL_CREATED to ChangeType enum"
   
   # Apply migration to database (includes time_format_preference column)
   flask db upgrade
   
   # Apply export templates migration (13/10/2025)
   # Migration file: 9227e34bde83_add_export_templates_table.py
   # This creates the export_templates table with indexes
   flask db upgrade
   
   # Verify migration status
   flask db current
   
   # Check enum values in database
   python scripts/check_enum_types.py
   
   # Verify time format preference column
   python -c "
   from app import create_app, db
   from sqlalchemy import inspect
   app = create_app()
   with app.app_context():
       inspector = inspect(db.engine)
       columns = [col['name'] for col in inspector.get_columns('user')]
       if 'time_format_preference' in columns:
           print('✅ time_format_preference column added successfully')
       else:
           print('❌ time_format_preference column missing')
   "
   
   # Verify export templates table
   python -c "
   from app import create_app, db
   from sqlalchemy import inspect
   app = create_app()
   with app.app_context():
       inspector = inspect(db.engine)
       tables = inspector.get_table_names()
       if 'export_templates' in tables:
           columns = [col['name'] for col in inspector.get_columns('export_templates')]
           indexes = inspector.get_indexes('export_templates')
           print('✅ export_templates table created successfully')
           print(f'   - Columns: {len(columns)}')
           print(f'   - Indexes: {len(indexes)}')
       else:
           print('❌ export_templates table missing')
   "
   ```

4. **Restart Services**
   ```bash
   # Restart application
   systemctl restart panelmerge
   
   # No Redis restart needed (no session changes)
   ```

5. **Verify New Features**
   ```bash
   # Test new audit action types
   python -c "
   from app.models import AuditActionType, ChangeType
   print('✅ New AuditActionTypes:')
   for action in ['PANEL_CREATE', 'PANEL_UPDATE', 'PANEL_SHARE', 'PANEL_LIST']:
       print(f'  - {action}: {getattr(AuditActionType, action)}')
   print('✅ New ChangeType:')
   print(f'  - PANEL_CREATED: {ChangeType.PANEL_CREATED}')
   "
   
   # Test time format preference functionality
   python -c "
   from app import create_app
   from app.models import User
   app = create_app()
   with app.app_context():
       user = User.query.first()
       if user:
           print(f'✅ User time format preference: {user.time_format_preference or \"24h (default)\"}')
           print('✅ Time format preference API endpoint: /api/timezone/preferences')
       else:
           print('ℹ️  No users found to test time format preference')
   "
   
   # Verify JavaScript timezone manager loads preferences
   echo "✅ JavaScript components updated to respect user preferences:"
   echo "  - timezone.js: loadUserPreferences() method"
   echo "  - profileManager.js: async time format detection"
   echo "  - API endpoint: /api/timezone/preferences"
   
   # Test export templates functionality
   python -c "
   from app import create_app
   from app.models import ExportTemplate
   app = create_app()
   with app.app_context():
       print('✅ Export Templates System:')
       print('   - Model: ExportTemplate')
       print('   - API Endpoints:')
       print('     - GET/POST /api/user/export-templates')
       print('     - GET/PUT/DELETE /api/user/export-templates/<id>')
       print('     - POST /api/user/export-templates/<id>/use')
       print('     - POST /api/user/export-templates/<id>/set-default')
       
       # Check if any templates exist
       count = ExportTemplate.query.count()
       print(f'   - Current templates: {count}')
   "
   ```

### Time Format Preference Feature (v1.5.0)

The v1.5.0 release includes user-configurable time format preference (12-hour vs 24-hour clock):

**New Features**:
- User profile setting for 12h/24h time display preference
- Backend filter automatically adjusts format strings based on user preference
- JavaScript components dynamically load and apply user preferences
- New API endpoint: `GET /api/timezone/preferences` returns timezone and time format settings
- Profile edit page includes dropdown selector for time format preference
- All timestamps throughout the application respect user's preference

**Database Changes**:
- Added `time_format_preference` column to `user` table (VARCHAR(10), default: '24h')
- Migration: `3d43d3ddbfa5_add_time_format_preference_to_users.py`

**Implementation Details**:
- Backend: `timezone_service.py` - `format_datetime_filter()` converts format strings
- Frontend: `timezone.js` - loads preferences via API and applies to all timestamps
- Profile: `profileManager.js` - updates current time display with user preference
- Template updates: Profile view displays time format preference, edit page includes selector

**User Experience**:
- Users can select preference in Edit Profile page under "Time Format"
- Default for new/existing users: 24-hour format
- Choice between:
  - 24-hour format: "18:53"
  - 12-hour format: "6:53 PM"
- Preference applies immediately across all timestamps in the application

### Migrating to v1.4.1 (Timezone Support)

#### From v1.4.0 to v1.4.1

**Major Changes**:
- User timezone preference support
- Timezone-aware datetime display throughout application
- Automatic timezone detection via browser
- Enhanced user profile with timezone settings

**Migration Steps**:

1. **Backup Current System**
   ```bash
   # Create backup directory
   mkdir -p backups/v1.4.0-$(date +%Y%m%d-%H%M%S)
   
   # Backup database
   pg_dump panelmerge > backups/v1.4.0-$(date +%Y%m%d-%H%M%S)/database.sql
   
   # Backup application
   cp -r . backups/v1.4.0-$(date +%Y%m%d-%H%M%S)/application/
   ```

2. **Update Application Code**
   ```bash
   # Pull latest code
   git fetch origin
   git checkout v1.4.1
   
   # Update dependencies (no new dependencies for this version)
   pip install -r requirements.txt
   npm install
   
   # Build CSS with timezone styles
   npm run build:css
   ```

3. **Run Database Migration**
   ```bash
   # Run timezone preference migration
   python scripts/migrations/add_timezone_preference.py
   
   # Verify migration
   python scripts/db/check_db.py
   ```

4. **Restart Services**
   ```bash
   # Restart application
   systemctl restart panelmerge
   
   # No Redis restart needed (session structure unchanged)
   ```

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

#### v1.4.1 Migration Scripts

1. **Timezone Preference Migration**
   ```bash
   # Location: scripts/migrations/add_timezone_preference.py
   python scripts/migrations/add_timezone_preference.py
   
   # This script will:
   # - Add timezone_preference column to user table
   # - Set default timezone to UTC for existing users
   # - Verify migration success
   ```

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

#### v1.5.x Migration Scripts (Saved Panels System)

1. **Saved Panels System Migration** - IMPLEMENTED 03/08/2025
   ```bash
   # Initialize Flask-Migrate (if not already done)
   flask db init
   
   # Create migration for saved panels tables
   flask db migrate -m "Add saved panels system - correct order"
   
   # Apply migration to database
   flask db upgrade
   
   # Verify migration status
   flask db current
   ```

   **Migration creates 5 new tables:**
   - `saved_panels` - Core panel metadata and ownership
   - `panel_versions` - Version history with timestamps and changelogs
   - `panel_genes` - Gene data with confidence levels and modifications
   - `panel_shares` - Sharing permissions and team access control
   - `panel_changes` - Detailed change tracking for diff views

   **Key Features:**
   - Foreign key relationships with proper dependency resolution
   - Circular dependency handling (saved_panels ↔ panel_versions)
   - Performance-optimized indexes for common query patterns
   - Support for version control and collaborative editing
   - Integration with existing user authentication system

2. **Time Format Preference Migration** - IMPLEMENTED 10/12/2025
   ```bash
   # Create migration for time format preference
   flask db revision -m "Add time format preference to users"
   
   # Apply migration to database
   flask db upgrade
   
   # Verify migration status
   flask db current
   ```

   **Migration adds:**
   - `time_format_preference` column to `user` table (VARCHAR(10), default: '24h')
   - Sets default value '24h' for existing users
   - Supports values: '12h' or '24h'
   
   **Migration file:** `3d43d3ddbfa5_add_time_format_preference_to_users.py`
   
   **SQL equivalent:**
   ```sql
   ALTER TABLE "user" ADD COLUMN time_format_preference VARCHAR(10);
   UPDATE "user" SET time_format_preference = '24h' WHERE time_format_preference IS NULL;
   ```

3. **Export Templates Migration** - IMPLEMENTED 13/10/2025
   ```bash
   # Create migration for export templates
   flask db revision -m "Add export templates table"
   
   # Apply migration to database
   flask db upgrade
   
   # Verify migration status
   flask db current
   
   # Verify export templates table
   python -c "
   from app import create_app, db
   from sqlalchemy import inspect
   app = create_app()
   with app.app_context():
       inspector = inspect(db.engine)
       if 'export_templates' in inspector.get_table_names():
           print('✅ export_templates table created')
           columns = inspector.get_columns('export_templates')
           print(f'   Columns: {len(columns)}')
           indexes = inspector.get_indexes('export_templates')
           print(f'   Indexes: {len(indexes)}')
       else:
           print('❌ export_templates table missing')
   "
   ```

   **Migration creates:**
   - `export_templates` table for user export preferences
   
   **Table structure:**
   - `id` - Primary key
   - `user_id` - Foreign key to user table
   - `name` - Template name (max 100 chars)
   - `description` - Optional description (max 255 chars)
   - `is_default` - Boolean flag for default template
   - `format` - Export format (excel, csv, tsv, json)
   - `include_metadata` - Boolean for metadata inclusion
   - `include_versions` - Boolean for version history
   - `include_genes` - Boolean for gene data
   - `filename_pattern` - Optional filename pattern
   - `created_at`, `updated_at` - Timestamps
   - `last_used_at` - Last usage timestamp
   - `usage_count` - Usage counter
   
   **Indexes:**
   - `idx_export_templates_user` on `user_id`
   - `idx_export_templates_default` on `user_id`, `is_default`
   - Unique constraint on `user_id`, `name`
   
   **Migration file:** `9227e34bde83_add_export_templates_table.py`
   
   **SQL equivalent:**
   ```sql
   CREATE TABLE export_templates (
       id SERIAL PRIMARY KEY,
       user_id INTEGER NOT NULL,
       name VARCHAR(100) NOT NULL,
       description VARCHAR(255),
       is_default BOOLEAN NOT NULL DEFAULT false,
       format VARCHAR(20) NOT NULL,
       include_metadata BOOLEAN NOT NULL DEFAULT true,
       include_versions BOOLEAN NOT NULL DEFAULT true,
       include_genes BOOLEAN NOT NULL DEFAULT true,
       filename_pattern VARCHAR(255),
       created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
       last_used_at TIMESTAMP,
       usage_count INTEGER NOT NULL DEFAULT 0,
       FOREIGN KEY (user_id) REFERENCES "user"(id),
       CONSTRAINT uq_user_template_name UNIQUE (user_id, name)
   );
   
   CREATE INDEX idx_export_templates_user ON export_templates(user_id);
   CREATE INDEX idx_export_templates_default ON export_templates(user_id, is_default);
   ```

4. **Export Template Audit Types Migration** - IMPLEMENTED 13/10/2025
   ```bash
   # Apply migration to add new audit action types
   flask db upgrade
   
   # Verify new enum values exist
   python verify_audit_types.py
   
   # Or run manually:
   python -c "
   from app import create_app, db
   from sqlalchemy import text
   app = create_app()
   with app.app_context():
       result = db.session.execute(text(
           '''SELECT e::text 
              FROM unnest(enum_range(NULL::auditactiontype)) AS e
              WHERE e::text LIKE \\'%EXPORT_TEMPLATE%\\';'''
       ))
       values = [row[0] for row in result]
       expected = ['PANEL_EXPORT_TEMPLATE_CREATE', 'PANEL_EXPORT_TEMPLATE_UPDATE', 'PANEL_EXPORT_TEMPLATE_DELETE']
       if all(v in values for v in expected):
           print('✅ All export template audit types added')
           for v in expected:
               print(f'   - {v}')
       else:
           print('❌ Some audit types missing')
           print(f'   Found: {values}')
           print(f'   Expected: {expected}')
   "
   ```

   **Migration adds:**
   - `PANEL_EXPORT_TEMPLATE_CREATE` - For template creation audit logs
   - `PANEL_EXPORT_TEMPLATE_UPDATE` - For template update audit logs
   - `PANEL_EXPORT_TEMPLATE_DELETE` - For template deletion audit logs
   
   **Migration file:** `b413fb2acd82_add_export_template_audit_types.py`
   
   **SQL equivalent:**
   ```sql
   -- Add new enum values to AuditActionType
   ALTER TYPE auditactiontype ADD VALUE IF NOT EXISTS 'PANEL_EXPORT_TEMPLATE_CREATE';
   ALTER TYPE auditactiontype ADD VALUE IF NOT EXISTS 'PANEL_EXPORT_TEMPLATE_UPDATE';
   ALTER TYPE auditactiontype ADD VALUE IF NOT EXISTS 'PANEL_EXPORT_TEMPLATE_DELETE';
   ```
   
   **Note:** PostgreSQL does not support removing enum values. If you need to downgrade, the enum values will remain in the database but will not be used.

#### v1.5.1 Migration Scripts (LitReview Foundation)

1. **LitReview Tables Migration** - IMPLEMENTED 22/03/2026
   ```bash
   # Apply LitReview tables migration
   flask db upgrade
   
   # Verify migration status
   flask db current
   # Should show: a1b2c3d4e5f6 (head)
   
   # Verify all 4 LitReview tables
   python -c "
   from app import create_app, db
   from sqlalchemy import inspect
   app = create_app()
   with app.app_context():
       inspector = inspect(db.engine)
       tables = inspector.get_table_names()
       litreview_tables = ['literature_searches', 'literature_articles', 'search_results', 'user_article_actions']
       for t in litreview_tables:
           if t in tables:
               cols = len(inspector.get_columns(t))
               idxs = len(inspector.get_indexes(t))
               print(f'  \u2705 {t} ({cols} columns, {idxs} indexes)')
           else:
               print(f'  \u274c {t} - MISSING')
   "
   ```

   **Migration creates 4 new tables:**
   - `literature_articles` — PubMed article metadata cache (pubmed_id, title, abstract, authors, mesh_terms, gene_mentions, doi, cache_expires_at)
   - `literature_searches` — Per-user PubMed search history (user_id, query, filters, result_count)
   - `search_results` — Junction table linking searches ↔ articles with result rank
   - `user_article_actions` — Per-user article interactions: save flag, view count, personal notes

   **Key constraints:**
   - `literature_articles.pubmed_id` has a unique constraint for cache deduplication
   - Cascade deletes on all user-owned rows
   - Composite unique constraints: `uq_search_article`, `uq_user_article_action`

   **Migration file:** `a1b2c3d4e5f6_add_litreview_tables.py`

   **SQL equivalent:**
   ```sql
   CREATE TABLE literature_articles (
       id SERIAL PRIMARY KEY,
       pubmed_id VARCHAR(20) NOT NULL,
       pmc_id VARCHAR(20),
       doi VARCHAR(255),
       title TEXT NOT NULL,
       abstract TEXT,
       authors JSON,
       journal VARCHAR(500),
       publication_date DATE,
       publication_types JSON,
       mesh_terms JSON,
       keywords JSON,
       gene_mentions JSON,
       cached_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
       cache_expires_at TIMESTAMP,
       CONSTRAINT uq_literature_articles_pubmed_id UNIQUE (pubmed_id)
   );
   
   CREATE TABLE literature_searches (
       id SERIAL PRIMARY KEY,
       user_id INTEGER NOT NULL,
       query TEXT NOT NULL,
       filters JSON,
       result_count INTEGER NOT NULL DEFAULT 0,
       created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
       FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
   );
   
   CREATE TABLE search_results (
       id SERIAL PRIMARY KEY,
       search_id INTEGER NOT NULL,
       article_id INTEGER NOT NULL,
       rank INTEGER,
       FOREIGN KEY (search_id) REFERENCES literature_searches(id) ON DELETE CASCADE,
       FOREIGN KEY (article_id) REFERENCES literature_articles(id) ON DELETE CASCADE,
       CONSTRAINT uq_search_article UNIQUE (search_id, article_id)
   );
   
   CREATE TABLE user_article_actions (
       id SERIAL PRIMARY KEY,
       user_id INTEGER NOT NULL,
       article_id INTEGER NOT NULL,
       is_saved BOOLEAN NOT NULL DEFAULT false,
       is_viewed BOOLEAN NOT NULL DEFAULT false,
       view_count INTEGER NOT NULL DEFAULT 0,
       notes TEXT,
       first_viewed_at TIMESTAMP,
       last_viewed_at TIMESTAMP,
       saved_at TIMESTAMP,
       created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
       FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
       FOREIGN KEY (article_id) REFERENCES literature_articles(id) ON DELETE CASCADE,
       CONSTRAINT uq_user_article_action UNIQUE (user_id, article_id)
   );
   ```

#### Manual Database Migration

If automatic scripts fail, use manual SQL migration:

```sql
-- Add timezone preference column (v1.4.1)
ALTER TABLE "user" ADD COLUMN timezone_preference VARCHAR(50) DEFAULT 'UTC';

-- Update existing users to have UTC timezone
UPDATE "user" SET timezone_preference = 'UTC' WHERE timezone_preference IS NULL;

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

-- Manual Saved Panels System Migration (v1.5.x)
-- Note: Use Flask-Migrate instead when possible, this is for emergency rollback

-- 1. Create enum types
CREATE TYPE panelstatus AS ENUM ('ACTIVE', 'ARCHIVED', 'DELETED', 'DRAFT');
CREATE TYPE panelvisibility AS ENUM ('PRIVATE', 'SHARED', 'PUBLIC');
CREATE TYPE changetype AS ENUM ('GENE_ADDED', 'GENE_REMOVED', 'GENE_MODIFIED', 'METADATA_CHANGED', 'CONFIDENCE_CHANGED', 'SOURCE_UPDATED');
CREATE TYPE sharepermission AS ENUM ('VIEW', 'COMMENT', 'EDIT', 'ADMIN');

-- 2. Create saved_panels table (without circular reference)
CREATE TABLE IF NOT EXISTS saved_panels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tags VARCHAR(500),
    owner_id INTEGER NOT NULL,
    status panelstatus NOT NULL DEFAULT 'ACTIVE',
    visibility panelvisibility NOT NULL DEFAULT 'PRIVATE',
    gene_count INTEGER NOT NULL DEFAULT 0,
    source_type VARCHAR(50),
    source_reference VARCHAR(255),
    current_version_id INTEGER, -- Will be added later
    version_count INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    storage_backend VARCHAR(20) NOT NULL DEFAULT 'local',
    storage_path VARCHAR(500),
    FOREIGN KEY (owner_id) REFERENCES "user"(id)
);

-- 3. Create panel_versions table
CREATE TABLE IF NOT EXISTS panel_versions (
    id SERIAL PRIMARY KEY,
    panel_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    comment TEXT,
    created_by_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    gene_count INTEGER,
    changes_summary TEXT,
    storage_path VARCHAR(500),
    FOREIGN KEY (created_by_id) REFERENCES "user"(id),
    FOREIGN KEY (panel_id) REFERENCES saved_panels(id),
    CONSTRAINT uq_panel_version UNIQUE (panel_id, version_number)
);

-- 4. Add the circular foreign key constraint
ALTER TABLE saved_panels ADD CONSTRAINT fk_saved_panels_current_version 
    FOREIGN KEY (current_version_id) REFERENCES panel_versions(id);

-- 5. Create remaining tables
CREATE TABLE IF NOT EXISTS panel_genes (
    id SERIAL PRIMARY KEY,
    panel_id INTEGER NOT NULL,
    gene_symbol VARCHAR(50) NOT NULL,
    gene_name VARCHAR(255),
    ensembl_id VARCHAR(50),
    hgnc_id VARCHAR(20),
    confidence_level VARCHAR(20),
    mode_of_inheritance VARCHAR(100),
    phenotype TEXT,
    evidence_level VARCHAR(20),
    source_panel_id VARCHAR(50),
    source_list_type VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT true,
    added_by_id INTEGER,
    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_notes TEXT,
    custom_confidence VARCHAR(20),
    is_modified BOOLEAN DEFAULT false,
    FOREIGN KEY (added_by_id) REFERENCES "user"(id),
    FOREIGN KEY (panel_id) REFERENCES saved_panels(id),
    CONSTRAINT uq_panel_gene_symbol UNIQUE (panel_id, gene_symbol)
);

CREATE TABLE IF NOT EXISTS panel_shares (
    id SERIAL PRIMARY KEY,
    panel_id INTEGER NOT NULL,
    shared_by_id INTEGER NOT NULL,
    shared_with_user_id INTEGER,
    shared_with_team_id INTEGER,
    permission_level sharepermission NOT NULL DEFAULT 'VIEW',
    can_reshare BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP,
    share_token VARCHAR(255),
    FOREIGN KEY (panel_id) REFERENCES saved_panels(id),
    FOREIGN KEY (shared_by_id) REFERENCES "user"(id),
    FOREIGN KEY (shared_with_user_id) REFERENCES "user"(id),
    CONSTRAINT check_share_target CHECK (
        (shared_with_user_id IS NOT NULL) OR 
        (shared_with_team_id IS NOT NULL) OR 
        (share_token IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS panel_changes (
    id SERIAL PRIMARY KEY,
    panel_id INTEGER NOT NULL,
    version_id INTEGER NOT NULL,
    change_type changetype NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id VARCHAR(100),
    old_value_encrypted TEXT,
    new_value_encrypted TEXT,
    changed_by_id INTEGER NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    change_reason VARCHAR(255),
    FOREIGN KEY (changed_by_id) REFERENCES "user"(id),
    FOREIGN KEY (panel_id) REFERENCES saved_panels(id),
    FOREIGN KEY (version_id) REFERENCES panel_versions(id)
);

-- 6. Create performance indexes (see Flask-Migrate file for complete list)
-- Key indexes for performance
CREATE INDEX IF NOT EXISTS idx_saved_panels_owner_status ON saved_panels(owner_id, status);
CREATE INDEX IF NOT EXISTS idx_panel_versions_panel_version ON panel_versions(panel_id, version_number);
CREATE INDEX IF NOT EXISTS idx_panel_genes_panel_symbol ON panel_genes(panel_id, gene_symbol);
CREATE INDEX IF NOT EXISTS idx_panel_shares_panel_active ON panel_shares(panel_id, is_active);
CREATE INDEX IF NOT EXISTS idx_panel_changes_panel_version ON panel_changes(panel_id, version_id);
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
    
    # Check admin_message table
    if 'admin_message' in tables:
        print('✅ admin_message table exists')
    else:
        print('❌ admin_message table missing')
    
    # Check saved panels system tables (v1.5.x)
    saved_panels_tables = ['saved_panels', 'panel_versions', 'panel_genes', 'panel_shares', 'panel_changes']
    print('\nSaved Panels System Tables:')
    for table in saved_panels_tables:
        if table in tables:
            print(f'✅ {table} - EXISTS')
        else:
            print(f'❌ {table} - MISSING')
    
    # Check timezone_preference column
    user_columns = [col['name'] for col in inspector.get_columns('user')]
    if 'timezone_preference' in user_columns:
        print('✅ timezone_preference column exists')
    else:
        print('❌ timezone_preference column missing')
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

#### New Variables in v1.4.1

No new environment variables required for v1.4.1 (timezone support uses existing configuration).

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

V1_4_1_REQUIRED_VARS = [
    'SECRET_KEY',
    'ENCRYPTION_KEY',
    'FLASK_ENV',
    'DATABASE_URL',
    'REDIS_URL',
    'SECURITY_MONITORING_ENABLED',
    'AUDIT_RETENTION_DAYS'
]

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

#### Timezone Preference Migration (v1.4.1)

```python
# migrate_timezone_preferences.py
from app import create_app
from app.models import db, User

def migrate_user_timezones():
    """Set default timezone for existing users"""
    app = create_app()
    
    with app.app_context():
        # Update users without timezone preference
        users_updated = User.query.filter(
            User.timezone_preference.is_(None)
        ).update({User.timezone_preference: 'UTC'})
        
        if users_updated > 0:
            db.session.commit()
            print(f"✅ Updated {users_updated} users with default UTC timezone")
        else:
            print("ℹ️ All users already have timezone preferences set")

if __name__ == "__main__":
    migrate_user_timezones()
```

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
# verify_migration_v1.4.1.py
from app import create_app, db
from app.models import User, AuditLog, AdminMessage, AuditActionType
from app.session_service import session_service
from app.audit_service import AuditService
from app.timezone_service import TimezoneService
import sys

def verify_migration():
    """Verify v1.4.1 migration completed successfully"""
    app = create_app()
    errors = []
    
    with app.app_context():
        # 1. Check timezone preference column
        try:
            user = User.query.first()
            if user:
                timezone = user.get_timezone()
                print(f"✅ User timezone preference accessible: {timezone}")
            else:
                print("ℹ️ No users found to test timezone preference")
        except Exception as e:
            errors.append(f"Timezone preference error: {e}")
        
        # 2. Test TimezoneService
        try:
            user_tz = TimezoneService.get_user_timezone()
            current_time = TimezoneService.now_in_user_timezone()
            formatted_time = TimezoneService.format_datetime(current_time)
            print(f"✅ TimezoneService working: {formatted_time}")
        except Exception as e:
            errors.append(f"TimezoneService error: {e}")
        
        # 3. Test timezone API endpoints
        try:
            from app.api.timezone import timezone_bp
            print("✅ Timezone API blueprint accessible")
        except Exception as e:
            errors.append(f"Timezone API error: {e}")
        
        # 4. Check database tables (existing v1.4.x checks)
        try:
            AdminMessage.query.first()
            print("✅ AdminMessage table accessible")
        except Exception as e:
            errors.append(f"AdminMessage table error: {e}")
        
        # 5. Check audit action types
        try:
            security_violation = AuditActionType.SECURITY_VIOLATION
            print("✅ New audit action types available")
        except Exception as e:
            errors.append(f"Audit action types error: {e}")
        
        # 6. Check Redis connection
        try:
            session_service.redis_client.ping()
            print("✅ Redis connection working")
        except Exception as e:
            errors.append(f"Redis connection error: {e}")
        
        # 7. Test audit logging
        try:
            AuditService.log_admin_action("Migration verification test")
            print("✅ Audit logging working")
        except Exception as e:
            errors.append(f"Audit logging error: {e}")
        
        # 8. Check encryption service
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
   - [ ] Timezone preference settings
   - [ ] Timezone-aware timestamp display
   - [ ] Automatic timezone detection
   - [ ] Time format preference selection (12h/24h)
   - [ ] Time format persistence across sessions
   - [ ] Dynamic time format updates in profile page
   - [ ] API endpoint `/api/timezone/preferences` returns correct format

---

## 🔄 Rollback Procedures

### Database Rollback

#### v1.4.1 Rollback

```bash
# Rollback timezone preference column
python -c "
from app import create_app, db
import sqlalchemy as sa
app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(sa.text('ALTER TABLE \"user\" DROP COLUMN IF EXISTS timezone_preference'))
        conn.commit()
    print('✅ Timezone preference column removed')
"
```

#### Automated Rollback

```bash
# Rollback admin messages table
python scripts/migrations/create_admin_messages_table.py rollback

# Rollback audit action types
python scripts/migrations/add_audit_action_types.py rollback
```

#### Manual Database Rollback

```sql
-- Remove timezone preference column (v1.4.1)
ALTER TABLE "user" DROP COLUMN IF EXISTS timezone_preference;

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

**Issue**: Timezone migration script fails with PostgreSQL syntax error
```bash
# The error occurs because "user" is a reserved keyword in PostgreSQL
# Solution: The migration script has been updated to use quoted table names

# If you encounter the error, ensure you're using the latest migration script:
python scripts/migrations/add_timezone_preference.py

# The script now uses: ALTER TABLE "user" instead of ALTER TABLE user
```

**Issue**: Automatic migration scripts fail
```bash
# Check database connection first
python scripts/db/check_db.py

# Run migrations with verbose output
python scripts/migrations/create_admin_messages_table.py migrate --verbose

# Check migration status
python scripts/migrations/create_admin_messages_table.py info
```

#### Saved Panels Migration Issues (v1.5.x)

**Issue**: Flask-Migrate circular dependency error
```bash
# Error: "unresolvable cycles between tables saved_panels, panel_versions"
# This is expected and handled automatically in the migration

# Check if migration completed successfully:
flask db current
# Should show: 64ca2e43ca66 (head)

# Verify tables exist:
python -c "
from app import create_app, db
from sqlalchemy import inspect
app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    saved_panels_tables = ['saved_panels', 'panel_versions', 'panel_genes', 'panel_shares', 'panel_changes']
    for table in saved_panels_tables:
        print(f'✅ {table}' if table in tables else f'❌ {table} MISSING')
"
```

**Issue**: Migration fails with "relation does not exist" error
```bash
# This indicates table creation order issue
# Solution: Reset migrations and recreate

# 1. Remove migrations directory
rm -rf migrations/

# 2. Clear alembic version table
python -c "
from app import create_app, db
from sqlalchemy import text
app = create_app()
with app.app_context():
    db.session.execute(text('DELETE FROM alembic_version'))
    db.session.commit()
    print('✅ Cleared alembic version table')
"

# 3. Reinitialize and migrate
flask db init
flask db migrate -m "Add saved panels system - correct order"
flask db upgrade
```

**Issue**: Foreign key constraint violations during migration
```bash
# Check for orphaned data before migration
python -c "
from app import create_app, db
from sqlalchemy import text
app = create_app()
with app.app_context():
    # Check for users without valid IDs
    result = db.session.execute(text('SELECT COUNT(*) FROM \"user\"'))
    print(f'User count: {result.scalar()}')
    
    # Ensure user table has data before migrating saved panels
    if result.scalar() == 0:
        print('❌ No users found - create admin user first')
    else:
        print('✅ Users exist - safe to migrate')
"
```

**Issue**: Migration succeeds but tables are empty or missing constraints
```bash
# Verify table structure
python -c "
from app import create_app, db
from sqlalchemy import inspect, text
app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    
    # Check saved_panels table structure
    if 'saved_panels' in inspector.get_table_names():
        columns = inspector.get_columns('saved_panels')
        fks = inspector.get_foreign_keys('saved_panels')
        print(f'saved_panels columns: {len(columns)}')
        print(f'saved_panels foreign keys: {len(fks)}')
        
        # Check for circular FK
        has_current_version_fk = any(fk['referred_table'] == 'panel_versions' for fk in fks)
        print(f'✅ Circular FK exists: {has_current_version_fk}')
    else:
        print('❌ saved_panels table not found')
"
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
   python verify_migration_v1.4.1.py
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

**Last Updated**: 2026-03-22  
**Document Version**: 1.2  
**Maintainer**: Development Team

> This migration guide should be updated with each new version release to ensure accurate migration paths and procedures.
