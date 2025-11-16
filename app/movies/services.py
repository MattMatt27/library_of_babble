"""
Movies Business Logic and Helper Functions
"""
from app.extensions import db
from app.movies.models import Movies
from app.collections.models import Reviews, Collections


def get_recently_watched_movies(limit=10):
    """Get recently watched movies with reviews"""
    movies = []

    # Query movies with reviews, ordered by date_reviewed
    query = db.session.query(Movies, Reviews).join(
        Reviews,
        db.and_(
            Reviews.item_id == Movies.tmdb_id,
            Reviews.item_type == 'Movie'
        )
    ).filter(
        Reviews.date_reviewed.isnot(None)
    ).order_by(
        Reviews.date_reviewed.desc()
    ).limit(limit)

    for movie, review in query:
        movies.append({
            'id': movie.tmdb_id,
            'title': movie.title,
            'director': movie.director,
            'year': movie.year,
            'cover_image_url': movie.cover_image_url if movie.cover_image_url else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_watched': review.date_reviewed,
            'my_rating': review.rating,
            'my_review': review.review_text
        })

    return movies


def read_movies_from_db():
    """Get all movies with reviews from database"""
    movies = []

    query = db.session.query(Movies, Reviews).join(
        Reviews,
        db.and_(
            Reviews.item_id == Movies.tmdb_id,
            Reviews.item_type == 'Movie'
        )
    ).filter(
        Reviews.date_reviewed.isnot(None)
    ).all()

    for movie, review in query:
        movies.append({
            'id': movie.tmdb_id,
            'title': movie.title,
            'director': movie.director,
            'year': movie.year,
            'cover_image_url': movie.cover_image_url if movie.cover_image_url else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_watched': review.date_reviewed,
            'my_rating': str(review.rating) if review.rating else '0',
            'my_review': review.review_text
        })

    return movies


def get_movies_from_collection(collection_name):
    """Get movies from a specific collection"""
    movies = []

    # Get movie IDs from collection
    collection_items = Collections.query.filter_by(
        collection_name=collection_name,
        item_type='Movie'
    ).all()

    for item in collection_items:
        movie = Movies.query.get(item.item_id)
        if movie:
            # Get the latest review for this movie
            review = Reviews.query.filter_by(
                item_type='Movie',
                item_id=movie.tmdb_id
            ).order_by(Reviews.date_reviewed.desc()).first()

            movies.append({
                'id': movie.tmdb_id,
                'title': movie.title,
                'director': movie.director,
                'year': movie.year,
                'cover_image_url': movie.cover_image_url if movie.cover_image_url else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
                'date_watched': review.date_reviewed if review else None,
                'my_rating': str(review.rating) if review and review.rating else '0',
                'my_review': review.review_text if review else None
            })

    return movies
