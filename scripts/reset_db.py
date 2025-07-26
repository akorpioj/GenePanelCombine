import os
import sys
import logging

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app
from app.models import db, User, UserRole
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_db():
    try:
        # Create the application instance
        app = create_app('development')
        logger.info("Created app instance with development config")

        with app.app_context():
            try:
                # Drop all tables
                db.drop_all()
                logger.info("Dropped all tables.")

                # Create all tables
                db.create_all()
                logger.info("Created all tables.")

                # Create admin user
                admin = User(
                    username='admin',
                    email=os.getenv('DB_EMAIL', 'admin@panelmerge.local'),
                    password_hash=generate_password_hash(os.getenv('DB_PASS', 'Admin123!')),
                    first_name='Admin',
                    last_name='User',
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True,
                )
                db.session.add(admin)
                db.session.commit()
                logger.info("Created admin user.")
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"Database error: {str(e)}")
                raise
    except Exception as e:
        logger.error(f"Error in reset_db: {str(e)}")
        raise
