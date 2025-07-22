from app import create_app
from app.models import User
import os

def test_auth():
    app = create_app('development')
    with app.app_context():
        # Get admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Admin user not found!")
            return
            
        # Test authentication
        test_password = os.getenv('DB_PASS', 'password')
        if admin.check_password(test_password):
            print("✅ Authentication successful!")
        else:
            print("❌ Authentication failed!")
            print(f"Password used for test: {test_password}")

if __name__ == '__main__':
    test_auth()
