"""
Collections Blueprint

Handles Reviews, Collections, Pins, and Alcohol Labels
"""
from flask import Blueprint

collections_bp = Blueprint('collections', __name__)

from app.collections import routes  # noqa: E402, F401
