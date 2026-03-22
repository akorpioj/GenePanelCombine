"""
PanelMerge Version Information
"""

# Application version
VERSION = "1.5.2"
VERSION_NAME = "Dynamic KnowHow & Session Fix"
RELEASE_DATE = "2026-03-22"

# Version details
VERSION_INFO = {
    "major": 1,
    "minor": 5,
    "patch": 2,
    "version": VERSION,
    "name": VERSION_NAME,
    "release_date": RELEASE_DATE,
    "features": [
        "User Authentication System",
        "Panel Comparison Tool", 
        "Panel Preview Feature",
        "Gene Autocomplete Search",
        "Enhanced File Upload Validation",
        "Role-Based Access Control",
        "Redis Caching for Better Performance",
        "Complete Audit Trail",
        "Interactive API Documentation",
        "Comprehensive Unit Testing Framework",
        "Timezone Support with Profile Integration",
        "Saved Panel Library with Version Control",
        "My Panels Profile Tab",
        "Multi-Format Export System (Excel, CSV, TSV, JSON)",
        "Export Wizard with Custom Templates",
        "Advanced Password Security Features",
        "Account Lockout Protection",
        "Enhanced Audit Log Viewer",
        "Database Testing Suite",
        "LitReview Module (Phase 1 Foundation)",
        "Dynamic KnowHow Categories & Subcategories",
        "Logout Session Cookie Fix"
    ]
}

def get_version():
    """Return the current version string"""
    return VERSION

def get_version_info():
    """Return detailed version information"""
    return VERSION_INFO

def get_full_version():
    """Return full version string with name"""
    return f"{VERSION} ({VERSION_NAME})"
