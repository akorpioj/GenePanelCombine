from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

#db = SQLAlchemy()
#migrate = Migrate()

login_manager = LoginManager()
# Configure LoginManager settings (can also be done in create_app after init_app)
login_manager.login_view = 'login' # Endpoint for the login page (BlueprintName.ViewFunctionName)
login_manager.login_message_category = 'info' # Category for flashed login_required messages
login_manager.login_message = "Please log in to access this page."

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"  # Use memory storage for simplicity))
)