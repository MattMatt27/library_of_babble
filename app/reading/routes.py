"""
Reading Routes
Main reading page with recommendations and recently read content
"""
from flask import render_template
from flask_login import current_user
from app.reading import reading_bp
from app.books.services import (
    get_recently_read_books,
    read_books_from_db,
    get_books_from_bookshelf
)
from app.utils.security import page_visible


@reading_bp.route('/')
@page_visible('reading')
def index():
    """Reading page with recently read and recommendations"""
    recently_read_books = get_recently_read_books()
    recommended_fiction_books = get_books_from_bookshelf('matts-recommended-fiction')
    recommended_nonfiction_books = get_books_from_bookshelf('matts-recommended-nonfiction')

    return render_template(
        'books/reading.html',
        recently_read_books=recently_read_books,
        recommended_fiction_books=recommended_fiction_books,
        recommended_nonfiction_books=recommended_nonfiction_books,
        current_user=current_user
    )


@reading_bp.route('/books')
@page_visible('books')
def books():
    """List all books"""
    books_data = read_books_from_db()
    return render_template('books/index.html', books=books_data)
