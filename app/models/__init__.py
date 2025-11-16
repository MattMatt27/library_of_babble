"""
Central Models Module

Imports all models for easy access throughout the application.
Import from here instead of individual blueprint model files.
"""
from app.auth.models import User
from app.books.models import Books, BookQuote
from app.movies.models import Movies
from app.shows.models import TVShows
from app.music.models import Playlists
from app.artworks.models import Artworks, LikedArtworks, GeneratedImages
from app.collections.models import Reviews, Collections

__all__ = [
    'User',
    'Books',
    'BookQuote',
    'Movies',
    'TVShows',
    'Playlists',
    'Artworks',
    'LikedArtworks',
    'GeneratedImages',
    'Reviews',
    'Collections',
]
