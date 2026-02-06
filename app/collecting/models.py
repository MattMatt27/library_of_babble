"""
Collecting Models

Database models for collections: pins, alcohol labels, and trading cards
"""
from datetime import datetime
from app.extensions import db


class Pin(db.Model):
    """Political pins, club pins, and other collectible pins"""

    __tablename__ = 'pins'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.String(20))  # Can be range like "1930s-40s"
    text = db.Column(db.Text)
    pin_type = db.Column(db.String(100))  # Presidential Campaign Pin, Club, etc.
    notes = db.Column(db.Text)
    associated_person = db.Column(db.String(200))
    origin = db.Column(db.String(200))
    owned = db.Column(db.Boolean, default=False)
    sold = db.Column(db.Boolean, default=False)
    dimensions = db.Column(db.String(50))
    grade = db.Column(db.String(50))
    reproduction = db.Column(db.Boolean, default=False)
    original_year = db.Column(db.String(20))
    links = db.Column(db.Text)
    set_id = db.Column(db.Integer)
    number_in_set = db.Column(db.Integer)
    image_filename = db.Column(db.String(200))  # Store filename, construct path in template

    def __repr__(self):
        return f'<Pin {self.id}: {self.text[:30]}...>'


class AlcoholLabel(db.Model):
    """Vintage alcohol labels from bottles"""

    __tablename__ = 'alcohol_labels'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.String(20))  # Can be range like "1930s-40s"
    text = db.Column(db.Text)
    alcohol_volume = db.Column(db.String(50))
    alcohol_proof = db.Column(db.Integer)
    alcohol_type = db.Column(db.String(50))  # Whiskey, Bourbon, etc.
    dimensions = db.Column(db.String(50))
    distributed_by = db.Column(db.String(200))
    distributed_by_location = db.Column(db.String(200))
    bottled_by = db.Column(db.String(200))
    bottled_by_location = db.Column(db.String(200))
    distilled_by = db.Column(db.String(200))
    distilled_by_location = db.Column(db.String(200))
    notes = db.Column(db.Text)
    grade = db.Column(db.String(50))
    origin = db.Column(db.String(200))
    owned = db.Column(db.Boolean, default=False)
    sold = db.Column(db.Boolean, default=False)
    image_filename = db.Column(db.String(200))  # Store filename, construct path in template

    def __repr__(self):
        return f'<AlcoholLabel {self.id}: {self.text[:30]}...>'


class Card(db.Model):
    """
    Card identity - represents a unique card definition.
    One record per unique card (set + number + variant combination).
    """

    __tablename__ = 'cards'

    id = db.Column(db.Integer, primary_key=True)

    # Core identity
    name = db.Column(db.String(300), nullable=False)  # Card name/subject
    brand = db.Column(db.String(100))  # Topps, Panini, Pokemon Company, etc.
    set_name = db.Column(db.String(200))  # "1989 Topps Baseball", "Base Set"
    set_year = db.Column(db.Integer)
    card_number = db.Column(db.String(50))  # Can be "1", "RC1", "SW-1", etc.

    # Classification
    category = db.Column(db.String(50), nullable=False)  # sports, pokemon, tcg, historical, advertising, other
    variant = db.Column(db.String(100))  # base, foil, refractor, holo, parallel, etc.

    # Flexible details (category-specific + special features)
    details = db.Column(db.JSON, default=dict)

    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    copies = db.relationship('CardCopy', back_populates='card', cascade='all, delete-orphan')

    # Indexes for search performance
    __table_args__ = (
        db.Index('idx_card_name', 'name'),
        db.Index('idx_card_set', 'set_name', 'set_year'),
        db.Index('idx_card_category', 'category'),
        db.Index('idx_card_brand', 'brand'),
    )

    def __repr__(self):
        return f'<Card {self.name} - {self.set_name} #{self.card_number}>'


class CardCopy(db.Model):
    """
    Physical copy of a card - each owned instance with its own condition/location.
    """

    __tablename__ = 'card_copies'

    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), nullable=False)

    # Condition
    condition = db.Column(db.String(20))  # mint, near_mint, excellent, good, poor
    is_graded = db.Column(db.Boolean, default=False)
    grading_service = db.Column(db.String(20))  # PSA, BGS, CGC, SGC
    grade = db.Column(db.String(10))  # "10", "9.5", etc.

    # Physical location
    storage_location = db.Column(db.String(100))  # "Binder A", "Box 12", etc.
    storage_type = db.Column(db.String(30))  # binder, box, display_case, framed

    # Visibility/status
    visibility = db.Column(db.String(20), default='public')  # public, for_trade, for_sale, hidden

    # Featured cards (gallery display)
    is_featured = db.Column(db.Boolean, default=False)
    image_front_url = db.Column(db.String(500))
    image_back_url = db.Column(db.String(500))

    # Metadata
    notes = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_acquired = db.Column(db.Date)  # When physically acquired

    # Relationship
    card = db.relationship('Card', back_populates='copies')

    # Indexes
    __table_args__ = (
        db.Index('idx_copy_visibility', 'visibility'),
        db.Index('idx_copy_featured', 'is_featured'),
        db.Index('idx_copy_storage', 'storage_location'),
    )

    def __repr__(self):
        return f'<CardCopy {self.id} of Card {self.card_id} - {self.condition}>'
