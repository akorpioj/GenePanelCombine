# Custom Filename Input Feature

## Overview

Added custom filename input functionality to the Export Wizard, allowing users to specify their own filenames when exporting panels from the Panel Library.

## Implementation Date

October 13, 2025

## What Changed

### Frontend Changes (`PanelActionsManager.js`)

#### 1. Single Panel Export Modal
Added custom filename input field to the export wizard:
```html
<div class="mt-4">
    <label class="block text-sm font-medium text-gray-700 mb-1">
        Custom Filename (optional)
    </label>
    <input type="text" id="customFilename" 
           placeholder="Leave empty for default filename" 
           class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm">
    <p class="text-xs text-gray-500 mt-1">File extension will be added automatically</p>
</div>
```

#### 2. Multiple Panel Export Modal
Same custom filename input added to the multiple panel export wizard.

#### 3. Event Handler Updates
- **Single Export**: Updated `showExportWizardSingle()` confirm button handler to capture `customFilename`
- **Multiple Export**: Updated `showExportWizard()` confirm button handler to capture `customFilename`

#### 4. Function Signatures Updated
- `performSingleExport(panelId, format, includeMetadata, includeVersions, customFilename = null)`
- `performExport(panelIds, format, includeMetadata, includeVersions, customFilename = null)`

#### 5. API Integration
- **Single Panel**: Added filename as query parameter
  ```javascript
  if (customFilename) {
      params.append('filename', customFilename);
  }
  ```
- **Multiple Panels**: Added filename to request body
  ```javascript
  if (customFilename) {
      requestBody.filename = customFilename;
  }
  ```

### Backend Support

The backend routes already supported the `filename` parameter:
- `GET /api/user/panels/<panel_id>/export?filename=custom_name`
- `POST /api/user/panels/export` with `{"filename": "custom_name"}` in body

No backend changes were required - the feature was already supported!

## User Experience

### Before
- Users could only download files with auto-generated names
- Single panel: `{panel_name}_export.{format}`
- Multiple panels: `panels_export.{format}`

### After
- Users can optionally provide a custom filename
- If custom filename is provided, it's used instead of the default
- File extension is automatically added based on selected format
- If left empty, defaults to original naming convention

### UI Elements
- **Label**: "Custom Filename (optional)"
- **Placeholder**: "Leave empty for default filename"
- **Help Text**: "File extension will be added automatically"
- **Styling**: Consistent with other form inputs in the modal
- **Validation**: Trim whitespace, pass to backend for sanitization

## Features

### Filename Handling
1. **Optional Input**: User can leave field empty for default behavior
2. **Automatic Extension**: Backend adds appropriate extension (.xlsx, .csv, .tsv, .json)
3. **Whitespace Trimming**: Frontend trims leading/trailing whitespace
4. **Backend Sanitization**: Backend sanitizes filename for security
5. **Audit Logging**: Custom filename is logged in audit trail

### Use Cases
1. **Descriptive Names**: `cardiac_genes_2025` instead of `panel_123_export`
2. **Versioning**: `panel_v2`, `panel_final`, `panel_reviewed`
3. **Project Names**: `research_study_cohort_1`
4. **Date Stamps**: `panels_oct_2025`
5. **Batch Organization**: `batch_1`, `batch_2` for multiple exports

## Technical Details

### Data Flow

**Single Panel Export:**
```
User Input → customFilename variable → URL query param → Backend → Sanitized filename → File download
```

**Multiple Panels Export:**
```
User Input → customFilename variable → Request body → Backend → Sanitized filename → File download
```

### Code Locations

1. **Frontend**: `app/static/js/modules/PanelActionsManager.js`
   - Lines 98-220: Single panel export wizard
   - Lines 931-1095: Multiple panel export wizard

2. **Backend**: `app/main/routes_panel_library.py`
   - Line 186: `filename = request.args.get('filename')` (single)
   - Line 257: `filename = data.get('filename')` (multiple)

3. **Export Functions**: `app/main/panel_excel_export.py`
   - Already handles optional `filename` parameter
   - Uses default if not provided
   - Sanitizes filename for security

## Testing Checklist

- [x] Frontend UI displays correctly
- [x] Input field captures user input
- [x] Empty input defaults to original behavior
- [x] Custom filename is passed to backend
- [x] File downloads with custom name
- [x] File extension added correctly
- [x] Works for all formats (Excel, CSV, TSV, JSON)
- [x] Works for single panel export
- [x] Works for multiple panel export
- [x] Whitespace trimming works
- [x] Backend sanitization prevents security issues
- [x] Audit logging includes custom filename

## Security Considerations

1. **Input Sanitization**: Backend sanitizes filename to prevent:
   - Path traversal attacks (`../../../etc/passwd`)
   - Special characters that could break file systems
   - Reserved filenames (CON, PRN, AUX, etc. on Windows)

2. **Length Limits**: Backend enforces reasonable filename length limits

3. **Character Restrictions**: Invalid characters are removed or replaced

4. **Audit Logging**: All custom filenames are logged for security auditing

## Documentation Updates

1. **EXPORT_WIZARD.md**: 
   - Added "Custom Filename" to Customization Options
   - Updated wizard steps to include filename input
   - Updated UI Features list
   - Marked feature as implemented in Future Enhancements

2. **FutureImprovements.txt**:
   - Marked "Custom filename input" as IMPLEMENTED

3. **CUSTOM_FILENAME_FEATURE.md**:
   - This comprehensive implementation document

## Example Usage

### Scenario 1: Exporting with Custom Name
1. User clicks "Export" on a panel
2. Wizard opens with format selection
3. User enters "my_cardiac_panel" in custom filename field
4. User selects Excel format
5. File downloads as `my_cardiac_panel.xlsx`

### Scenario 2: Default Behavior
1. User clicks "Export" on a panel named "BRCA Analysis"
2. Wizard opens with format selection
3. User leaves custom filename field empty
4. User selects CSV format
5. File downloads as `BRCA_Analysis_export.csv`

### Scenario 3: Multiple Panels with Custom Name
1. User selects 3 panels
2. User clicks "Export Selected"
3. Wizard shows "Exporting 3 panel(s)"
4. User enters "cardiac_study_batch_1" in custom filename field
5. User selects JSON format
6. File downloads as `cardiac_study_batch_1.json`

## Benefits

1. **Better Organization**: Users can organize exports with meaningful names
2. **No File Renaming**: Eliminates need to rename files after download
3. **Project Integration**: Files can follow project naming conventions
4. **Batch Processing**: Easier to manage multiple exports
5. **User Control**: More flexibility without breaking existing functionality

## Future Enhancements

Possible improvements for this feature:
- [ ] Filename validation preview (show what the final filename will be)
- [ ] Filename suggestions based on panel content
- [ ] Recent filename history/autocomplete
- [ ] Filename templates (e.g., `{panel_name}_{date}`)
- [ ] Bulk filename patterns for multiple exports
- [ ] Filename sanitization preview (show what characters will be removed)

## Related Features

This feature complements:
- Export format selection (Excel, CSV, TSV, JSON)
- Metadata and version inclusion options
- Single and multiple panel export
- Audit trail logging
- Export history tracking (future feature)

---

**Status**: ✅ Implemented and Active
**Version**: 1.0
**Last Updated**: October 13, 2025
