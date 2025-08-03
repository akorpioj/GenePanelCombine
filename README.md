# PanelMerge v1.4.1

PanelMerge is a secure, enterprise-grade web application for researchers and clinicians to easily combine, filter, and download gene lists from multiple sources, including Genomics England PanelApp, PanelApp Australia, and user-uploaded custom gene panels.

## 🚀 New in v1.4.1 (August 2025)

- **Interactive API Documentation:**
  - Swagger/OpenAPI documentation with live testing capabilities
  - Comprehensive endpoint documentation with examples
  - Interactive request/response testing interface

- **Comprehensive Unit Testing Framework:**
  - Full pytest and unittest integration
  - Automated testing for all core functionality
  - Test coverage analysis and reporting

- **Enhanced Timezone Support:**
  - User timezone preferences with automatic detection
  - Timezone-aware datetime display throughout the application
  - Profile integration for timezone management
  - Real-time current time display

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

- **Admin Dashboard:**
  - Login-protected admin area for managing users and viewing download logs.
  - **Site Messages System**: Create and manage announcements displayed on the main page
    - Support for Info, Success, Warning, and Error message types with color coding
    - Optional expiration dates for automatic message removal
    - Live preview when creating messages
    - Toggle active/inactive status for immediate control
    - Full audit logging for all administrative actions

- **Flexible Database Support:**
  - Can run with or without database (set WITHOUT_DB=True in .env).
  - SQLite (local development) or Cloud SQL (production) supported.

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
- **Security**: Enterprise encryption service, comprehensive audit logging, threat detection
- **APIs**: Genomics England PanelApp, PanelApp Australia
- **Database**: PostgreSQL (production), SQLite (local), Redis (caching/sessions)
- **Build Tools**: npm, Tailwind CSS compiler
- **Deployment**: Google Cloud Platform with Cloud SQL

## API Endpoints
- `/api/panels?source={uk|aus}` - Get all panels from specified source
- `/api/genes/{entity_name}?source={uk|aus}` - Find panels containing specific gene
- `/upload_user_panel` - Upload custom gene panels
- `/uploaded_user_panels` - List uploaded panels in session
- `/remove_user_panel` - Remove uploaded panel from session
- `/api/version` - Application version information
- `/admin/messages` - Admin message management (admin only)
- `/admin/messages/create` - Create new site messages (admin only)

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
- **Quick Reference**: See [`docs/POSTGRESQL_QUICK_REFERENCE.md`](docs/POSTGRESQL_QUICK_REFERENCE.md) for daily operations
- **Testing**: Comprehensive database testing framework with 32 test cases

## Documentation
- [`docs/FutureImprovements.txt`](docs/FutureImprovements.txt) - Feature roadmap and implementation status
- [`docs/GOOGLE_CLOUD_POSTGRESQL_SETUP.md`](docs/GOOGLE_CLOUD_POSTGRESQL_SETUP.md) - PostgreSQL database setup guide
- [`docs/POSTGRESQL_QUICK_REFERENCE.md`](docs/POSTGRESQL_QUICK_REFERENCE.md) - Database quick reference
- [`docs/TESTING_FRAMEWORK.md`](docs/TESTING_FRAMEWORK.md) - Testing framework documentation

## License
MIT License
