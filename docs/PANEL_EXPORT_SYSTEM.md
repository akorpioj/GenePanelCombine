# Panel Export System

## Overview

The Panel Export System provides Excel export functionality for saved panels in the Panel Library. It generates comprehensive Excel workbooks with multiple sheets containing genes, metadata, and version history.

## Features

### 1. **Multi-Sheet Excel Export**
- **Genes Sheet**: Detailed gene information including symbols, names, IDs, confidence levels, phenotypes, etc.
- **Panel Metadata Sheet**: Panel information including owner, status, visibility, dates, etc.
- **Version History Sheet**: Complete version timeline with comments, changes, and access statistics
- **Combined Genes Sheet** (for multiple panels): Aggregated gene list showing which panels each gene belongs to

### 2. **Professional Formatting**
- Bold headers with blue background color
- Borders on all cells for easy reading
- Auto-fitted column widths based on content
- Autofilter enabled on all sheets for easy data filtering
- Text wrapping for long content

### 3. **Export Options**
- **Single Panel Export**: Export one panel via dropdown menu or direct API call
- **Multiple Panel Export**: Select multiple panels and export them together
- **Batch Export**: Export all selected panels in one Excel file

## Implementation

### Backend Components

#### 1. **Excel Export Module** (`app/main/panel_excel_export.py`)

Main functions:
- `generate_panel_excel(panel_ids, filename)`: Generate Excel from panel IDs
- `generate_panel_excel_from_data(panel_data, genes_data, versions_data, filename)`: Generate from data dictionaries
- `apply_excel_styling(worksheet, df)`: Apply consistent styling to sheets
- `clean_list_value(value)`: Clean list values from database
- `safe_sheet_name(name, max_length)`: Create safe Excel sheet names

#### 2. **API Endpoints** (`app/api/saved_panels.py`)

##### Export Multiple Panels
```
POST /api/user/panels/export
Body: {
    "panel_ids": [1, 2, 3],
    "filename": "my_panels_export.xlsx"  // optional
}
```

##### Export Single Panel
```
GET /api/user/panels/<panel_id>/export?filename=panel_export.xlsx
```

### Frontend Components

#### 1. **JavaScript Methods** (`app/static/js/modules/PanelActionsManager.js`)

##### Export Single Panel
```javascript
async exportPanel(panelId)
```
- Called from panel card dropdown menu
- Downloads Excel file with single panel data
- Shows success/error notifications

##### Export Selected Panels
```javascript
async exportSelected()
```
- Called from bulk actions menu
- Exports all selected panels in one Excel file
- Validates that at least one panel is selected

### User Interface

#### Individual Panel Export
1. Click the **⋮** (more options) button on any panel card
2. Select **"Export"** from the dropdown menu
3. Excel file downloads automatically

#### Bulk Panel Export
1. Select multiple panels using checkboxes
2. Click **"Export Selected"** from the actions menu at the top
3. Combined Excel file downloads with all selected panels

## Excel File Structure

### Single Panel Export

**Sheet 1: Genes**
- Gene Symbol
- Gene Name
- Ensembl ID
- HGNC ID
- Confidence Level
- Mode of Inheritance
- Phenotype
- Evidence Level
- Source Panel ID
- Source List Type
- User Notes
- Custom Confidence
- Modified (Yes/No)
- Added At

**Sheet 2: Panel Metadata**
- Panel ID
- Panel Name
- Description
- Tags
- Owner
- Status
- Visibility
- Gene Count
- Source Type
- Source Reference
- Current Version
- Version Count
- Created At
- Updated At
- Last Accessed

**Sheet 3: Version History**
- Panel Name
- Version Number
- Comment
- Created By
- Created At
- Gene Count
- Changes Summary
- Is Protected
- Access Count
- Last Accessed

### Multiple Panel Export

**Sheet 1: Combined Genes**
- Gene Symbol
- Panel Name
- Confidence Level
- Mode of Inheritance
- Phenotype
- Evidence Level

**Sheets 2-N: Individual Panel Genes** (one sheet per panel)
- Same structure as single panel "Genes" sheet

**Sheet N+1: Panel Metadata**
- Combined metadata for all exported panels

**Sheet N+2: Version History**
- Combined version history for all exported panels

## Security & Access Control

- ✅ Authentication required for all export endpoints
- ✅ Authorization checks ensure users can only export panels they own or have access to
- ✅ Shared panels can be exported if user has VIEW permission
- ✅ Rate limiting: 10 exports per minute per user
- ✅ Audit logging for all export operations

## File Naming

### Default Names
- Single panel: `{panel_name}_export_{YYYYMMDD}.xlsx`
- Multiple panels: `panels_export_{YYYYMMDD}.xlsx`

### Custom Names
- Can be specified via API parameter `filename`
- Invalid filename characters are automatically replaced with underscores

## Dependencies

- **openpyxl**: Excel file generation and manipulation
- **pandas**: Data frame creation and Excel writing
- **Flask**: File response and download handling

## Error Handling

- Invalid panel IDs → 404 Not Found
- Access denied → 403 Forbidden
- Export failure → 500 Internal Server Error with detailed message
- Network errors → User-friendly error notification in UI

## Performance Considerations

- In-memory Excel generation (no temporary files)
- Efficient bulk data retrieval with SQLAlchemy
- Streaming file response for large exports
- Database indexes on frequently queried fields

## Audit Trail

All export operations are logged with:
- Action type: PANEL_DOWNLOAD
- User ID and username
- Panel IDs and names
- Filename
- Timestamp
- IP address (if configured)

## Future Enhancements

Potential improvements:
- [ ] CSV format export option
- [ ] PDF format export with formatted reports
- [ ] Scheduled exports (email delivery)
- [ ] Export templates with custom column selection
- [ ] Export filtering (e.g., only high-confidence genes)
- [ ] Multi-language support for sheet names and headers
- [ ] Custom branding/logos in exported files
- [ ] Compress large exports as ZIP files

## Testing

To test the export functionality:

1. **Single Panel Export**:
   ```bash
   curl -X GET "http://localhost:5000/api/user/panels/1/export" \
        -H "Cookie: session=<your_session>" \
        --output panel_export.xlsx
   ```

2. **Multiple Panel Export**:
   ```bash
   curl -X POST "http://localhost:5000/api/user/panels/export" \
        -H "Content-Type: application/json" \
        -H "Cookie: session=<your_session>" \
        -d '{"panel_ids": [1, 2, 3]}' \
        --output panels_export.xlsx
   ```

3. **UI Testing**:
   - Navigate to My Panels page
   - Select one or more panels
   - Use export buttons and verify downloads

## Troubleshooting

### Export button doesn't work
- Check browser console for JavaScript errors
- Verify user is authenticated
- Check API rate limiting hasn't been exceeded

### Excel file is empty or corrupt
- Verify panels exist and have data
- Check server logs for backend errors
- Ensure openpyxl is installed: `pip install openpyxl`

### Download doesn't start
- Check browser pop-up blocker settings
- Verify Content-Disposition header is set correctly
- Check network tab in browser dev tools for response

## API Documentation

Full API documentation available at:
- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`

Navigate to the `saved-panels` namespace to see export endpoint details.
