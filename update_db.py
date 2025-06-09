import os
import logging
from app import create_app
from app.models import db, User, Visit, PanelDownload

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_db():
    try:
        # Create the application instance
        app = create_app('development')
        logger.info("Created app instance with development config")

        with app.app_context():
            try:
                # Get existing users before dropping tables
                existing_users = User.query.all()
                user_data = [(u.username, u.password_hash) for u in existing_users]
                logger.info(f"Backed up {len(user_data)} users")

                # Drop all tables
                db.drop_all()
                logger.info("Dropped all tables.")

                # Create all tables with new schema
                db.create_all()
                logger.info("Created all tables with new schema.")

                # Restore users
                for username, password_hash in user_data:
                    user = User(username=username)
                    user.password_hash = password_hash  # Directly set hash, no need to rehash
                    db.session.add(user)
                
                db.session.commit()
                logger.info("Restored users successfully!")

            except Exception as e:
                db.session.rollback()
                logger.error(f"Database error: {str(e)}")
                raise
    except Exception as e:
        logger.error(f"Error in update_db: {str(e)}")
        raise

if __name__ == '__main__':
    update_db()
