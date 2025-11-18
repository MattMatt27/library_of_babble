"""
Movies Models
"""
from app.extensions import db
from datetime import datetime


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

    # Audit/metadata fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    source = db.Column(db.String(50), default='manual')  # 'manual', 'letterboxd_import', 'boredom_killer_import', etc.
    import_batch_id = db.Column(db.String)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<Movie {self.title} ({self.year})>'
