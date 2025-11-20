"""
Application Entry Point

Run this file to start the Flask development server.
"""
import os
from app import create_app

# Create the Flask application
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Only enable debug in development
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    # Don't bind to 0.0.0.0 unless explicitly needed
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))

    app.run(debug=debug_mode, host=host, port=port)
