"""
Creating Blueprint

Handles creative projects showcase: art, software, research projects
"""
from flask import Blueprint

creating_bp = Blueprint('creating', __name__)

from app.creating import routes  # noqa: E402, F401
