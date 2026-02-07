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


class MovieQuote(db.Model):
    """Movie quotes model"""

    __tablename__ = 'movie_quote'

    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.String(50), nullable=False)
    quote_text = db.Column(db.Text, nullable=False)
    character = db.Column(db.String(200))  # Who said it
    scene_timestamp = db.Column(db.String(20))  # When in the movie (e.g. "01:23:45")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MovieQuote from movie {self.movie_id}>'


class LikedMovieQuotes(db.Model):
    """User movie quote likes (many-to-many relationship)"""

    __tablename__ = 'liked_movie_quotes'

    # Composite primary key (user_id + quote_id)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('movie_quote.id'), primary_key=True)

    # Audit field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LikedMovieQuote user={self.user_id} quote={self.quote_id}>'
