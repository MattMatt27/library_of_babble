"""
Reading Routes
Main reading page with recommendations and recently read content
"""
import random
from flask import render_template, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy import func
from app.reading import reading_bp
from app.books.models import Books, BookQuote, BookPairing, LikedQuotes
from app.books.services import (
    get_recently_read_books,
    read_books_from_db,
    get_books_from_bookshelf
)
from app.utils.security import page_visible
from app.extensions import db


@reading_bp.route('/')
@page_visible('reading')
def index():
    """Reading page with recently read and recommendations"""
    recently_read_books = get_recently_read_books()
    recommended_fiction_books = get_books_from_bookshelf('matts-recommended-fiction')
    recommended_nonfiction_books = get_books_from_bookshelf('matts-recommended-nonfiction')

    # Get all visible book pairings for cycling display
    pairings = BookPairing.query.filter_by(is_visible=True).order_by(BookPairing.updated_at.desc()).all()
    book_pairings = []
    for pairing in pairings:
        if pairing.book_1 and pairing.book_2:
            book_pairings.append({
                'id': pairing.id,
                'book_1': {
                    'id': pairing.book_1.id,
                    'title': pairing.book_1.title,
                    'author': pairing.book_1.author,
                    'cover_image_url': pairing.book_1.cover_image_url,
                },
                'book_2': {
                    'id': pairing.book_2.id,
                    'title': pairing.book_2.title,
                    'author': pairing.book_2.author,
                    'cover_image_url': pairing.book_2.cover_image_url,
                },
                'note': pairing.note,
                'is_visible': pairing.is_visible
            })

    # Get a random short quote (under 300 chars) for the quote card
    short_quotes = BookQuote.query.filter(
        func.length(BookQuote.quote_text) <= 300
    ).all()

    random_quote = None
    if short_quotes:
        quote = random.choice(short_quotes)
        book = Books.query.get(quote.book_id)
        if book:
            random_quote = {
                'id': quote.id,
                'text': quote.quote_text,
                'book_title': book.title,
                'book_author': book.author,
                'book_id': book.id,
                'chapter': quote.chapter,
                'page_number': quote.page_number
            }

    return render_template(
        'books/reading.html',
        recently_read_books=recently_read_books,
        recommended_fiction_books=recommended_fiction_books,
        recommended_nonfiction_books=recommended_nonfiction_books,
        book_pairings=book_pairings,
        random_quote=random_quote,
        current_user=current_user
    )


@reading_bp.route('/books')
@page_visible('books')
def books():
    """List all books"""
    books_data = read_books_from_db()
    return render_template('books/index.html', books=books_data)


@reading_bp.route('/api/pairing', methods=['GET'])
@login_required
def get_pairing():
    """Get current book pairing"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    pairing = BookPairing.query.order_by(BookPairing.updated_at.desc()).first()
    if pairing and pairing.book_1 and pairing.book_2:
        return jsonify({
            'book_id_1': pairing.book_id_1,
            'book_title_1': pairing.book_1.title,
            'book_author_1': pairing.book_1.author,
            'book_id_2': pairing.book_id_2,
            'book_title_2': pairing.book_2.title,
            'book_author_2': pairing.book_2.author,
            'note': pairing.note
        })
    return jsonify({'book_id_1': None, 'book_id_2': None, 'note': None})


@reading_bp.route('/api/pairing', methods=['POST'])
@login_required
def set_pairing():
    """Create or update book pairing (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    pairing_id = data.get('id')
    book_id_1 = data.get('book_id_1')
    book_id_2 = data.get('book_id_2')
    note = data.get('note', '').strip()
    is_visible = data.get('is_visible', True)

    if not book_id_1 or not book_id_2 or not note:
        return jsonify({'error': 'Two books and a note are required'}), 400

    if book_id_1 == book_id_2:
        return jsonify({'error': 'Please select two different books'}), 400

    # Verify both books exist
    book_1 = Books.query.get(book_id_1)
    book_2 = Books.query.get(book_id_2)
    if not book_1 or not book_2:
        return jsonify({'error': 'One or both books not found'}), 404

    # Update existing or create new pairing
    if pairing_id:
        pairing = BookPairing.query.get(pairing_id)
        if not pairing:
            return jsonify({'error': 'Pairing not found'}), 404
        pairing.book_id_1 = book_id_1
        pairing.book_id_2 = book_id_2
        pairing.note = note
        pairing.is_visible = is_visible
        pairing.updated_by = current_user.id
    else:
        pairing = BookPairing(
            book_id_1=book_id_1,
            book_id_2=book_id_2,
            note=note,
            is_visible=is_visible,
            updated_by=current_user.id
        )
        db.session.add(pairing)

    db.session.commit()
    return jsonify({'success': True})


@reading_bp.route('/api/books/search', methods=['GET'])
@login_required
def search_books():
    """Search books for the featured book modal"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])

    books = Books.query.filter(
        db.or_(
            Books.title.ilike(f'%{query}%'),
            Books.author.ilike(f'%{query}%')
        )
    ).limit(20).all()

    return jsonify([{
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'cover_image_url': book.cover_image_url
    } for book in books])


@reading_bp.route('/quotes')
@page_visible('reading')
def quotes():
    """Quotes exploration page"""
    # Get all quotes with their associated books
    all_quotes = BookQuote.query.all()

    # Get user's liked quotes (if authenticated)
    liked_quote_ids = set()
    if current_user.is_authenticated:
        liked_quotes = LikedQuotes.query.filter_by(
            user_id=current_user.id
        ).all()
        liked_quote_ids = {like.quote_id for like in liked_quotes}

    quotes_data = []
    for quote in all_quotes:
        book = Books.query.get(quote.book_id)
        if book:
            quotes_data.append({
                'id': quote.id,
                'text': quote.quote_text,
                'book_id': book.id,
                'book_title': book.title,
                'book_author': book.author,
                'book_cover': book.cover_image_url,
                'book_year': book.original_publication_year,
                'chapter': quote.chapter,
                'page_number': quote.page_number,
                'is_liked': quote.id in liked_quote_ids
            })

    # Get unique books for filtering
    books_with_quotes = Books.query.filter(
        Books.id.in_([q.book_id for q in all_quotes])
    ).order_by(Books.title).all()

    return render_template(
        'books/quotes.html',
        quotes=quotes_data,
        books_with_quotes=books_with_quotes,
        current_user=current_user
    )
