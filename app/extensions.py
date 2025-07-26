from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

#db = SQLAlchemy()
#migrate = Migrate()

login_manager = LoginManager()
# Configure LoginManager settings
login_manager.login_view = 'auth.login'  # Updated to use auth blueprint
login_manager.login_message_category = 'info'
login_manager.login_message = "Please log in to access this page."

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    from .models import User
    return User.query.get(int(user_id))

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"  # Use memory storage for simplicity))
)

# Cache configuration
cache = Cache()