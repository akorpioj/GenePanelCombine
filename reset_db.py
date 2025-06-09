import os
import logging
from app import create_app
from app.models import db, User
from sqlalchemy.exc import SQLAlchemyError

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
                admin = User(username='admin')
                admin.set_password(os.getenv('DB_PASS', 'password'))
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
