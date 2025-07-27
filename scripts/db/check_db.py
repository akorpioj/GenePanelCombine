import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app
from app.models import User, db

def check_db():
    app = create_app('development')
    with app.app_context():
        # Check if the database file exists
        db_path = app.config['CLOUD_SQL_CONNECTION_NAME']
        print(f"Database path: {db_path}")
        
        # Check if table exists
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables in database: {tables}")
            
            # Show table details
            for table in tables:
                columns = [col['name'] for col in inspector.get_columns(table)]
                print(f"\nTable '{table}' columns: {columns}")
        except Exception as e:
            print(f"Error checking tables: {e}")
            
        # Check for users
        try:
            users = User.query.all()
            print(f"\nUsers found: {[u.username for u in users]}")
            for user in users:
                print(f"  User '{user.username}' has password hash set: {bool(user.password_hash)}")
        except Exception as e:
            print(f"Error querying users: {e}")

if __name__ == '__main__':
    check_db()
