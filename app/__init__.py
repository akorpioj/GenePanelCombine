from flask import Flask, render_template # Added render_template for error handlers
from .config_settings import DevelopmentConfig, ProductionConfig, TestingConfig # Your config classes
from .models import db
from .extensions import login_manager, limiter # Your uninitialized extensions
import os
from flask import redirect, url_for, flash

# Configuration mapping
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def create_app(config_name=None):
    """
    Application factory function.
    :param config_name: The name of the configuration to use (e.g., 'development',
    'testing', 'production').
    Defaults to 'development' if not provided or invalid.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Determine which configuration to load
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')

    selected_config = config_by_name.get(config_name, DevelopmentConfig)
    app.config.from_object(selected_config) # Load the selected config object

    # Load configuration from instance/config.py, if it exists (overrides above)
    # silent=True means it won't fail if the file doesn't exist.
    app.config.from_pyfile('config.py', silent=True)

    # Ensure the instance folder exists (Flask creates it on first access if needed,
    # but explicit creation can be useful if other parts of your app expect it).
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # Folder already exists

    # Initialize Flask extensions with the app instance
    db.init_app(app)
    # migrate.init_app(app, db) # Flask-Migrate needs both app and db
    login_manager.init_app(app)
    #mail.init_app(app) # Initialize other extensions
    limiter.init_app(app)
    
    # Define user_loader callback for Flask-Login here, after login_manager is initialized
    # This avoids circular import issues if the User model is in a separate models.py
    from .models import User # Import User model here

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register Blueprints
    from .main import main_bp # Assuming main_bp is defined in my_app/main/__init__.py
    app.register_blueprint(main_bp)

    from .admin import admin_bp # Assuming auth_bp is defined in my_app/admin/__init__.py
    app.register_blueprint(admin_bp)

    # You could register other Blueprints here
    # from .api import api_bp
    # app.register_blueprint(api_bp, url_prefix='/api/v1')

    # Application-level error handlers (optional, but good practice)
    @app.errorhandler(404)
    def page_not_found(e):
        # return render_template('errors/404.html'), 404 # Assuming you have a 404.html
        return "Oops! Page Not Found (404) - Custom App Handler.", 404

    @app.errorhandler(500)
    def internal_server_error(e):
        # db.session.rollback() # Good practice if using SQLAlchemy and an error occurs
        # return render_template('errors/500.html'), 500
        return "Sorry, something went wrong on our end (500) - Custom App Handler.", 500

    # Rate limit error handler
    def handle_429(e):
        flash("Too many requests. Please try again later.", "error")
        return redirect(url_for('main.index'))
    app.errorhandler(429)(handle_429)

    # Add other application setup like custom logging, context processors, etc.
    @app.shell_context_processor
    def make_shell_context():
        """Makes variables automatically available in the 'flask shell'."""
        return {'db': db, 'User': User} # Add other models or objects you use often

    app.logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    app.logger.info(f"Configuration loaded: {config_name}")
    app.logger.info(f"Application created with '{config_name}' configuration.")
    return app