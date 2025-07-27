#!/usr/bin/env python3
"""
Display PanelMerge version information
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def show_version():
    """Display version information"""
    try:
        from app.version import get_version_info, get_full_version
        
        version_info = get_version_info()
        
        print("🚀 PanelMerge Version Information")
        print("=" * 40)
        print(f"Version: {get_full_version()}")
        print(f"Release Date: {version_info['release_date']}")
        print()
        print("🔒 Security Features:")
        for feature in version_info['features']:
            print(f"  • {feature}")
        print()
        print("📊 Version Details:")
        print(f"  Major: {version_info['major']}")
        print(f"  Minor: {version_info['minor']}")
        print(f"  Patch: {version_info['patch']}")
        print()
        print("🎯 This is a security-enhanced release with comprehensive")
        print("   audit logging and threat detection capabilities.")
        
    except ImportError as e:
        print(f"Error importing version module: {e}")
        print("Make sure you're running this from the project root directory.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    show_version()
