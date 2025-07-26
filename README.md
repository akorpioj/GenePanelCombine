# PanelMerge

PanelMerge is a web application for researchers and clinicians to easily combine, filter, and download gene lists from multiple sources, including Genomics England PanelApp, PanelApp Australia, and user-uploaded custom gene panels.

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
- **Backend**: Python, Flask, SQLAlchemy, Pandas, openpyxl
- **Frontend**: JavaScript, Tailwind CSS, Bootstrap (admin UI)
- **APIs**: Genomics England PanelApp, PanelApp Australia
- **Database**: SQLite (local), Google Cloud SQL (production)
- **Build Tools**: npm, Tailwind CSS compiler

## API Endpoints
- `/api/panels?source={uk|aus}` - Get all panels from specified source
- `/api/genes/{entity_name}?source={uk|aus}` - Find panels containing specific gene
- `/upload_user_panel` - Upload custom gene panels
- `/uploaded_user_panels` - List uploaded panels in session
- `/remove_user_panel` - Remove uploaded panel from session

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

## License
MIT License
