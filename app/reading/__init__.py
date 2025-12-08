"""
Reading Blueprint
"""
from flask import Blueprint

reading_bp = Blueprint('reading', __name__)

from app.reading import routes  # noqa: E402, F401
