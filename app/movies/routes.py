"""
Movies Routes
"""
from flask import render_template
from app.movies import movies_bp
from app.movies.services import read_movies_from_db


@movies_bp.route('/')
def index():
    """List all movies"""
    movies_data = read_movies_from_db()
    return render_template('movies/index.html', movies=movies_data)
