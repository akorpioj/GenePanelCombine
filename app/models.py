import os
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
# Import the Cloud SQL Python Connector library
from google.cloud.sql.connector import Connector, IPTypes

db = SQLAlchemy()  # Add this line to define db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def db_init(app):
    """
    Initializes a connection pool for a Cloud SQL instance of Postgres
    using the Cloud SQL Python Connector. The application is configured to use
    this pool for all database operations.
    """# These variables are set in the Cloud Run environment.
    instance_connection_name = os.getenv("CLOUD_SQL_CONNECTION_NAME") # e.g. 'project:region:instance'
    db_user = os.getenv("DB_USER")                  # e.g. 'my-db-user'
    db_pass = os.getenv("DB_PASS")                  # e.g. 'my-db-password'
    db_name = os.getenv("DB_NAME")                  # e.g. 'my-database'

    # Initialize the Cloud SQL Python Connector
    connector = Connector()

    # The Cloud SQL Python Connector automatically handles IAM DB Authentication
    def getconn() -> sqlalchemy.engine.base.Connection:
        conn = connector.connect(
            instance_connection_name,
            "pg8000",
            user=db_user,
            password=db_pass,
            db=db_name,
            ip_type=IPTypes.PRIVATE
        )
        return conn

    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "creator": getconn,
        "pool_size": 5,
        "max_overflow": 2,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    }

    db.init_app(app)

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
                admin.set_password(db_pass)
                db.session.add(admin)
                db.session.commit()
                print("Database initialized and admin user created successfully!")
            else:
                print("Database already initialized and admin user exists.")
        except Exception as e:
            print(f"Error initializing database: {e}")            
            raise