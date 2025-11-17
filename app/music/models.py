"""
Music/Playlists Models
"""
from app.extensions import db
from datetime import datetime


class Playlists(db.Model):
    """Spotify playlists model"""

    __tablename__ = 'playlists'

    user_id = db.Column(db.String, nullable=False)
    playlist_owner = db.Column(db.String, nullable=False)
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    album_art = db.Column(db.String)
    track_count = db.Column(db.Integer)
    is_collab = db.Column(db.Boolean)
    is_public = db.Column(db.Boolean)
    site_approved = db.Column(db.Boolean, default=False, nullable=False)

    # Audit/metadata fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    source = db.Column(db.String(50), default='spotify_api')  # 'spotify_api', 'manual', etc.
    import_batch_id = db.Column(db.String)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<Playlist {self.name}>'
