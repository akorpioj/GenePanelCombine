"""
PanelMerge Version Information
"""

# Application version
VERSION = "1.4.1"
VERSION_NAME = "Developer Tools & Timezone Enhanced"
RELEASE_DATE = "2025-08-02"

# Version details
VERSION_INFO = {
    "major": 1,
    "minor": 4,
    "patch": 1,
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
        "Timezone Support with Profile Integration"
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
