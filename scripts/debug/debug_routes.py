#!/usr/bin/env python3
"""
Debug script to check what routes are registered in the app
"""

import os
import sys
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db

def debug_routes():
    """Check what routes are registered"""
    
    print("🔍 Debugging Flask Routes...")
    
    # Set up test environment
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'True'
    
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    # Create app with testing configuration
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'ENCRYPT_SENSITIVE_FIELDS': False,
    })
    
    with app.app_context():
        db.create_all()
        
        print("\n📋 Registered Routes:")
        print("=" * 60)
        
        # Get all routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'rule': rule.rule
            })
        
        # Sort routes by rule
        routes.sort(key=lambda x: x['rule'])
        
        # Print all routes
        for route in routes:
            methods = ', '.join([m for m in route['methods'] if m not in ['HEAD', 'OPTIONS']])
            print(f"{route['rule']:40} {methods:15} -> {route['endpoint']}")
        
        print("=" * 60)
        
        # Specifically check for API routes
        api_routes = [r for r in routes if '/api/' in r['rule']]
        print(f"\n🔗 API Routes Found: {len(api_routes)}")
        
        for route in api_routes:
            methods = ', '.join([m for m in route['methods'] if m not in ['HEAD', 'OPTIONS']])
            print(f"  {route['rule']:35} {methods}")
        
        # Check if saved-panels routes exist
        saved_panel_routes = [r for r in routes if 'saved-panel' in r['rule']]
        print(f"\n💾 Saved Panel Routes Found: {len(saved_panel_routes)}")
        
        for route in saved_panel_routes:
            methods = ', '.join([m for m in route['methods'] if m not in ['HEAD', 'OPTIONS']])
            print(f"  {route['rule']:35} {methods}")
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)
    
    print("\n✅ Route debugging complete!")


if __name__ == "__main__":
    debug_routes()
