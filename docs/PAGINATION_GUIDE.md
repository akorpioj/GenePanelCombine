# Enhanced Pagination Support for Panel API

## Overview

The `/api/user/panels` GET endpoint now includes comprehensive server-side pagination support with advanced filtering and sorting capabilities.

## Server-Side Pagination Features

### 1. **Pagination Parameters**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)

### 2. **Advanced Filtering**
- `search` (string): Search in panel names and descriptions
- `status` (string): Filter by status (ACTIVE, ARCHIVED, DELETED, DRAFT)
- `visibility` (string): Filter by visibility (PRIVATE, SHARED, PUBLIC)
- `gene_count_min` (int): Minimum gene count filter
- `gene_count_max` (int): Maximum gene count filter

### 3. **Sorting Options**
- `sort_by` (string): Sort field (name, created_at, updated_at, gene_count, etc.)
- `sort_order` (string): Sort direction (asc, desc)

## API Request Examples

### Basic Pagination
```
GET /api/user/panels?page=1&per_page=20
```

### Pagination with Filters
```
GET /api/user/panels?page=2&per_page=10&search=cancer&status=ACTIVE&visibility=PRIVATE
```

### Pagination with Gene Count Filtering
```
GET /api/user/panels?page=1&per_page=25&gene_count_min=50&gene_count_max=200
```

### Pagination with Sorting
```
GET /api/user/panels?page=1&per_page=15&sort_by=gene_count&sort_order=desc
```

### Complex Query Example
```
GET /api/user/panels?page=3&per_page=10&search=hereditary&status=ACTIVE&gene_count_min=10&gene_count_max=100&sort_by=updated_at&sort_order=desc
```

## Response Format

```json
{
  "panels": [
    {
      "id": 123,
      "name": "Cardiovascular Panel",
      "description": "Panel for cardiovascular diseases",
      "gene_count": 45,
      "status": "ACTIVE",
      "visibility": "PRIVATE",
      "source_type": "manual",
      "created_at": "2025-08-09T10:00:00",
      "updated_at": "2025-08-09T15:30:00",
      "version_count": 2,
      "tags": []
    }
  ],
  "pagination": {
    "page": 3,
    "pages": 15,
    "per_page": 10,
    "total": 147
  }
}
```

## Pagination Object Details

- `page`: Current page number
- `pages`: Total number of pages
- `per_page`: Items per page
- `total`: Total number of items matching the filters

## Client-Side Integration

The JavaScript `PanelLibraryGrid` class automatically handles:

### **Intelligent Pagination Mode**
- **Server Pagination**: Used when user is authenticated and has real panels
- **Client Pagination**: Used for demo data when user is not logged in

### **Automatic Filter Synchronization**
- Filters trigger server requests with current parameters
- Sort changes reload data from server with new sort order
- Page navigation preserves all current filters and sort settings

### **Seamless User Experience**
- Pagination controls adapt to server or client mode automatically
- Filter counts reflect server-side totals when available
- Smooth transitions between filtered results

## JavaScript Usage Examples

### Initialize with Default Settings
```javascript
const panelLibrary = new PanelLibraryGrid();
// Automatically loads first page with default settings
```

### Navigate to Specific Page
```javascript
panelLibrary.goToPage(3);
// Loads page 3 with current filters and sort settings
```

### Apply Filters (Triggers Reload)
```javascript
panelLibrary.currentFilters.search = 'cancer';
panelLibrary.applyFilters();
// Resets to page 1 with search filter applied
```

### Change Sort Order (Triggers Reload)
```javascript
panelLibrary.currentSort = { field: 'gene_count', direction: 'desc' };
panelLibrary.sortAndRender();
// Resets to page 1 with new sort order
```

## Performance Benefits

### **Server-Side Processing**
- Database-level filtering and sorting (efficient for large datasets)
- Reduced network traffic (only current page data transferred)
- Faster initial page loads
- Better scalability for users with many panels

### **Smart Caching**
- Current filters and sort preserved during navigation
- Audit logging for user panel access patterns
- Optimized database queries with proper indexes

### **User Experience**
- Immediate response to pagination controls
- Consistent filter behavior across pages
- Real-time total counts and statistics

## Implementation Architecture

### **Backend (Python/Flask)**
```python
# Server handles all filtering, sorting, and pagination
query = SavedPanel.query.filter_by(owner_id=current_user.id)

# Apply filters
if search:
    query = query.filter(SavedPanel.name.contains(search))
if gene_count_min:
    query = query.filter(SavedPanel.gene_count >= int(gene_count_min))

# Apply sorting
if sort_by and hasattr(SavedPanel, sort_by):
    sort_field = getattr(SavedPanel, sort_by)
    query = query.order_by(desc(sort_field) if sort_order == 'desc' else sort_field)

# Paginate
pagination = query.paginate(page=page, per_page=per_page, error_out=False)
```

### **Frontend (JavaScript)**
```javascript
// Intelligent mode detection
if (this.useServerPagination) {
    // Server handles everything - just request the page
    this.loadPanels(page, true);
} else {
    // Client-side fallback for demo data
    this.clientSidePagination();
}
```

## Migration Notes

### **Backward Compatibility**
- Existing API calls without pagination parameters work unchanged
- Default values ensure consistent behavior
- Gradual enhancement path for existing implementations

### **Error Handling**
- Invalid page numbers handled gracefully
- Malformed filter values ignored with logging
- Fallback to demo data if server unavailable

This enhanced pagination system provides a robust, scalable solution for managing large numbers of user panels while maintaining optimal performance and user experience.
