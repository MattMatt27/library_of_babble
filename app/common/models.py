"""
Common Models

Cross-cutting models that apply to multiple content types.
"""
from app.extensions import db
from datetime import datetime


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


class Collection(db.Model):
    """
    Collection metadata - one row per collection.
    Stores collection-level information like name, description, and approval status.
    """

    __tablename__ = 'collections'

    id = db.Column(db.Integer, primary_key=True)
    collection_name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    # Optional type hint for filtering (e.g., 'Playlist', 'Book'). Collections can still
    # contain mixed items - this just helps with filtering empty/new collections.
    collection_type = db.Column(db.String(20), nullable=True)
    site_approved = db.Column(db.Boolean, default=False, nullable=False)
    sort_order = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    # Relationship to items in this collection
    items = db.relationship('CollectionItem', back_populates='collection', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Collection {self.collection_name}>'


class CollectionItem(db.Model):
    """
    Join table linking collections to items.
    One row per item in a collection (many-to-many relationship).
    """

    __tablename__ = 'collection_items'

    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collections.id'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # 'Book', 'Movie', 'TVShow', 'Playlist'
    item_id = db.Column(db.String(50), nullable=False)
    item_order = db.Column(db.Integer, nullable=True)  # Optional ordering within collection

    # Relationship back to collection
    collection = db.relationship('Collection', back_populates='items')

    def __repr__(self):
        return f'<CollectionItem {self.collection_id}:{self.item_type}:{self.item_id}>'


class ContentPairing(db.Model):
    """
    Admin-curated content pairing - two items that complement each other.
    Supports cross-content-type pairings (e.g. Book + Movie).
    """

    __tablename__ = 'content_pairing'

    id = db.Column(db.Integer, primary_key=True)
    item_type_1 = db.Column(db.String(20), nullable=False)  # 'Book', 'Movie', 'TVShow'
    item_id_1 = db.Column(db.String(50), nullable=False)
    item_type_2 = db.Column(db.String(20), nullable=False)
    item_id_2 = db.Column(db.String(50), nullable=False)
    note = db.Column(db.Text, nullable=False)  # Why these items pair well together
    is_visible = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<ContentPairing {self.item_type_1}:{self.item_id_1} + {self.item_type_2}:{self.item_id_2}>'
