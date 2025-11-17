"""
Books Models
"""
from app.extensions import db
from datetime import datetime


class Books(db.Model):
    """Books model for tracking reading history"""

    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)  # Increased for long titles
    author = db.Column(db.String(200), nullable=False)  # Increased for long names
    additional_authors = db.Column(db.Text)  # Changed to Text for comma-separated lists
    isbn = db.Column(db.String(20))
    isbn13 = db.Column(db.String(20))
    my_rating = db.Column(db.Float)
    average_rating = db.Column(db.Float)
    publisher = db.Column(db.String(200))  # Increased for long publisher names
    number_of_pages = db.Column(db.Integer)
    original_publication_year = db.Column(db.Integer)
    date_read = db.Column(db.String(20))
    date_added = db.Column(db.String(20))
    bookshelves = db.Column(db.Text)  # Changed to Text for comma-separated bookshelves
    read = db.Column(db.Boolean)
    my_review = db.Column(db.Text)
    private_notes = db.Column(db.Text)
    read_count = db.Column(db.Integer)
    owned_copies = db.Column(db.Integer)
    cover_image_url = db.Column(db.String(500))  # Increased for long URLs

    # Audit/metadata fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    source = db.Column(db.String(50), default='manual')  # 'manual', 'goodreads_import', etc.
    import_batch_id = db.Column(db.String)
    notes = db.Column(db.Text)  # Internal admin notes (separate from private_notes)

    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'


class BookQuote(db.Model):
    """Book quotes model"""

    __tablename__ = 'book_quote'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.String(50), nullable=False)
    quote_text = db.Column(db.Text, nullable=False)
    page_number = db.Column(db.Integer)

    def __repr__(self):
        return f'<BookQuote from book {self.book_id}>'
