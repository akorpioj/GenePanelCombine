"""
PanelMerge Version Information
"""

# Application version
VERSION = "1.5.3"
VERSION_NAME = "GDPR Compliance & Retention Controls"
RELEASE_DATE = "2026-03-25"

# Version details
VERSION_INFO = {
    "major": 1,
    "minor": 5,
    "patch": 3,
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
        "Logout Session Cookie Fix",
        "GDPR Retention Controls (Visit, Suspicious Activity, Download Logs)",
        "KnowHow Stored-XSS Protection (nh3 Sanitization)",
        "NCBI International Transfer Disclosure",
        "PanelGene Annotations Privacy Notices",
        "Privacy Policy v1.2 (Saved Panels, Security Infrastructure, Exports)"
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
