"""
Account Blueprint
Handles user account pages, settings, and admin tools
"""
from flask import Blueprint

account_bp = Blueprint('account', __name__, template_folder='../templates/account')

# Import routes to register them with the blueprint
from app.account import routes
