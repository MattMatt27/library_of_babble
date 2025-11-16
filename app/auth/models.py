"""
Authentication Models
"""
from flask_login import UserMixin
from app.extensions import db


class User(UserMixin, db.Model):
    """User model for authentication and authorization"""

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Increased for hashed passwords
    role = db.Column(db.String(50), nullable=False)

    @property
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'

    @property
    def can_view_artworks(self):
        """Check if user can view artworks (all authenticated users can)"""
        return True

    def __repr__(self):
        return f'<User {self.username}>'
