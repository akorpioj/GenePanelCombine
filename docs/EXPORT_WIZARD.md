# Export Wizard for Panel Library

## Overview

The Export Wizard provides a user-friendly interface for exporting saved panels in multiple formats with customizable options. Users can choose from Excel, CSV, TSV, or JSON formats and select which data to include in the export.

## Features

### Supported Export Formats

1. **Excel (.xlsx)**
   - Multiple sheets: Genes, Panel Metadata, Version History
   - Professional formatting with styled headers and borders
   - Auto-fitted columns and autofilters
   - Best for comprehensive exports and offline analysis

2. **CSV (.csv)**
   - Single file with comma-separated values
   - Combines genes with panel metadata in flat structure
   - Universal compatibility with spreadsheet applications
   - Best for simple data import/export

3. **TSV (.tsv)**
   - Tab-separated values format
   - Similar to CSV but uses tabs as delimiters
   - Better for data with commas in fields
   - Compatible with bioinformatics tools

4. **JSON (.json)**
   - Structured hierarchical data format
   - Includes nested genes and version arrays
   - Programmatic access friendly
   - Best for API integration and data processing

### Customization Options

#### Include Panel Metadata
- Panel name, description, tags
- Owner information
- Status and visibility
- Source type and reference
- Timestamps (created, updated)

#### Include Version History
- Version numbers and comments
- Creation dates and authors
- Gene counts per version
- Change summaries
- Protection status

#### Include Genes (JSON only)
- Complete gene list with all fields
- Gene symbols, names, and IDs
- Confidence levels and inheritance
- Phenotype and evidence information
- User notes and modifications

## User Interface

### Single Panel Export

**Access:** Click ⋮ menu on any panel card → "Export"

**Wizard Steps:**
1. Modal appears with format selection
2. Choose format (Excel/CSV/TSV/JSON)
3. Toggle metadata and version options
4. Click "Export" to download
5. File downloads automatically with appropriate extension

**Format Descriptions:**
- Visual format selection with radio buttons
- Description of each format's characteristics
- Icons and helpful text for each option

### Multiple Panel Export

**Access:** Select panels → Click "Export Selected" button

**Wizard Steps:**
1. Shows count of selected panels
2. Same format selection interface
3. Same customization options
4. Exports combined data for all panels

### UI Features

- **Modal Design**: Clean, centered modal with backdrop
- **Format Cards**: Visual cards with radio selection
- **Checkboxes**: Toggle options for metadata and versions
- **Loading State**: Spinner and disabled buttons during export
- **Error Handling**: Clear error messages if export fails
- **Success Notification**: Confirmation message with format info

## API Endpoints

### Single Panel Export

```http
GET /api/user/panels/<panel_id>/export
```

**Query Parameters:**
- `format`: excel|csv|tsv|json (default: excel)
- `include_metadata`: true|false (default: true)
- `include_versions`: true|false (default: true)
- `include_genes`: true|false (default: true)
- `filename`: custom filename (optional)

**Example:**
```
GET /api/user/panels/123/export?format=json&include_versions=true
```

### Multiple Panel Export

```http
POST /api/user/panels/export
```

**Request Body:**
```json
{
    "panel_ids": [123, 456, 789],
    "format": "csv",
    "include_metadata": true,
    "include_versions": true,
    "include_genes": true,
    "filename": "my_panels.csv"
}
```

**Response:**
- Content-Type: Appropriate MIME type for format
- Content-Disposition: Attachment with filename
- Binary file data

## Format Specifications

### Excel Format

**Sheets:**
1. **Combined Genes** (multi-panel exports only)
   - Gene Symbol, Panel Name, Confidence, Inheritance, Phenotype, Evidence

2. **Genes** (per panel)
   - Gene Symbol, Gene Name, Ensembl ID, HGNC ID
   - Confidence Level, Mode of Inheritance
   - Phenotype, Evidence Level
   - Source info, User notes, Modified status

3. **Panel Metadata**
   - All panel metadata fields
   - One row per panel

4. **Version History**
   - Version details for all panels
   - Chronologically ordered

### CSV/TSV Format

**Columns:**
- Gene Symbol, Gene Name, Ensembl ID, HGNC ID
- Confidence Level, Mode of Inheritance, Phenotype, Evidence Level
- Source Panel ID, Source List Type
- Panel Name, Description, Tags (if metadata included)
- Panel Status, Owner (if metadata included)
- Current Version, Created At, Updated At (if versions included)

**Characteristics:**
- Flat structure with one row per gene
- Panel metadata repeated for each gene
- Suitable for importing into databases

### JSON Format

**Structure:**
```json
{
  "export_date": "2025-10-13T12:00:00",
  "export_format": "json",
  "panel_count": 2,
  "panels": [
    {
      "id": 123,
      "name": "Panel Name",
      "description": "Description",
      "tags": ["tag1", "tag2"],
      "status": "ACTIVE",
      "visibility": "PRIVATE",
      "gene_count": 50,
      "owner": {
        "id": 1,
        "username": "user",
        "full_name": "User Name"
      },
      "genes": [
        {
          "gene_symbol": "BRCA1",
          "gene_name": "Breast cancer 1",
          "ensembl_id": "ENSG00000012048",
          "confidence_level": "high",
          ...
        }
      ],
      "versions": [
        {
          "version_number": 2,
          "comment": "Updated genes",
          "created_at": "2025-10-12T10:00:00",
          ...
        }
      ]
    }
  ]
}
```

## Implementation Details

### Backend (Python)

**Files:**
- `app/main/panel_excel_export.py`: Export generation functions
- `app/main/routes_panel_library.py`: API route handlers

**Functions:**
- `generate_panel_excel()`: Excel with openpyxl
- `generate_panel_csv()`: CSV with pandas
- `generate_panel_tsv()`: TSV with pandas
- `generate_panel_json()`: JSON with native Python

### Frontend (JavaScript)

**Files:**
- `app/static/js/modules/PanelActionsManager.js`: Export logic and wizard

**Methods:**
- `exportPanel()`: Single panel export trigger
- `exportSelected()`: Multiple panel export trigger
- `showExportWizard()`: Display format selection modal
- `showExportWizardSingle()`: Single panel wizard variant
- `performExport()`: Execute multiple panel export
- `performSingleExport()`: Execute single panel export

**UI Components:**
- Export wizard modal with Tailwind CSS
- Format selection radio buttons
- Option checkboxes
- Cancel and Export buttons
- Loading states

## Security & Auditing

### Access Control
- Authentication required (login_required)
- Ownership verification for all panels
- Deleted panels excluded from export
- Rate limiting: 10 exports per minute

### Audit Logging
- Action type: PANEL_DOWNLOAD
- User ID and resource ID logged
- Export format recorded
- Panel IDs and names tracked
- Timestamp and IP address captured

## Error Handling

### Client-Side
- Validates panel selection
- Validates format parameter
- Shows user-friendly error messages
- Handles network errors gracefully
- Re-enables UI on errors

### Server-Side
- Validates panel access
- Validates format parameter
- Catches export generation errors
- Returns appropriate HTTP status codes
- Logs errors for debugging

## Performance

### Optimizations
- In-memory file generation (no temp files)
- Efficient pandas data frame operations
- Streaming file downloads
- Database query optimization
- Minimal memory footprint

### Scalability
- Handles multiple panels efficiently
- Large gene lists supported
- Concurrent export requests handled
- Rate limiting prevents abuse

## User Experience

### Workflow
1. User selects panel(s) to export
2. Clicks export button
3. Wizard modal appears
4. User selects format
5. User toggles options
6. Clicks "Export" button
7. File downloads automatically
8. Success notification shown

### Feedback
- Visual format cards with descriptions
- Loading spinner during export
- Progress indication
- Success/error notifications
- Downloaded file confirmation

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Edge, Safari)
- File download via Blob API
- Modal overlay with backdrop
- Responsive design
- Keyboard accessibility (ESC to close)

## Future Enhancements

Potential improvements:
- [ ] Export templates (save format preferences)
- [ ] Column selection for CSV/TSV
- [ ] Custom filename input
- [ ] Preview before export
- [ ] Scheduled exports
- [ ] Email delivery option
- [ ] Compression for large exports
- [ ] Export queue for bulk operations
- [ ] Export history tracking

## Testing

### Manual Testing
1. Export single panel in each format
2. Export multiple panels in each format
3. Toggle metadata/versions options
4. Cancel export operation
5. Test with large panels (1000+ genes)
6. Test with special characters in names
7. Verify file downloads correctly
8. Check file contents are correct

### Automated Testing
- Unit tests for export functions
- Integration tests for API endpoints
- Format validation tests
- Permission tests
- Error handling tests

## Documentation

- User guide in main documentation
- API reference in Swagger/OpenAPI
- Developer guide in code comments
- This comprehensive feature document

---

**Last Updated:** October 13, 2025
**Version:** 1.0
**Status:** Implemented and Active
