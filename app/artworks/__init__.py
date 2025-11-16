"""
Artworks Blueprint
"""
from flask import Blueprint

artworks_bp = Blueprint('artworks', __name__)

from app.artworks import routes  # noqa: E402, F401
