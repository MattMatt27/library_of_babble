"""
Collections and Reviews Models

Cross-cutting models that apply to multiple content types.
"""
from app.extensions import db


class Reviews(db.Model):
    """
    Unified reviews table supporting multiple content types.
    Allows multiple reviews per item over time.
    """

    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(20), nullable=False)  # 'Book', 'Movie', 'TVShow'
    item_id = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Float)
    review_text = db.Column(db.Text)
    date_reviewed = db.Column(db.String(20))

    def __repr__(self):
        return f'<Review {self.item_type} {self.item_id}>'


class Collections(db.Model):
    """Custom collections/groupings for content"""

    __tablename__ = 'collections'

    id = db.Column(db.Integer, primary_key=True)
    collection_name = db.Column(db.String(100), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)
    item_id = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<Collection {self.collection_name}>'
