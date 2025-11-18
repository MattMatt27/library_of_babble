"""
Books Business Logic and Helper Functions
"""
import sqlite3
from app.extensions import db
from app.books.models import Books, BookQuote
from app.common.models import Reviews


def truncate_title(title):
    """Clean book titles by dropping text after the first colon (usually a subtitle)"""
    index = title.find(':')
    return title[:index] if index != -1 else title


def get_recently_read_books(limit=10):
    """Get recently read books with reviews"""
    books = []

    # Query books with reviews, ordered by date_reviewed
    query = db.session.query(Books, Reviews).join(
        Reviews,
        db.and_(
            Reviews.item_id == db.cast(Books.id, db.String),
            Reviews.item_type == 'Book'
        )
    ).filter(
        Reviews.date_reviewed.isnot(None),
        Reviews.date_reviewed != ""
    ).order_by(
        Reviews.date_reviewed.desc()
    ).limit(limit)

    for book, review in query:
        books.append({
            'id': book.id,
            'title': truncate_title(book.title),
            'author': book.author,
            'publication_year': book.original_publication_year,
            'cover_image_url': book.cover_image_url if book.cover_image_url else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_read': review.date_reviewed,
            'my_rating': review.rating,
            'my_review': review.review_text
        })

    return books


def read_books_from_db():
    """Get all books with reviews from database"""
    books = []

    # Join Books with Reviews to get the latest review data
    query = db.session.query(Books, Reviews).join(
        Reviews,
        db.and_(
            Reviews.item_id == db.cast(Books.id, db.String),
            Reviews.item_type == 'Book'
        )
    ).filter(
        Reviews.rating > 0,
        Reviews.date_reviewed != ""
    ).order_by(
        Reviews.date_reviewed.desc()
    ).all()

    for book, review in query:
        books.append({
            'id': book.id,
            'title': truncate_title(book.title),
            'author': book.author,
            'publication_year': book.original_publication_year,
            'cover_image_url': book.cover_image_url if book.cover_image_url else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_read': review.date_reviewed,
            'my_rating': str(review.rating) if review.rating else '0',
            'my_review': review.review_text
        })

    return books


def get_books_from_bookshelf(bookshelf_name):
    """Get books from a specific Goodreads bookshelf"""
    books = []

    # Query books that have the bookshelf name in their bookshelves field
    query = Books.query.filter(
        Books.bookshelves.like(f'%{bookshelf_name}%')
    ).all()

    for book in query:
        # Get the latest review for this book
        review = Reviews.query.filter_by(
            item_type='Book',
            item_id=str(book.id)
        ).order_by(Reviews.date_reviewed.desc()).first()

        books.append({
            'id': book.id,
            'title': truncate_title(book.title),
            'author': book.author,
            'publication_year': book.original_publication_year,
            'cover_image_url': book.cover_image_url if book.cover_image_url else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_read': review.date_reviewed if review else None,
            'my_rating': str(review.rating) if review and review.rating else '0',
            'my_review': review.review_text if review else None
        })

    return books
