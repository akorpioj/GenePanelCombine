from flask import Flask, render_template # Added render_template for error handlers
from .config_settings import DevelopmentConfig, ProductionConfig, TestingConfig # Your config classes
from .extensions import login_manager, limiter, cache # Your uninitialized extensions
import os
from flask import redirect, url_for, flash
from .models import db_init, db

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

    # Add visit logging middleware
    @app.before_request
    def log_visit():
        import datetime
        from .models import Visit, db
        from flask import request
                
        # Skip static files and some endpoints
        if request.endpoint and (
            'static' in request.endpoint or 
            request.endpoint == 'main.api_panels'  # Skip API endpoints
        ):
            return

        # Get the real IP address, considering proxy headers
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip and ',' in ip:  # Get the first IP if multiple are present
            ip = ip.split(',')[0].strip()
            
        visit = Visit(
            ip_address=ip,
            visit_date=datetime.datetime.now(),
            path=request.path,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        
        try:
            db.session.add(visit)
            db.session.commit()
        except:
            db.session.rollback()  # Don't let logging errors affect the request

    # Continue with existing configuration
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')    
    selected_config = config_by_name.get(config_name, DevelopmentConfig)
    app.config.from_object(selected_config) # Load the selected config object

    # Load configuration from instance/config.py, if it exists (overrides above)
    # silent=True means it won't fail if the file doesn't exist.
    app.config.from_pyfile('config.py', silent=True)

    # Debug output for configuration
    app.logger.info(f"DB_USER: {app.config.get('DB_USER')}")
    app.logger.info(f"DB_NAME: {app.config.get('DB_NAME')}")
    app.logger.info(f"CLOUD_SQL_CONNECTION_NAME: {app.config.get('CLOUD_SQL_CONNECTION_NAME')}")

    # Ensure the instance folder exists (Flask creates it on first access if needed,
    # but explicit creation can be useful if other parts of your app expect it).
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # Folder already exists

    # Initialize Flask extensions with the app instance
    db_init(app) # Initialize the database and create an admin user if needed
    # migrate.init_app(app, db) # Flask-Migrate needs both app and db
    login_manager.init_app(app)
    #mail.init_app(app) # Initialize other extensions
    limiter.init_app(app)
    cache.init_app(app)  # Initialize Redis cache
    
    # Initialize security and encryption services
    from .encryption_service import init_encryption
    from .security_service import init_security
    from .session_service import init_session_service
    
    init_encryption(app)      # Initialize encryption service
    init_security(app)        # Initialize security service with HTTPS enforcement and headers
    init_session_service(app) # Initialize enhanced session management
    
    # Initialize comprehensive security monitoring
    try:
        from .security_monitor import init_security_monitoring
        security_monitor = init_security_monitoring(app)
        app.logger.info("Security monitoring initialized successfully")
    except Exception as e:
        app.logger.error(f"Failed to initialize security monitoring: {e}")
        # Don't fail app startup due to monitoring issues
    
    # Define user_loader callback for Flask-Login here, after login_manager is initialized
    # This avoids circular import issues if the User model is in a separate models.py
    from .models import User # Import User model here

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register Blueprints
    from .main import main_bp
    app.register_blueprint(main_bp)

    from .auth import auth_bp  # Register the new auth blueprint
    app.register_blueprint(auth_bp)

    # Register API blueprint with Swagger documentation
    from .api import api_bp
    app.register_blueprint(api_bp)

    # Register timezone API
    from .api.timezone import timezone_bp
    app.register_blueprint(timezone_bp)

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

    # Register timezone service and filters
    from .timezone_service import register_timezone_filters
    register_timezone_filters(app)

    # Add other application setup like custom logging, context processors, etc.
    @app.shell_context_processor
    def make_shell_context():
        """Makes variables automatically available in the 'flask shell'."""
        from .models import User, UserRole, Visit, PanelDownload, AuditLog, AuditActionType
        from .audit_service import AuditService
        from .timezone_service import TimezoneService
        return {
            'db': db, 
            'User': User, 
            'UserRole': UserRole, 
            'Visit': Visit, 
            'PanelDownload': PanelDownload,
            'AuditLog': AuditLog,
            'AuditActionType': AuditActionType,
            'AuditService': AuditService,
            'TimezoneService': TimezoneService
        }

    app.logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    app.logger.info(f"Configuration loaded: {config_name}")
    app.logger.info(f"Application created with '{config_name}' configuration.")
    return app