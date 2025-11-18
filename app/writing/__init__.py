"""
Writing Module
Contains publications models and routes for academic and creative writing
"""
from flask import Blueprint

writing_bp = Blueprint('writing', __name__)

from app.writing import routes
