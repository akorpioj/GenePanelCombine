# PanelMerge v1.5.2

PanelMerge is a secure, enterprise-grade web application for researchers and clinicians to easily combine, filter, and download gene lists from multiple sources, including Genomics England PanelApp, PanelApp Australia, and user-uploaded custom gene panels. Features comprehensive panel library management with version control, multi-format export capabilities, and advanced security features.

## 🚀 New in v1.5.2 (March 2026)

- **Dynamic KnowHow Categories:** Admin-managed categories replace hardcoded sections — add/edit/remove categories with custom colours, descriptions, and ordering
- **KnowHow Subcategories (Folders):** Optional folder nesting within categories; articles and links assignable to subcategories
- **KnowHow Admin UI:** New `/knowhow/admin` page with hex colour picker and full CRUD for categories and subcategories
- **Logout Fix:** Session cookie now correctly cleared on logout (fixed ordering of `destroy_session()` / `logout_user()`)
- **Link Delete Button:** Hover-reveal × button on all KnowHow links (owner or admin only)

## 🚀 Previously in v1.5.0 (March 2026)

- **Saved Panel Library System:**
  - Personal panel storage with modifications for future use
  - Git-like version control with configurable retention (default: 10 versions)
  - Tag system for important versions (e.g., "v1.0-production")
  - Branch/merge capabilities for panel evolution tracking
  - Visual version timeline with branch visualization
  - Google Cloud Storage integration with multi-backend support

- **My Panels Profile Tab:**
  - Comprehensive panel management interface with sortable grid
  - Advanced filtering by name, date, source, gene count, and sharing status
  - Quick actions for edit, export, share, and delete operations
  - Inline editing of panel metadata and gene lists
  - Real-time validation and error highlighting

- **Multi-Format Export System:**
  - Export panels in Excel (.xlsx), CSV, TSV, and JSON formats
  - Excel exports include multiple sheets (genes, metadata, version history)
  - Batch export functionality for multiple panels
  - Export Wizard with custom filenames and column selection
  - Export template creation for recurring export needs
  - Template management in user profile

- **Enhanced Security Features:**
  - Password history tracking to prevent password reuse
  - Account lockout protection after multiple failed attempts
  - Single-use password reset tokens with expiration
  - Admin password override with secure temporary passwords
  - Email change verification system
  - Suspicious activity detection with geographic anomaly analysis

- **Advanced Filtering:**
  - Multi-criteria panel filtering by status, version, date, and gene count
  - Save and reuse filter configurations
  - Filter presets for common search patterns

- **Database Testing Suite:**
  - Comprehensive 50+ test suite for schema validation
  - Data integrity and security testing
  - Migration testing for schema evolution
  - Multi-environment support (SQLite/PostgreSQL)

- **LitReview Module (Preview):**
  - New Literature Review blueprint for future development
  - Placeholder for PubMed integration and literature analysis
  - Accessible via Tools menu in navigation

## 🔒 Security Features (v1.4)

- **Comprehensive Security Audit Logging:**
  - 33 audit action types including security violations, access denied events, and compliance logging
  - Real-time threat detection with automated response capabilities
  - Risk assessment scoring (0-100) for security events

- **Enterprise-Grade Security Monitoring:**
  - Automated detection of SQL injection, path traversal, and brute force attacks
  - Suspicious user agent detection and IP blocking
  - File upload security validation with malicious content detection
  - Rate limiting and behavioral anomaly detection

- **Advanced Session Management:**
  - Enhanced session security with individual session revocation
  - Redis-based session storage with secure token rotation
  - Session hijacking protection and privilege escalation monitoring

- **Data Encryption & Compliance:**
  - Complete data encryption at rest and in transit
  - GDPR compliance logging and regulatory event tracking
  - Comprehensive audit trail for forensic analysis

## Features

- **PanelApp Integration:**
  - Search and select gene panels from Genomics England PanelApp (UK) and PanelApp Australia.
  - Filter genes by rating (e.g., Green, Amber, Red) and disease group.
  - Search by panel name, description, disease group, or gene name (e.g., "BRCA1").
  - View panel details and gene counts before combining.

- **Enhanced Search Capabilities:**
  - Text-based search across panel names, descriptions, and disease groups.
  - Gene-based search to find panels containing specific genes.
  - Combined search results with duplicate removal.
  - Real-time filtering with debounced input.

- **User Panel Upload:**
  - Upload your own gene panels in Excel (.xls, .xlsx), CSV, or TSV format.
  - Flexible column naming: accepts "gene", "genes", "entity_name", or "genesymbol" (case-insensitive).
  - Drag-and-drop or click-to-select multiple files.
  - Prevents duplicate uploads and allows removal of files before and after upload.
  - Uploaded panels are stored per session and can be combined with PanelApp panels.

- **Gene List Generation:**
  - Combine selected PanelApp panels and user-uploaded panels into a single Excel file.
  - Each user-uploaded panel appears as a separate sheet in the Excel output.
  - The "Combined list" sheet includes all unique genes, with a column indicating the source panel(s), including user panel file names.

- **Modern, User-Friendly UI:**
  - Tabbed interface for UK, Australia, and Upload Panel workflows.
  - Real-time feedback on upload status, file list, and errors.
  - Responsive design using Tailwind CSS and Bootstrap (for admin pages).
  - Header navigation with version history tracking.

- **Saved Panel Library:**
  - Personal panel storage with complete version control
  - Share panels with other users and manage permissions
  - Comprehensive panel metadata tracking
  - Google Cloud Storage backend with local file system backup
  - Automatic versioning with optional commit messages

- **My Panels Management:**
  - Dedicated profile tab for managing saved panels
  - Visual version timeline with branch visualization
  - Advanced search and filtering capabilities
  - Inline editing with real-time validation
  - Quick actions for common operations

- **Multi-Format Export:**
  - Export panels in Excel, CSV, TSV, and JSON formats
  - Customizable export templates for recurring needs
  - Batch export for multiple panels simultaneously
  - Include metadata and version history in exports

- **Admin Dashboard:**
  - Login-protected admin area for managing users and viewing download logs
  - **Site Messages System**: Create and manage announcements displayed on the main page
    - Support for Info, Success, Warning, and Error message types with color coding
    - Optional expiration dates for automatic message removal
    - Live preview when creating messages
    - Toggle active/inactive status for immediate control
    - Full audit logging for all administrative actions
  - **Account Management**: Unlock locked accounts and manage security settings
  - **Enhanced Audit Log Viewer**: Advanced filtering and search capabilities

- **Flexible Database Support:**
  - Can run with or without database (set WITHOUT_DB=True in .env)
  - SQLite (local development) or Cloud SQL (production) supported
  - Support for multiple storage backends (GCS, local file system)

## Usage

1. **Search for Panels:**
   - Use the search field to find panels by name, disease group, or gene name.
   - Examples: "BRCA1" (gene), "cardiac" (panel name), "heart disease" (description).

2. **Select and Configure:**
   - Choose panels from UK or Australian PanelApp using the tabbed interface.
   - Select gene confidence levels (Green, Amber, Red) for each panel.
   - Optionally upload your own gene panel files via the Upload Panel tab.

3. **Generate Combined List:**
   - Click "Generate Gene List" to download a combined Excel file.
   - Each source appears as a separate sheet with a combined summary sheet.

## File Upload Details
- **Supported formats**: `.csv`, `.tsv`, `.xls`, `.xlsx`.
- **Required column**: One of `gene`, `genes`, `entity_name`, or `genesymbol` (case-insensitive).
- **Session-based**: Uploaded files are stored per session and not shared between users.
- **Multiple files**: Upload multiple panels at once with duplicate prevention.

## Technologies Used
- **Backend**: Python, Flask, SQLAlchemy, Pandas, openpyxl, Redis
- **Frontend**: JavaScript, Tailwind CSS, Bootstrap (admin UI)
- **Security**: Enterprise encryption service, comprehensive audit logging, threat detection, account lockout
- **Storage**: Google Cloud Storage (primary), Local file system (backup), Multi-backend architecture
- **APIs**: Genomics England PanelApp, PanelApp Australia, Saved Panel Management API
- **Database**: PostgreSQL (production), SQLite (local/testing), Redis (caching/sessions)
- **Build Tools**: npm, Tailwind CSS compiler
- **Testing**: pytest, unittest, comprehensive database and API testing
- **Deployment**: Google Cloud Platform with Cloud SQL and Cloud Storage

## API Endpoints

### Panel Discovery
- `/api/panels?source={uk|aus}` - Get all panels from specified source
- `/api/genes/{entity_name}?source={uk|aus}` - Find panels containing specific gene

### User Panel Upload
- `/upload_user_panel` - Upload custom gene panels
- `/uploaded_user_panels` - List uploaded panels in session
- `/remove_user_panel` - Remove uploaded panel from session

### Saved Panel Library (15 new endpoints)
- `/api/user/panels` - List user's saved panels
- `/api/user/panels` (POST) - Save new panel
- `/api/user/panels/{id}` - Get specific panel
- `/api/user/panels/{id}` (PUT) - Update panel
- `/api/user/panels/{id}` (DELETE) - Delete panel
- `/api/user/panels/{id}/versions` - List panel versions
- `/api/user/panels/{id}/versions/{version}` - Get specific version
- `/api/user/panels/{id}/versions/{version}/restore` - Restore version
- `/api/user/panels/{id}/diff/{v1}/{v2}` - Compare versions
- `/api/user/panels/{id}/merge` - Merge updates
- `/api/user/panels/{id}/share` - Share panel
- `/api/user/panels/{id}/duplicate` - Duplicate panel
- `/api/user/panels/{id}/export/{format}` - Export panel
- `/api/user/panels/import` - Import panel
- `/api/shared/panels` - List shared panels

### System
- `/api/version` - Application version information

### Admin (requires admin role)
- `/admin/messages` - Admin message management
- `/admin/messages/create` - Create new site messages
- `/admin/unlock-account` - Unlock locked user accounts

## Development
```bash
# Install dependencies
npm install
pip install -r requirements.txt

# Build CSS
npm run build:css

# Run development server
python run.py
```

## Deployment
- Configure environment variables in `.env`
- Set `WITHOUT_DB=True` for database-free operation
- Use `SQLITE_DB_PATH` for local SQLite database
- Deploy to cloud with Google Cloud SQL for production

### Database Setup
- **Google Cloud PostgreSQL**: See [`docs/GOOGLE_CLOUD_POSTGRESQL_SETUP.md`](docs/GOOGLE_CLOUD_POSTGRESQL_SETUP.md) for complete setup instructions
- **Google Cloud Storage**: See [`docs/GOOGLE_CLOUD_STORAGE_SETUP.md`](docs/GOOGLE_CLOUD_STORAGE_SETUP.md) for storage backend configuration
- **Quick Reference**: See [`docs/POSTGRESQL_QUICK_REFERENCE.md`](docs/POSTGRESQL_QUICK_REFERENCE.md) for daily operations
- **Storage Reference**: See [`docs/STORAGE_QUICK_REFERENCE.md`](docs/STORAGE_QUICK_REFERENCE.md) for storage operations
- **Testing**: Comprehensive database testing framework with 50+ test cases

## Documentation

### Core Documentation
- [`CHANGELOG.md`](CHANGELOG.md) - Complete version history and changes
- [`docs/FutureImprovements.txt`](docs/FutureImprovements.txt) - Feature roadmap and implementation status
- [`docs/UPDATE_CHECKLIST.md`](docs/UPDATE_CHECKLIST.md) - Version update checklist and procedures

### Feature Documentation
- [`docs/LITREVIEW_FEATURES.md`](docs/LITREVIEW_FEATURES.md) - Literature Review feature specification
- [`docs/PROFILE_TEMPLATES_IMPLEMENTATION.md`](docs/PROFILE_TEMPLATES_IMPLEMENTATION.md) - Export template system
- [`docs/MY_PANELS_PROFILE_TAB.md`](docs/MY_PANELS_PROFILE_TAB.md) - Panel library management
- [`docs/PANEL_EXPORT_SYSTEM.md`](docs/PANEL_EXPORT_SYSTEM.md) - Multi-format export system
- [`docs/EXPORT_WIZARD.md`](docs/EXPORT_WIZARD.md) - Export wizard documentation

### Security Documentation
- [`docs/SECURITY_GUIDE.md`](docs/SECURITY_GUIDE.md) - Security implementation guide
- [`docs/PASSWORD_HISTORY_IMPLEMENTATION.md`](docs/PASSWORD_HISTORY_IMPLEMENTATION.md) - Password security features
- [`docs/ACCOUNT_LOCKOUT_SYSTEM.md`](docs/ACCOUNT_LOCKOUT_SYSTEM.md) - Account lockout protection
- [`docs/PASSWORD_RESET_SYSTEM.md`](docs/PASSWORD_RESET_SYSTEM.md) - Password reset security
- [`docs/EMAIL_CHANGE_VERIFICATION_IMPLEMENTATION.md`](docs/EMAIL_CHANGE_VERIFICATION_IMPLEMENTATION.md) - Email verification

### Database & Storage
- [`docs/GOOGLE_CLOUD_POSTGRESQL_SETUP.md`](docs/GOOGLE_CLOUD_POSTGRESQL_SETUP.md) - PostgreSQL database setup guide
- [`docs/GOOGLE_CLOUD_STORAGE_SETUP.md`](docs/GOOGLE_CLOUD_STORAGE_SETUP.md) - Cloud Storage setup guide
- [`docs/POSTGRESQL_QUICK_REFERENCE.md`](docs/POSTGRESQL_QUICK_REFERENCE.md) - Database quick reference
- [`docs/STORAGE_QUICK_REFERENCE.md`](docs/STORAGE_QUICK_REFERENCE.md) - Storage quick reference

### Testing
- [`docs/TESTING_FRAMEWORK.md`](docs/TESTING_FRAMEWORK.md) - Testing framework documentation
- Database testing suite with 50+ comprehensive tests
- API testing with authentication and authorization tests

## License
MIT License
