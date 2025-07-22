from app import create_app
from app.models import User, db
import os

def check_db():
    app = create_app('development')
    with app.app_context():
        # Check if the database file exists
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        print(f"Database path: {db_path}")
        print(f"Database exists: {os.path.exists(db_path)}\n")
        
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
