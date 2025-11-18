"""
Artworks Models
"""
from app.extensions import db
from datetime import datetime


class ArtworkGallery(db.Model):
    """Gallery collections for organizing artworks into curated groups"""

    __tablename__ = 'artwork_galleries'

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(10))  # emoji or icon class
    is_system = db.Column(db.Boolean, default=False, nullable=False)  # system vs user-created
    is_public = db.Column(db.Boolean, default=True, nullable=False)  # public vs private (admin-only)
    display_order = db.Column(db.Integer, default=0)

    # Audit/metadata fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<ArtworkGallery {self.name}>'

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'is_system': self.is_system,
            'is_public': self.is_public,
            'display_order': self.display_order
        }


class ArtworkGalleryItem(db.Model):
    """Junction table for many-to-many relationship between artworks and galleries"""

    __tablename__ = 'artwork_gallery_items'

    artwork_id = db.Column(db.String, db.ForeignKey('artworks.id', ondelete='CASCADE'), primary_key=True)
    gallery_id = db.Column(db.String, db.ForeignKey('artwork_galleries.id', ondelete='CASCADE'), primary_key=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    gallery = db.relationship('ArtworkGallery', backref='artwork_gallery_items')
    artwork = db.relationship('Artworks', backref='artwork_gallery_items')

    def __repr__(self):
        return f'<ArtworkGalleryItem artwork={self.artwork_id} gallery={self.gallery_id}>'


class Artworks(db.Model):
    """Artworks model for gallery management"""

    __tablename__ = 'artworks'

    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    artist = db.Column(db.String(200))
    after = db.Column(db.String(200))
    year = db.Column(db.String(100), nullable=False)
    series = db.Column(db.String(500))
    series_id = db.Column(db.Integer)
    file_name = db.Column(db.String(500))
    location = db.Column(db.String(500))
    description = db.Column(db.Text)
    medium = db.Column(db.Text)
    collections = db.Column(db.Text)
    site_approved = db.Column(db.Boolean, default=False, nullable=False)

    # Audit/metadata fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    source = db.Column(db.String(50), default='manual')  # 'manual', 'csv_import', etc.
    import_batch_id = db.Column(db.String)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<Artwork {self.title} by {self.artist}>'


class LikedArtworks(db.Model):
    """User artwork likes (many-to-many)"""

    __tablename__ = 'liked_artworks'

    user_id = db.Column(db.Integer, primary_key=True)
    artwork_id = db.Column(db.String, primary_key=True)

    def __repr__(self):
        return f'<LikedArtwork user={self.user_id} artwork={self.artwork_id}>'


class GeneratedImages(db.Model):
    """AI-generated images model"""

    __tablename__ = 'generated_images'

    id = db.Column(db.String, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    artist_palette = db.Column(db.String(1000), nullable=False)
    model = db.Column(db.String(255))
    model_version = db.Column(db.Integer)
    prompt = db.Column(db.String(1000))

    # Audit/metadata fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    source = db.Column(db.String(50), default='generated')  # 'generated', 'api', etc.
    import_batch_id = db.Column(db.String)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<GeneratedImage {self.file_name}>'
