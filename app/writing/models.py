"""
Writing Models
"""
from app.extensions import db
from datetime import datetime


class Author(db.Model):
    """Author model for publication authors"""

    __tablename__ = 'authors'

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    is_you = db.Column(db.Boolean, default=False)  # Mark which author is the site owner
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Author {self.name}>'

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'is_you': self.is_you
        }


class PublicationAuthor(db.Model):
    """Junction table for many-to-many relationship between publications and authors"""

    __tablename__ = 'publication_authors'

    id = db.Column(db.String, primary_key=True)
    publication_id = db.Column(db.String, db.ForeignKey('publications.id', ondelete='CASCADE'), nullable=False)
    author_id = db.Column(db.String, db.ForeignKey('authors.id', ondelete='CASCADE'), nullable=False)
    author_order = db.Column(db.Integer, nullable=False)  # 1st author, 2nd author, etc.

    # Relationships
    author = db.relationship('Author', backref='publication_authors')

    def __repr__(self):
        return f'<PublicationAuthor pub={self.publication_id} author={self.author_id} order={self.author_order}>'


class Publication(db.Model):
    """Publications model for academic and creative writing"""

    __tablename__ = 'publications'

    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    venue = db.Column(db.String(500), nullable=False)
    publication_date = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(1000))
    doi = db.Column(db.String(200))
    pmid = db.Column(db.String(50))
    volume_issue = db.Column(db.String(100))
    badge = db.Column(db.String(200))
    section = db.Column(db.String(50), nullable=False)  # 'academic' or 'creative'
    category = db.Column(db.String(50), nullable=False)  # 'journal_article', 'fiction', etc.
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    publication_authors = db.relationship('PublicationAuthor',
                                         backref='publication',
                                         cascade='all, delete-orphan',
                                         order_by='PublicationAuthor.author_order')

    def __repr__(self):
        return f'<Publication {self.title}>'

    def get_authors_ordered(self):
        """Get authors in the correct order with bolding for site owner"""
        authors = []
        for pub_author in sorted(self.publication_authors, key=lambda x: x.author_order):
            author = pub_author.author
            authors.append({
                'name': author.name,
                'is_you': author.is_you
            })
        return authors

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'authors': self.get_authors_ordered(),
            'venue': self.venue,
            'publication_date': self.publication_date,
            'url': self.url,
            'doi': self.doi,
            'pmid': self.pmid,
            'volume_issue': self.volume_issue,
            'badge': self.badge,
            'section': self.section,
            'category': self.category,
            'display_order': self.display_order
        }
