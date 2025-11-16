"""
Flask Extensions

Extensions are initialized here to avoid circular imports.
They are configured in the app factory (app/__init__.py).
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
