# PanelMerge Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.1] - 2026-03-22 - Literature Review Foundation

### 🚀 New Features

#### LitReview Module (Phase 1)
- **LitReview Blueprint**: New `/litreview` section with `litreview` Flask blueprint
  - Placeholder index page accessible via Tools menu (login required)
  - Foundation for PubMed search integration (Phase 1)
  - Audit trail integration on page access

#### Literature Review Database Schema
- **New Tables** (migration `a1b2c3d4e5f6_add_litreview_tables.py`):
  - `literature_articles` — Cached PubMed article metadata (pubmed_id, title, abstract, authors, MeSH terms, gene mentions, DOI, cache expiry)
  - `literature_searches` — Per-user PubMed search history (query, filters, result count)
  - `search_results` — Junction table linking searches ↔ articles with result rank
  - `user_article_actions` — Per-user article interactions: save, view count, personal notes
- All 4 tables cascade-delete on user removal
- Composite unique constraints prevent duplicate rows
- Performance indexes on all foreign keys and frequently queried columns

### 📦 Dependencies
- Added `biopython>=1.81` for PubMed Entrez API access
- Added `xmltodict>=0.13.0` for XML response parsing

### 🗃️ Database Changes
- **New Tables**: `literature_articles`, `literature_searches`, `search_results`, `user_article_actions`
- **Migration**: `a1b2c3d4e5f6_add_litreview_tables.py` (chains from `d24f652d1a59`)

### 🔄 Migration Notes
- Run `flask db upgrade` to apply the LitReview schema migration
- No configuration changes required
- Backward compatible with v1.5.0

---

## [1.5.0] - 2026-03-22 - Saved Panel Library & Security Enhanced

### 🚀 Major Features Added

#### Saved Panel Library System
- **Personal Panel Storage**: Users can now save downloaded panels with modifications for future use
  - Complete database schema with `saved_panels`, `panel_versions`, `panel_genes`, `panel_shares`, and `panel_changes` tables
  - Google Cloud Storage integration with multi-backend support (primary: GCS, backup: local file system)
  - Three dedicated storage buckets: active panels, version history, and long-term backups
  - Service account authentication with proper permissions and security
  
- **Version Control System**: Git-like versioning for saved panels
  - Configurable retention policy (default: keep last 10 versions)
  - Automatic versioning on save with optional commit messages
  - Tag system for important versions (e.g., "v1.0-production")
  - Branch/merge capabilities for panel evolution tracking
  - Visual version timeline with branch visualization

- **My Panels Profile Tab**: Comprehensive panel library management interface
  - Sortable grid view with panel thumbnails and metadata
  - Advanced filtering by name, date, source, gene count, and sharing status
  - Quick actions for edit, export, share, and delete operations
  - Inline editing of panel metadata and gene lists
  - Real-time validation and error highlighting

#### Export System Enhancements
- **Multi-Format Export**: Export panels in multiple formats
  - Excel (.xlsx) with multiple sheets (genes, metadata, version history)
  - CSV/TSV with configurable column selection
  - JSON format for programmatic access
  - Batch export functionality for multiple panels
  
- **Export Wizard**: Intuitive export interface with advanced options
  - Format selection with preview
  - Column customization with metadata and version options
  - Custom filename input for exports
  - Export template creation for recurring export needs
  - Template management in user profile

#### Security Enhancements
- **Advanced Password Security**:
  - Password history tracking to prevent password reuse
  - Configurable password history length
  - Strong password requirements enforcement
  - Secure password hashing with bcrypt
  
- **Account Lockout Protection**:
  - Automatic account lockout after multiple failed login/reset attempts
  - Configurable lockout threshold (default: 5 attempts)
  - Configurable lockout duration (default: 24 hours)
  - Email notifications to users and administrators
  - Admin interface to unlock accounts with audit trail
  - Automatic expiration for time-based locks
  - Admin accounts exempt from lockout but receive alerts
  
- **Password Reset Security**:
  - Single-use password reset tokens to prevent token reuse
  - Token expiration and validation
  - Suspicious activity detection and alerting
  - Geographic anomaly detection
  - Time-based pattern analysis
  
- **Admin Password Override**:
  - Admin can reset user passwords with proper authentication
  - Forces password change on next login
  - Generates secure temporary passwords with expiration
  - Terminates all user sessions on password reset
  - Email notification with temporary password
  - Complete audit trail for compliance
  
- **Email Change Verification**:
  - Verification required when users change email addresses
  - Old email remains active until new email is verified
  - Prevents unauthorized email hijacking
  - Email notifications to both old and new addresses

#### Advanced Search & Filtering
- **Enhanced Filtering Options**:
  - Filter panels by status, version, creation date, and gene count
  - Multi-criteria filtering with logical operators
  - Save and reuse filter configurations
  - Filter presets for common search patterns

#### API Enhancements
- **Saved Panel API Endpoints** (15 new endpoints):
  - `GET /api/user/panels` - List user's saved panels
  - `POST /api/user/panels` - Save new panel
  - `GET /api/user/panels/{id}` - Get specific panel
  - `PUT /api/user/panels/{id}` - Update panel
  - `DELETE /api/user/panels/{id}` - Delete panel
  - `GET /api/user/panels/{id}/versions` - List panel versions
  - `GET /api/user/panels/{id}/versions/{version}` - Get specific version
  - `POST /api/user/panels/{id}/versions/{version}/restore` - Restore version
  - `GET /api/user/panels/{id}/diff/{v1}/{v2}` - Compare versions
  - `POST /api/user/panels/{id}/merge` - Merge updates
  - `POST /api/user/panels/{id}/share` - Share panel
  - `POST /api/user/panels/{id}/duplicate` - Duplicate panel
  - `GET /api/user/panels/{id}/export/{format}` - Export panel
  - `POST /api/user/panels/import` - Import panel
  - `GET /api/shared/panels` - List shared panels
  
- **Enhanced Rate Limiting**:
  - Sophisticated rate limiting with user tiers
  - Per-endpoint rate limit configuration
  - User-specific rate limit overrides
  - Rate limit status in API responses

### 🔧 Improvements
- **Enhanced Audit Log Viewer**: Improved interface for reviewing security audit logs with advanced filtering
- **Profile Integration**: Seamless integration of panel library with user profile system
- **Data Versioning**: Complete tracking of panel evolution with diff capabilities
- **Storage Abstraction**: Pluggable storage backend architecture for flexibility
- **Performance Optimizations**: Improved query performance and caching strategies

### 🧪 Testing & Quality Assurance
- **Database Testing Suite**: Comprehensive testing infrastructure
  - 50+ database tests covering all operations
  - Schema validation and integrity testing
  - Migration testing for schema evolution
  - Performance testing for bulk operations
  - Security testing for data encryption and SQL injection prevention
  - Multi-environment support (SQLite for testing, PostgreSQL for production)
  - SQLAlchemy 2.0 compatible test suite

### 🗃️ Database Changes
- **New Tables**:
  - `saved_panels` - Panel metadata, ownership, and sharing permissions
  - `panel_versions` - Version history with timestamps and changelogs
  - `panel_genes` - Gene data with confidence levels and modifications
  - `panel_shares` - Sharing permissions and team access
  - `panel_changes` - Detailed change tracking for diff views
  - `password_reset_tokens` - Single-use token management
  - `password_history` - Historical password tracking
  - `account_lockouts` - Account lockout tracking and management

- **Enhanced Tables**:
  - User table extended with password history settings
  - Audit log enhancements for security events
  - Session management improvements

### 📚 Documentation
- Created comprehensive documentation for saved panel library system
- Updated security implementation guides
- Added export system documentation with examples
- Enhanced API documentation with new endpoints
- Created database testing documentation
- Updated configuration guides for new features

### 🔄 Migration Notes
- Automatic database migrations included
- Backward compatible with version 1.4.1
- No manual intervention required for standard deployments
- Google Cloud Storage setup required for cloud storage backend

## [1.4.1] - 2025-08-02 - Developer Tools & Timezone Enhanced

### 🚀 Major Features Added
- **Interactive API Documentation**: Comprehensive Swagger/OpenAPI documentation with live testing capabilities
  - Complete endpoint documentation with request/response examples
  - Interactive request testing interface
  - Automatic API schema generation
  - Developer-friendly documentation portal

- **Comprehensive Unit Testing Framework**: Enterprise-grade testing infrastructure
  - Full pytest and unittest integration
  - Automated testing for authentication, API endpoints, and core functionality
  - Test coverage analysis and reporting
  - Mock data generation for testing
  - Database migration testing capabilities

- **Enhanced Timezone Support**: User-centric timezone management system
  - Automatic timezone detection using browser Intl API
  - User timezone preferences stored in database
  - Timezone-aware datetime display throughout application
  - Profile page integration for timezone management
  - Real-time current time display
  - Priority-based timezone selection (user preference > session > browser > UTC)

### 🔧 Improvements
- **Profile Management**: Enhanced user profile page with timezone information and management
- **User Experience**: Cleaner UI with timezone information properly integrated into profile workflow
- **Documentation**: Updated comprehensive timezone system documentation
- **Bug Fixes**: Fixed profile update audit logging and current time display issues
- **Template Fix**: Fixed corrupted HTML in audit logs template causing Jinja2 UndefinedError

### 🧪 Testing & Quality Assurance
- **Test Framework**: Complete test infrastructure setup
- **API Testing**: Automated testing of all REST endpoints
- **Authentication Testing**: Comprehensive user authentication flow testing
- **Database Testing**: Migration and data integrity testing
- **Cache Testing**: Redis caching functionality testing

## [1.4.0] - 2025-07-27 - Security Enhanced

### 🔒 Security Features Added
- **Comprehensive Security Audit Logging**: Implemented enterprise-grade audit system with 33 action types
- **Automated Threat Detection**: Real-time monitoring for SQL injection, path traversal, and brute force attacks
- **Security Violation Tracking**: Detailed logging with severity levels (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- **Enhanced Session Management**: Individual session revocation and Redis-based secure session storage
- **Data Encryption**: Complete encryption service for data at rest and in transit
- **Compliance Logging**: GDPR and regulatory compliance event tracking
- **Risk Assessment**: Automated risk scoring system (0-100 scale) for security events
- **Behavioral Analysis**: Anomaly detection for suspicious user behavior patterns
- **File Upload Security**: Malicious content detection and file type validation
- **IP Blocking**: Automatic blocking of suspicious IP addresses with rate limiting

### 🎛️ Admin Features Added
- **Admin Message System**: Site-wide announcement system for communicating with users
  - Create, edit, and delete messages visible on the main page
  - Message types: Info, Success, Warning, Error with color coding
  - Optional expiration dates for automatic message removal
  - Live preview when creating messages
  - Toggle active/inactive status for immediate control
  - Full audit logging for all message operations
- **Enhanced Admin Dashboard**: Streamlined navigation between user management, site messages, and audit logs

### 🛡️ Security Components Added
- `security_monitor.py`: Automated security monitoring service
- `audit_service.py`: Enhanced with 13 new security audit methods
- `encryption_service.py`: Enterprise-grade encryption capabilities
- Database migration for 33 audit action types
- Security monitoring middleware integration

### 🔧 Technical Improvements
- Updated database schema with new security audit action types
- Enhanced Redis integration for session management and caching
- Improved error handling and logging throughout the application
- Added comprehensive security event documentation
- Created security testing framework

### 📊 New Endpoints
- `/api/version` - Application version information API
- `/version` - Version information page
- `/admin/messages` - Admin message management interface
- `/admin/messages/create` - Create new site messages
- `/admin/messages/<id>/toggle` - Toggle message active status
- `/admin/messages/<id>/delete` - Delete admin messages
- Enhanced audit logging for all existing endpoints

### 🗃️ Database Changes
- Added 13 new audit action types: SECURITY_VIOLATION, ACCESS_DENIED, PRIVILEGE_ESCALATION, SUSPICIOUS_ACTIVITY, BRUTE_FORCE_ATTEMPT, ACCOUNT_LOCKOUT, PASSWORD_RESET, MFA_EVENT, API_ACCESS, FILE_ACCESS, DATA_BREACH_ATTEMPT, COMPLIANCE_EVENT, SYSTEM_SECURITY
- Enhanced AuditLog model with encrypted fields for sensitive data
- **New AdminMessage table**: Stores site-wide announcements with expiration support
- Migration scripts for seamless upgrade from v1.3

### 📚 Documentation
- Added comprehensive security implementation guide
- Updated README with security features
- Enhanced version history with detailed changelog
- Created security testing documentation

## [1.3.0] - 2025-07-25

### Added
- **Enhanced Gene Search**: Search by gene name (e.g., "BRCA1") to find panels containing that gene
- **Flexible Upload Columns**: Support for gene, genes, entity_name, genesymbol column names (case-insensitive)
- **Version History Page**: Added comprehensive changelog and navigation
- **Header Navigation**: Easy access to main features and version history
- **Improved Search UI**: Updated instructions with clear examples and better placeholder text
- **New API Endpoint**: /api/genes/{entity_name} for gene-based panel discovery
- **Database Flexibility**: Optional database mode with WITHOUT_DB configuration
- **App Rebranding**: Renamed from "Gene Panel Combine" to "PanelMerge"

## [1.2.0] - 2025-07-20

### Added
- Comprehensive user panel upload functionality (Excel, CSV, TSV)
- Drag-and-drop file upload interface
- Multiple file upload support with duplicate prevention
- User panels appear as separate sheets in Excel output
- Combined list now shows source panel names including user uploads
- Session-based panel management with add/remove capabilities

## [1.1.0] - 2025-06-15

### Added
- Australian PanelApp integration
- Tabbed interface for UK/Australia panel selection
- Enhanced Excel output with source indicators (GB/AUS prefixes)
- Improved caching with separate cache for each API source
- Visual indicators for panel source in dropdowns

## [1.0.0] - 2025-05-01

### Added
- Initial release with UK PanelApp integration
- Panel search and filtering by name, disease group, description
- Gene confidence level filtering (Green, Amber, Red)
- Excel file generation with combined gene lists
- Admin dashboard with user management and download tracking
- Responsive design with Tailwind CSS
- Rate limiting and caching for optimal performance

---

## Version Numbering

- **Major version** (X.0.0): Breaking changes or significant new features
- **Minor version** (1.X.0): New features that are backward compatible
- **Patch version** (1.1.X): Bug fixes and small improvements

## Security Versions

Starting with v1.4.0, all releases include comprehensive security features and audit logging. Security patches will be released as needed with appropriate version increments.
