# PanelMerge Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
