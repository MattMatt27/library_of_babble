"""
TV Shows Blueprint
"""
from flask import Blueprint

shows_bp = Blueprint('shows', __name__)

from app.shows import routes  # noqa: E402, F401
