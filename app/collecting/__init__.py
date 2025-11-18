"""
Collecting Blueprint

Handles antiques collection: pins, alcohol labels, and other collectibles
"""
from flask import Blueprint

collecting_bp = Blueprint('collecting', __name__)

from app.collecting import routes  # noqa: E402, F401
