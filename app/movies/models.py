"""
Movies Models
"""
from app.extensions import db


class Movies(db.Model):
    """Movies model for tracking watched movies"""

    __tablename__ = 'movies'

    tmdb_id = db.Column(db.String, primary_key=True)
    imdb_id = db.Column(db.String)
    letterboxd_id = db.Column(db.String)
    title = db.Column(db.String(500), nullable=False)
    director = db.Column(db.String(200))
    year = db.Column(db.Integer, nullable=False)
    my_rating = db.Column(db.Float)
    date_watched = db.Column(db.String(20))
    my_review = db.Column(db.Text)
    language = db.Column(db.String(50))
    cover_image_url = db.Column(db.String(500))
    collections = db.Column(db.Text)
    status = db.Column(db.String(20))

    def __repr__(self):
        return f'<Movie {self.title} ({self.year})>'
