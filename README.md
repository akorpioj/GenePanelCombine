# Gene Panel Combine

Gene Panel Combine is a web application for researchers and clinicians to easily combine, filter, and download gene lists from multiple sources, including Genomics England PanelApp, PanelApp Australia, and user-uploaded custom gene panels.

## Features

- **PanelApp Integration:**
  - Search and select gene panels from Genomics England PanelApp (UK) and PanelApp Australia.
  - Filter genes by rating (e.g., Green, Amber, Red) and disease group.
  - View panel details and gene counts before combining.

- **User Panel Upload:**
  - Upload your own gene panels in Excel (.xls, .xlsx), CSV, or TSV format.
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

- **Admin Dashboard:**
  - Login-protected admin area for managing users and viewing download logs.

- **Database Required:**
  - SQLite or Cloud SQL supported.

## Usage

1. Select panels from UK or Australian PanelApp, or upload your own gene panel files.
2. Filter and review gene lists as needed.
3. Click "Generate Gene List" to download a combined Excel file with all selected and uploaded panels.

## File Upload Details
- Supported formats: `.csv`, `.tsv`, `.xls`, `.xlsx`.
- Each file must have a column named `Genes` (case-insensitive).
- Uploaded files are session-based and not shared between users.

## Technologies Used
- Python, Flask, SQLAlchemy
- Tailwind CSS (main UI), Bootstrap (admin UI)
- JavaScript (for dynamic UI and uploads)
- Pandas, openpyxl (for Excel/CSV/TSV parsing)

## Deployment
- Can be run locally with SQLite or deployed to the cloud with Google Cloud SQL.
- Use `.env` for configuration options.

## License
MIT License
