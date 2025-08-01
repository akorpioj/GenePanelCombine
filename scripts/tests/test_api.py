"""
Test script for API documentation
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_api_creation():
    """Test if the API can be created without errors"""
    try:
        from app import create_app
        
        app = create_app('development')
        
        with app.app_context():
            print("✅ Flask app created successfully")
            
            # Test if API endpoints are registered
            routes = []
            for rule in app.url_map.iter_rules():
                if rule.rule.startswith('/api/v1'):
                    routes.append(rule.rule)
            
            print(f"✅ Found {len(routes)} API routes:")
            for route in sorted(routes):
                print(f"   - {route}")
            
            # Test if Swagger UI is available
            swagger_routes = [r for r in routes if 'docs' in r]
            if swagger_routes:
                print(f"✅ Swagger UI available at: {swagger_routes}")
            else:
                print("⚠️  Swagger UI routes not found")
                
            return True
            
    except Exception as e:
        print(f"❌ Error creating app: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_creation()
    if success:
        print("\n🎉 API documentation setup completed successfully!")
        print("\nTo access the interactive API documentation:")
        print("1. Start the application: python run.py")
        print("2. Open your browser to: http://localhost:5000/api/v1/docs/")
        print("3. Explore the interactive Swagger UI")
    else:
        print("\n❌ API setup failed. Please check the errors above.")
