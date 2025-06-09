import os
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

def db_init(app, db):
    """ Initialize the database and create an admin user if it doesn't exist.
    This function should be called within the application context.
    """
    db.init_app(app)

    password = os.getenv('DB_PASS', 'password')  # Default password if not set

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass  # Folder already exists

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

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)