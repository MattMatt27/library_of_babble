"""
Collecting Models

Database models for antiques collection: pins and alcohol labels
"""
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
