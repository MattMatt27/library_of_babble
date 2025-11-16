"""
Music/Playlists Blueprint
"""
from flask import Blueprint

music_bp = Blueprint('music', __name__)

from app.music import routes  # noqa: E402, F401
