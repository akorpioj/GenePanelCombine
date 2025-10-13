# Export Templates Feature

## Overview

The Export Templates feature allows users to save their export format preferences for quick reuse. Users can create multiple templates with different settings and set one as default.

## Implementation Date

October 13, 2025

## Database Schema

### ExportTemplate Model

```python
class ExportTemplate(db.Model):
    id = Integer (Primary Key)
    user_id = Integer (Foreign Key to User)
    name = String(100) - Template name
    description = String(255) - Optional description
    is_default = Boolean - Whether this is the user's default template
    
    # Export settings
    format = String(20) - excel, csv, tsv, json
    include_metadata = Boolean
    include_versions = Boolean
    include_genes = Boolean
    filename_pattern = String(255) - Optional filename pattern
    
    # Metadata
    created_at = DateTime
    updated_at = DateTime
    last_used_at = DateTime
    usage_count = Integer
```

### Indexes
- `idx_export_templates_user` on `user_id`
- `idx_export_templates_default` on `user_id`, `is_default`
- Unique constraint on `user_id`, `name`

## API Endpoints

### List Templates
```http
GET /api/user/export-templates
```

**Response:**
```json
{
  "templates": [
    {
      "id": 1,
      "name": "My Excel Export",
      "description": "Export with all metadata",
      "is_default": true,
      "format": "excel",
      "include_metadata": true,
      "include_versions": true,
      "include_genes": true,
      "filename_pattern": null,
      "created_at": "2025-10-13T10:00:00",
      "updated_at": "2025-10-13T10:00:00",
      "last_used_at": "2025-10-13T11:30:00",
      "usage_count": 5
    }
  ],
  "count": 1
}
```

### Create Template
```http
POST /api/user/export-templates
```

**Request Body:**
```json
{
  "name": "My Excel Export",
  "description": "Export with all metadata",
  "is_default": true,
  "format": "excel",
  "include_metadata": true,
  "include_versions": true,
  "include_genes": true,
  "filename_pattern": "{panel_name}_{date}"
}
```

### Get Template
```http
GET /api/user/export-templates/<template_id>
```

### Update Template
```http
PUT /api/user/export-templates/<template_id>
```

**Request Body:** (same as create, all fields optional)

### Delete Template
```http
DELETE /api/user/export-templates/<template_id>
```

### Mark Template as Used
```http
POST /api/user/export-templates/<template_id>/use
```

Updates `last_used_at` and increments `usage_count`.

### Set as Default
```http
POST /api/user/export-templates/<template_id>/set-default
```

Sets this template as default and unsets others.

## Frontend Features

### Export Wizard Enhancement

#### Template Dropdown
- Displayed at the top of export wizard
- Shows all user's templates
- Default template is pre-selected (marked with ⭐)
- "-- Custom Settings --" option for manual configuration

#### Quick Actions
- **Manage Templates**: Opens template management interface
- **Save as Template**: Saves current settings as a new template

### Template Selection
When a user selects a template from the dropdown:
1. Form fields are automatically populated with template settings
2. Template's `usage_count` is incremented
3. `last_used_at` timestamp is updated

### Save Template Dialog
- Input for template name (required)
- Input for description (optional)
- Checkbox to set as default
- Shows current settings summary
- Validates template name uniqueness

## User Workflow

### Creating a Template

1. Open export wizard
2. Configure desired settings (format, options, filename)
3. Click "Save as Template"
4. Enter template name and optional description
5. Optionally set as default
6. Click "Save Template"

### Using a Template

1. Open export wizard
2. Select template from dropdown
3. Settings are automatically applied
4. Optionally modify settings
5. Click "Export"

### Managing Templates

1. Click "Manage Templates" in export wizard
2. View all templates
3. Edit, delete, or set default templates
4. See usage statistics

## Features

### Automatic Default Loading
- Default template is automatically applied when opening export wizard
- User can still override settings manually
- Selecting "-- Custom Settings --" clears template selection

### Template Statistics
- **usage_count**: How many times template has been used
- **last_used_at**: When template was last used
- **created_at**: When template was created
- Sorted by default status first, then by usage count

### Unique Names
- Template names must be unique per user
- System prevents duplicate template names
- Edit allows changing name to another unique name

### Default Template Management
- Only one template can be default per user
- Setting a new default automatically unsets the old one
- Default templates are marked with ⭐ star icon

## Security

### Authorization
- Users can only access their own templates
- All endpoints check `user_id` ownership
- Rate limiting: 30 requests per minute

### Audit Logging
- Template creation logged as PANEL_EXPORT_TEMPLATE_CREATE
- Template updates logged as PANEL_EXPORT_TEMPLATE_UPDATE
- Template deletion logged as PANEL_EXPORT_TEMPLATE_DELETE
- All actions include user_id, resource_type, and details

### Validation
- Format must be one of: excel, csv, tsv, json
- Template name is required and limited to 100 characters
- Description limited to 255 characters
- Filename pattern limited to 255 characters

## Database Migration

Migration file: `9227e34bde83_add_export_templates_table.py`

```python
def upgrade():
    # Create export_templates table with all columns and constraints
    # Create indexes
    
def downgrade():
    # Drop indexes
    # Drop table
```

To apply migration:
```bash
flask db upgrade
```

## UI Components

### Template Dropdown HTML
```html
<select id="templateSelect">
    <option value="">-- Custom Settings --</option>
    <option value="1">My Excel Export (EXCEL) ⭐</option>
    <option value="2">Quick CSV (CSV)</option>
</select>
```

### Quick Action Buttons
```html
<button id="manageTemplatesBtn">
    <i class="fas fa-cog"></i> Manage Templates
</button>
<button id="saveAsTemplateBtn">
    <i class="fas fa-save"></i> Save as Template
</button>
```

### Save Template Dialog
Modal dialog with:
- Template name input
- Description input
- Default checkbox
- Current settings summary
- Save/Cancel buttons

## JavaScript Methods

### `loadExportTemplates()`
Fetches user's templates from API.

### `applyTemplate(template)`
Applies template settings to export form fields.

### `showSaveTemplateDialog()`
Displays dialog to save current settings as template.

### `showManageTemplatesDialog()`
Shows template management interface (to be fully implemented).

## Integration Points

### Export Wizard
- Loads templates on wizard open
- Applies default template automatically
- Allows template selection and saving
- Passes template settings to export functions

### Panel Library
- Export action triggers wizard with templates
- Templates work for both single and multiple panel exports

## Error Handling

### Client-Side
- Validates template name is not empty
- Shows error messages for API failures
- Gracefully handles missing templates
- Re-enables buttons on errors

### Server-Side
- Returns 404 if template not found
- Returns 409 if template name already exists
- Returns 400 for validation errors
- Returns 500 for server errors
- Rolls back database on errors

## Benefits

1. **Time Saving**: Quickly reuse common export configurations
2. **Consistency**: Ensure same settings across exports
3. **Convenience**: One-click access to favorite formats
4. **Organization**: Named templates for different purposes
5. **Learning Curve**: Default templates guide new users
6. **Flexibility**: Can still customize settings per export

## Use Cases

### Research Team
- "Publication Export" - Excel with all metadata
- "Quick Review" - CSV with genes only
- "Full Archive" - JSON with everything

### Clinical Lab
- "Patient Report" - Excel formatted
- "Database Import" - CSV minimal
- "Backup" - JSON complete

### Data Analyst
- "R Analysis" - CSV for statistics
- "Python Import" - JSON structured
- "Excel Dashboard" - Excel formatted

## Future Enhancements

Possible improvements:
- [ ] Template sharing between users/teams
- [ ] Template import/export
- [ ] Template categories or tags
- [ ] Template preview before applying
- [ ] Bulk template operations
- [ ] Template versioning
- [ ] Clone template feature
- [ ] Template usage analytics dashboard
- [ ] Suggested templates based on usage patterns
- [ ] Template marketplace for common formats

## Testing Checklist

- [x] Database model and migration created
- [x] API endpoints implemented
- [x] Frontend methods added
- [x] Template dropdown in wizard
- [x] Template selection works
- [x] Save template dialog functional
- [x] Default template loading
- [x] Template CRUD operations
- [x] Usage statistics tracking
- [x] Authorization checks
- [x] Audit logging
- [x] Error handling
- [x] Single panel export with templates
- [x] Multiple panel export with templates
- [ ] UI/UX testing (needs user testing)
- [ ] Edge cases testing (duplicate names, etc.)

## Known Limitations

1. "Manage Templates" button in export wizard shows placeholder message (use Profile → Export Templates tab instead)
2. Filename pattern parsing not yet implemented (stored but not used)
3. No template sharing between users yet
4. Template usage analytics dashboard not yet implemented

## Documentation Updates

- [x] Created EXPORT_TEMPLATES_FEATURE.md
- [x] Updated FutureImprovements.txt
- [x] Updated MIGRATION_GUIDE.md
- [x] Updated AUDIT_TRAIL_SYSTEM.md
- [ ] Update EXPORT_WIZARD.md with template information
- [ ] Update user guide with template usage

---

**Status**: ✅ Implemented (Backend Complete, Frontend Complete - Manage UI Pending)
**Version**: 1.0
**Last Updated**: October 13, 2025

## Next Steps

1. ✅ ~~Complete wizard integration for template selection~~ - DONE
2. Implement full manage templates UI (low priority - can use profile page)
3. Add template list to profile page
4. Test all template operations with users
5. Add filename pattern parsing
6. Create user documentation/tutorial
7. Add template usage analytics dashboard
