"""
Site Settings Model

Key-value store for site-wide configuration that can be customized
by anyone who forks the repository.
"""
from app.extensions import db
from datetime import datetime


class SiteSetting(db.Model):
    """
    Key-value store for site-wide configuration.

    Allows anyone who forks the repository to customize site settings
    without modifying code. Settings can be managed via admin UI or seed scripts.

    Common keys:
    - site_title: Main site title shown in browser tab
    - site_owner_name: Owner name for display
    - contact_email: Contact email for inquiries
    - home_background_images: JSON list of background image paths
    - home_background_interval: Milliseconds between background changes
    """

    __tablename__ = 'site_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    value_type = db.Column(db.String(20), default='string')  # string, json, boolean, integer
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<SiteSetting {self.key}>'
