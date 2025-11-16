"""
Books Routes
"""
from flask import render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from app.books import books_bp
from app.books.models import Books, BookQuote
from app.books.services import (
    get_recently_read_books,
    read_books_from_db,
    get_books_from_bookshelf,
    truncate_title
)
from app.collections.models import Reviews
from app.extensions import db


@books_bp.route('/')
def index():
    """List all books"""
    books_data = read_books_from_db()
    return render_template('books/index.html', books=books_data)


@books_bp.route('/reading')
def reading():
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


@books_bp.route('/<int:book_id>')
def detail(book_id):
    """Individual book detail page with reviews and quotes"""
    # Get book details from the database
    book = Books.query.get(book_id)

    # If book doesn't exist, return a 404 page
    if not book:
        return render_template('404.html'), 404

    book_details = {
        'id': book.id,
        'title': truncate_title(book.title),
        'author': book.author,
        'publication_year': book.original_publication_year,
        'cover_image_url': book.cover_image_url if book.cover_image_url else 'https://theprairiesbookreview.com/wp-content/uploads/2023/11/cover-not-availble-image.jpg',
    }

    # Get reviews from the Reviews table
    reviews = []
    review_records = Reviews.query.filter_by(
        item_type='Book',
        item_id=str(book_id)
    ).order_by(Reviews.date_reviewed.desc()).all()

    for review in review_records:
        reviews.append({
            'date_read': review.date_reviewed,
            'my_rating': str(review.rating) if review.rating else '0',
            'my_review': review.review_text
        })

    # Get quotes from database
    quotes = []
    quote_records = BookQuote.query.filter_by(
        book_id=str(book_id)
    ).order_by(BookQuote.page_number).all()

    for quote in quote_records:
        quotes.append({
            'text': quote.quote_text,
            'page_number': quote.page_number if quote.page_number else "N/A"
        })

    return render_template(
        'books/detail.html',
        book=book_details,
        reviews=reviews,
        quotes=quotes
    )


@books_bp.route('/update_review/<int:book_id>', methods=['POST'])
@login_required
def update_review(book_id):
    """Update book review (admin only)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Permission denied'}), 403

    book = Books.query.get_or_404(book_id)
    new_review = request.form.get('my_review')
    date_read = request.form.get('date_read')

    # Find or create review
    review = Reviews.query.filter_by(
        item_type='Book',
        item_id=str(book_id),
        date_reviewed=date_read
    ).first()

    if review:
        review.review_text = new_review
    else:
        review = Reviews(
            item_type='Book',
            item_id=str(book_id),
            review_text=new_review,
            date_reviewed=date_read,
            rating=book.my_rating
        )
        db.session.add(review)

    db.session.commit()

    # Redirect back to the referring page (index or detail)
    referrer = request.referrer
    if referrer and '/books/' in referrer and referrer.endswith('/books/'):
        return redirect(url_for('books.index'))
    return redirect(url_for('books.detail', book_id=book_id))


@books_bp.route('/add_quote/<book_id>', methods=['POST'])
@login_required
def add_quote(book_id):
    """Add a quote to a book (admin only)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Permission denied'}), 403

    quote_text = request.form.get('quote_text')
    page_number = request.form.get('page_number')

    if quote_text:
        new_quote = BookQuote(
            book_id=str(book_id),
            quote_text=quote_text,
            page_number=int(page_number) if page_number else None
        )
        db.session.add(new_quote)
        db.session.commit()

    return redirect(url_for('books.detail', book_id=book_id))


@books_bp.route('/update_cover_url/<int:book_id>', methods=['POST'])
@login_required
def update_cover_url(book_id):
    """Update the cover image URL for a book (admin only)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Permission denied'}), 403

    book = Books.query.get_or_404(book_id)
    cover_url = request.form.get('cover_url', '').strip()

    if not cover_url:
        flash('Please provide a valid URL', 'error')
        return redirect(url_for('books.detail', book_id=book_id))

    # Update the cover URL
    book.cover_image_url = cover_url
    db.session.commit()

    flash('Cover image URL updated successfully!', 'success')
    return redirect(url_for('books.detail', book_id=book_id))


@books_bp.route('/update_rating/<int:book_id>', methods=['POST'])
@login_required
def update_rating(book_id):
    """Update book rating via AJAX (admin only)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Permission denied'}), 403

    try:
        data = request.get_json()
        rating = data.get('rating')

        # Validate rating
        if rating is None:
            return jsonify({'error': 'Rating is required'}), 400

        rating = float(rating)
        if rating < 0 or rating > 5 or (rating * 2) % 1 != 0:
            return jsonify({'error': 'Rating must be between 0-5 in 0.5 increments'}), 400

        # Update book rating
        book = Books.query.get_or_404(book_id)
        book.my_rating = rating

        # Update review rating if exists
        review = Reviews.query.filter_by(
            item_type='Book',
            item_id=str(book_id)
        ).first()

        if review:
            review.rating = rating

        db.session.commit()

        return jsonify({
            'success': True,
            'rating': rating,
            'message': f'Rating updated to {rating} stars'
        })

    except ValueError:
        return jsonify({'error': 'Invalid rating value'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
