"""
Watching Blueprint (Movies and TV Shows)
"""
from flask import Blueprint

watching_bp = Blueprint('watching', __name__)

from app.shows import routes  # noqa: E402, F401
