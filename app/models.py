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
    password_hash = db.Column(db.String(255), nullable=False)  # Increased length for scrypt hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password) #, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 can be up to 45 chars
    visit_date = db.Column(db.DateTime, nullable=False)
    path = db.Column(db.String(255), nullable=False)
    user_agent = db.Column(db.String(255))

class PanelDownload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    download_date = db.Column(db.DateTime, nullable=False)
    panel_ids = db.Column(db.String(255), nullable=False)  # Comma-separated list of panel IDs
    list_types = db.Column(db.String(255), nullable=False)  # Comma-separated list of list types
    gene_count = db.Column(db.Integer)  # Number of genes in the downloaded list

def db_init(app):
    """
    Initializes a connection pool for a Cloud SQL instance of Postgres
    using the Cloud SQL Python Connector. The application is configured to use
    this pool for all database operations.
    """# These variables are set in the Cloud Run environment.
    db_pass = os.getenv("DB_PASS")                  # e.g. 'my-db-password'

    # --- Cloud SQL Python Connector Initialization ---   
    if app.config["CLOUD_SQL_CONNECTION_NAME"]:
        try:
            connector = Connector()

            def getconn() -> sqlalchemy.engine.base.Connection:
                conn = connector.connect(
                    app.config["CLOUD_SQL_CONNECTION_NAME"],
                    "pg8000",
                    user=app.config["DB_USER"],
                    password=app.config["DB_PASS"],
                    db=app.config["DB_NAME"],
                    ip_type=IPTypes.PRIVATE if os.getenv('CLOUD_RUN') else IPTypes.PUBLIC
                )
                return conn
        except Exception as e:
            app.logger.error(f"Failed to initialize Cloud SQL connector: {e}")
            raise

        app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+pg8000://"
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            "creator": getconn
        }
    # --- End of Connector Logic ---

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