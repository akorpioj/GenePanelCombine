import os
from app import create_app # Import the factory fun
# run.py - Entry point for the Flask application

# Create the application instance with the appropriate configuration
config_name = os.getenv('FLASK_CONFIG', 'production')  # Default to 'production'
app = create_app(config_name)
    
if __name__ == '__main__':
    # Get port from environment variable or default to 8080
    #port = int(os.environ.get('PORT', 8080))
    # In development, run with debug. In production, Gunicorn will be used
    #app.run(port=port)
    pass