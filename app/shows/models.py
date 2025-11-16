"""
TV Shows Models
"""
from app.extensions import db


class TVShows(db.Model):
    """TV Shows model for tracking watched shows"""

    __tablename__ = 'tv_shows'

    tvdb_id = db.Column(db.String, primary_key=True)
    imdb_id = db.Column(db.String)
    title = db.Column(db.String(500), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    my_rating = db.Column(db.Integer)
    date_finished = db.Column(db.String(20))
    last_watched = db.Column(db.String(20))
    my_review = db.Column(db.Text)
    language = db.Column(db.String(50))
    cover_image_url = db.Column(db.String(500))
    collections = db.Column(db.Text)
    status = db.Column(db.String(50))

    def __repr__(self):
        return f'<TVShow {self.title} ({self.year})>'
