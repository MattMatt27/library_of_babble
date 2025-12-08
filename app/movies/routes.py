"""
Movies Routes
"""
from flask import render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.movies import movies_bp
from app.movies.models import Movies
from app.movies.services import read_movies_from_db
from app.common.models import Reviews
from app.extensions import db
from app.utils.security import page_visible
from app.utils.security import sanitize_html


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
