"""
Movies Routes
"""
from flask import render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.movies import movies_bp
from app.movies.models import Movies
from app.movies.services import read_movies_from_db
from app.collections.models import Reviews
from app.extensions import db


@movies_bp.route('/')
def index():
    """List all movies"""
    movies_data = read_movies_from_db()
    return render_template('movies/index.html', movies=movies_data)


@movies_bp.route('/update_review/<movie_id>', methods=['POST'])
@login_required
def update_review(movie_id):
    """Update movie review (admin only)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Permission denied'}), 403

    movie = Movies.query.get_or_404(movie_id)
    new_review = request.form.get('my_review')
    date_watched = request.form.get('date_watched')

    # Find or create review
    review = Reviews.query.filter_by(
        item_type='Movie',
        item_id=movie_id,
        date_reviewed=date_watched
    ).first()

    if review:
        review.review_text = new_review
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
            review_text=new_review,
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
