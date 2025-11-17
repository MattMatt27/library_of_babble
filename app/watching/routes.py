"""
Watching Routes
Aggregates movies and TV shows for the watching page
"""
from flask import render_template
from app.watching import watching_bp
from app.shows.services import get_shows_from_collection
from app.movies.services import get_recently_watched_movies, get_movies_from_collection


@watching_bp.route('/')
def index():
    """Watching page - recently watched movies and TV shows"""
    # Get movie data
    recently_watched_movies = get_recently_watched_movies(limit=8)
    recommended_movies = get_movies_from_collection('matts-recommended')

    # Get TV show data
    recommended_shows = get_shows_from_collection('matts-recommended')

    return render_template(
        'watching/index.html',
        recently_watched_movies=recently_watched_movies,
        recommended_movies=recommended_movies,
        recommended_shows=recommended_shows
    )
