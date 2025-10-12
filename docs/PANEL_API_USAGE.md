# Panel API Endpoints Usage Guide

## Overview
The `/api/user/panels` endpoint has been updated to support both creating new panels and updating existing panels. Additionally, a new endpoint `/api/user/panels/<panel_id>` provides RESTful operations for individual panels.

## Endpoints

### 1. `/api/user/panels` - Panel Collection

#### GET - List User Panels
Retrieve a paginated list of user's panels with optional filtering and sorting.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)
- `search` (string): Search in panel names
- `status` (string): Filter by status (ACTIVE, ARCHIVED, DELETED, DRAFT)
- `visibility` (string): Filter by visibility (PRIVATE, SHARED, PUBLIC)
- `sort_by` (string): Sort field (name, created_at, updated_at, gene_count)
- `sort_order` (string): Sort direction (asc, desc)

**Example Request:**
```
GET /api/user/panels?page=1&per_page=20&sort_by=updated_at&sort_order=desc
```

**Example Response:**
```json
{
  "panels": [
    {
      "id": 1,
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
    "page": 1,
    "pages": 5,
    "per_page": 20,
    "total": 89
  }
}
```

#### POST - Create New Panel
Create a new panel with genes and metadata.

**Request Body:**
```json
{
  "name": "New Panel Name",
  "description": "Panel description",
  "tags": "tag1,tag2,tag3",
  "status": "ACTIVE",
  "visibility": "PRIVATE",
  "source_type": "manual",
  "source_reference": "Reference info",
  "genes": [
    {
      "symbol": "BRCA1",
      "ensembl_id": "ENSG00000012048",
      "name": "BRCA1 DNA repair associated",
      "confidence": "High",
      "mode_of_inheritance": "Autosomal dominant",
      "phenotypes": "Breast cancer"
    },
    {
      "symbol": "BRCA2",
      "name": "BRCA2 DNA repair associated"
    }
  ]
}
```

**Alternative gene formats:**
```json
{
  "name": "Panel Name",
  "gene_list": "BRCA1,BRCA2,TP53,PALB2"
}
```

**Response (201 Created):**
```json
{
  "message": "Panel created successfully",
  "panel": {
    "id": 123,
    "name": "New Panel Name",
    "description": "Panel description",
    "gene_count": 4,
    "status": "ACTIVE",
    "visibility": "PRIVATE",
    "source_type": "manual",
    "created_at": "2025-08-09T16:00:00",
    "updated_at": "2025-08-09T16:00:00",
    "version_count": 1,
    "tags": ["tag1", "tag2", "tag3"]
  }
}
```

### 2. `/api/user/panels/<panel_id>` - Individual Panel Operations

#### GET - Get Panel Details
Retrieve detailed information about a specific panel including genes.

**Example Request:**
```
GET /api/user/panels/123
```

**Response:**
```json
{
  "panel": {
    "id": 123,
    "name": "Cardiovascular Panel",
    "description": "Panel for cardiovascular diseases",
    "gene_count": 45,
    "status": "ACTIVE",
    "visibility": "PRIVATE",
    "source_type": "manual",
    "source_reference": "Literature review 2025",
    "created_at": "2025-08-09T10:00:00",
    "updated_at": "2025-08-09T15:30:00",
    "last_accessed_at": "2025-08-09T16:45:00",
    "version_count": 2,
    "tags": ["cardiovascular", "heart"],
    "genes": [
      {
        "symbol": "MYBPC3",
        "ensembl_id": "ENSG00000134571",
        "name": "myosin binding protein C3",
        "confidence": "High",
        "mode_of_inheritance": "Autosomal dominant",
        "phenotypes": "Hypertrophic cardiomyopathy"
      }
    ]
  }
}
```

#### PUT - Update Panel
Update panel metadata and/or genes.

**Request Body (partial updates supported):**
```json
{
  "name": "Updated Panel Name",
  "description": "Updated description",
  "status": "ARCHIVED",
  "visibility": "SHARED",
  "tags": "updated,tags",
  "genes": [
    {
      "symbol": "NEW_GENE",
      "name": "New gene description"
    }
  ]
}
```

**Response:**
```json
{
  "message": "Panel updated successfully",
  "panel": {
    "id": 123,
    "name": "Updated Panel Name",
    "description": "Updated description",
    "gene_count": 1,
    "status": "ARCHIVED",
    "visibility": "SHARED",
    "updated_at": "2025-08-09T17:00:00"
  }
}
```

#### DELETE - Delete Panel
Soft delete a panel (sets status to DELETED).

**Example Request:**
```
DELETE /api/user/panels/123
```

**Response:**
```json
{
  "message": "Panel deleted successfully"
}
```

## Field Specifications

### Panel Fields
- `name` (string, max 255 chars): Panel name (required for new panels)
- `description` (string, max 1000 chars): Panel description
- `tags` (string, max 500 chars): Comma-separated tags
- `status` (enum): ACTIVE, ARCHIVED, DELETED, DRAFT
- `visibility` (enum): PRIVATE, SHARED, PUBLIC
- `source_type` (string): manual, upload, panelapp, template
- `source_reference` (string, max 1000 chars): Reference information

### Gene Fields
- `symbol` (string): Gene symbol (required)
- `ensembl_id` (string): Ensembl gene ID
- `name` (string): Gene full name
- `confidence` (string): Confidence level
- `mode_of_inheritance` (string): Inheritance pattern
- `phenotypes` (string): Associated phenotypes

## Error Responses

### 400 Bad Request
```json
{
  "error": "Panel name is required"
}
```

### 404 Not Found
```json
{
  "error": "Panel not found or access denied"
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to save panel"
}
```

## Usage Examples

### JavaScript/Fetch Examples

#### Create a new panel:
```javascript
const newPanel = {
  name: "Cancer Panel",
  description: "Comprehensive cancer gene panel",
  genes: ["BRCA1", "BRCA2", "TP53", "PALB2"],
  visibility: "PRIVATE"
};

fetch('/api/user/panels', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(newPanel)
})
.then(response => response.json())
.then(data => console.log('Panel created:', data));
```

#### Update an existing panel:
```javascript
const updates = {
  name: "Updated Cancer Panel",
  status: "ACTIVE"
};

fetch('/api/user/panels/123', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(updates)
})
.then(response => response.json())
.then(data => console.log('Panel updated:', data));
```

#### Delete a panel:
```javascript
fetch('/api/user/panels/123', {
  method: 'DELETE'
})
.then(response => response.json())
.then(data => console.log('Panel deleted:', data));
```

## Security Notes

- All endpoints require user authentication
- Users can only access/modify their own panels
- Rate limiting: 30 requests per minute per user
- All actions are logged via AuditService
- Enum values are validated on input
- Field length limits are enforced
