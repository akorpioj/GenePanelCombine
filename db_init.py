from app import create_app
from app.models import db, User
import os

# Create the application instance with the appropriate configuration
config_name = os.getenv('FLASK_CONFIG', 'production')
password = os.getenv('DB_PASS', 'password')  # Default password if not set
app = create_app(config_name)

# Use the app context
with app.app_context():
    try:
        db.create_all()
        # Check if admin user already exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin')
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print("Database initialized and admin user created successfully!")
        else:
            print("Database already initialized and admin user exists.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise