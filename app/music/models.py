"""
Music/Playlists Models
"""
from app.extensions import db


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

    def __repr__(self):
        return f'<Playlist {self.name}>'
