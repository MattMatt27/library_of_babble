"""
Movies Routes
"""
from flask import render_template, request, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app.movies import movies_bp
from app.movies.models import Movies, MovieQuote, LikedMovieQuotes
from app.movies.services import read_movies_from_db
from app.common.models import Reviews
from app.extensions import db, limiter
from app.utils.security import page_visible, user_required
from app.utils.security import sanitize_html


def normalize_quote_text(text):
    """Normalize quote text to fix encoding issues before saving."""
    if not text:
        return text
    replacements = {
        '\u0091': "'", '\u0092': "'",
        '\u0093': '"', '\u0094': '"',
        '\u0095': '\u2022', '\u0096': '\u2013',
        '\u0097': '\u2014', '\u0085': '\u2026',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


@movies_bp.route('/')
@page_visible('movies')
def index():
    """List all movies"""
    movies_data = read_movies_from_db()
    return render_template('movies/index.html', movies=movies_data)


@movies_bp.route('/update_review/<movie_id>', methods=['POST'])
@login_required
def update_review(movie_id):
    """Update movie review (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Permission denied'}), 403

    movie = Movies.query.get_or_404(movie_id)
    new_review = request.form.get('my_review', '')
    date_watched = request.form.get('date_watched')

    # Sanitize review HTML to prevent XSS attacks
    sanitized_review = sanitize_html(new_review)

    # Find or create review
    review = Reviews.query.filter_by(
        item_type='Movie',
        item_id=movie_id,
        date_reviewed=date_watched
    ).first()

    if review:
        review.review_text = str(sanitized_review)
    else:
        # Get rating from movie if exists
        existing_review = Reviews.query.filter_by(
            item_type='Movie',
            item_id=movie_id
        ).first()
        rating = existing_review.rating if existing_review else 0

        review = Reviews(
            item_type='Movie',
            item_id=movie_id,
            review_text=str(sanitized_review),
            date_reviewed=date_watched,
            rating=rating
        )
        db.session.add(review)

    db.session.commit()

    # Redirect back to the referring page (index)
    referrer = request.referrer
    if referrer and '/movies/' in referrer and referrer.endswith('/movies/'):
        return redirect(url_for('movies.index'))
    return redirect(url_for('movies.index'))


@movies_bp.route('/update_rating/<movie_id>', methods=['POST'])
@login_required
def update_rating(movie_id):
    """Update movie rating via AJAX (admin only)"""
    if not current_user.is_admin:
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

        # Update movie rating
        movie = Movies.query.get_or_404(movie_id)
        movie.my_rating = rating

        # Update review rating if exists
        review = Reviews.query.filter_by(
            item_type='Movie',
            item_id=movie_id
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


@movies_bp.route('/add_quote/<movie_id>', methods=['POST'])
@login_required
def add_quote(movie_id):
    """Add a quote to a movie (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Permission denied'}), 403

    quote_text = normalize_quote_text(request.form.get('quote_text'))
    character = request.form.get('character', '').strip()
    scene_timestamp = request.form.get('scene_timestamp', '').strip()

    if quote_text:
        new_quote = MovieQuote(
            movie_id=str(movie_id),
            quote_text=quote_text,
            character=character if character else None,
            scene_timestamp=scene_timestamp if scene_timestamp else None,
        )
        db.session.add(new_quote)
        db.session.commit()

    return redirect(url_for('movies.index'))


@movies_bp.route('/update_quote/<int:quote_id>', methods=['POST'])
@login_required
def update_quote(quote_id):
    """Update a movie quote (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Permission denied'}), 403

    quote = MovieQuote.query.get_or_404(quote_id)
    quote_text = normalize_quote_text(request.form.get('quote_text'))
    character = request.form.get('character', '').strip()
    scene_timestamp = request.form.get('scene_timestamp', '').strip()

    if quote_text:
        quote.quote_text = quote_text
        quote.character = character if character else None
        quote.scene_timestamp = scene_timestamp if scene_timestamp else None
        db.session.commit()

    return redirect(url_for('movies.index'))


@movies_bp.route('/like_quote', methods=['POST'])
@limiter.limit("60 per minute")
@user_required
def like_quote():
    """Toggle movie quote like (API endpoint)"""
    quote_id = request.json.get('quote_id')
    if not quote_id:
        return jsonify({'error': 'Quote ID is required'}), 400

    try:
        quote_id = int(quote_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid quote ID'}), 400

    quote = MovieQuote.query.get(quote_id)
    if not quote:
        return jsonify({'error': 'Quote not found'}), 404

    try:
        liked = LikedMovieQuotes.query.filter_by(
            user_id=current_user.id,
            quote_id=quote_id
        ).first()

        if liked:
            db.session.delete(liked)
            db.session.commit()
            return jsonify({'liked': False})
        else:
            new_like = LikedMovieQuotes(
                user_id=current_user.id,
                quote_id=quote_id
            )
            db.session.add(new_like)
            db.session.commit()
            return jsonify({'liked': True})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling movie quote like: {str(e)}", exc_info=True)
        return jsonify({'error': 'An error occurred'}), 500
