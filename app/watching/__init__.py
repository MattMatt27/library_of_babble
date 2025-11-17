"""
Watching Blueprint
Aggregates movies and TV shows for the watching page
"""
from flask import Blueprint

watching_bp = Blueprint('watching', __name__)

from app.watching import routes  # noqa: E402, F401
