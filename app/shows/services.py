"""
TV Shows Business Logic and Helper Functions
"""
from app.extensions import db
from app.shows.models import TVShows
from app.common.models import Reviews, Collection, CollectionItem


def get_recently_watched_shows(limit=10):
    """Get recently watched TV shows with reviews"""
    shows = []

    # Query shows with reviews, ordered by date_reviewed
    query = db.session.query(TVShows, Reviews).join(
        Reviews,
        db.and_(
            Reviews.item_id == TVShows.tvdb_id,
            Reviews.item_type == 'TVShow'
        )
    ).filter(
        Reviews.date_reviewed.isnot(None)
    ).order_by(
        Reviews.date_reviewed.desc()
    ).limit(limit)

    for show, review in query:
        shows.append({
            'id': show.tvdb_id,
            'title': show.title,
            'year': show.year,
            'cover_image_url': show.cover_image_url if show.cover_image_url else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_watched': review.date_reviewed,
            'my_rating': review.rating,
            'my_review': review.review_text
        })

    return shows


def read_shows_from_db():
    """Get all TV shows with reviews from database"""
    shows = []

    query = db.session.query(TVShows, Reviews).join(
        Reviews,
        db.and_(
            Reviews.item_id == TVShows.tvdb_id,
            Reviews.item_type == 'TVShow'
        )
    ).filter(
        Reviews.date_reviewed.isnot(None)
    ).all()

    for show, review in query:
        shows.append({
            'id': show.tvdb_id,
            'title': show.title,
            'year': show.year,
            'cover_image_url': show.cover_image_url if show.cover_image_url else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_watched': review.date_reviewed,
            'my_rating': str(review.rating) if review.rating else '0',
            'my_review': review.review_text
        })

    return shows


def get_shows_from_collection(collection_name):
    """Get TV shows from a specific collection"""
    shows = []

    # Get the collection
    collection = Collection.query.filter_by(collection_name=collection_name).first()
    if not collection:
        return shows

    # Get show IDs from collection items
    collection_items = CollectionItem.query.filter_by(
        collection_id=collection.id,
        item_type='TVShow'
    ).all()

    for item in collection_items:
        show = TVShows.query.get(item.item_id)
        if show:
            # Get the latest review for this show
            review = Reviews.query.filter_by(
                item_type='TVShow',
                item_id=show.tvdb_id
            ).order_by(Reviews.date_reviewed.desc()).first()

            shows.append({
                'id': show.tvdb_id,
                'title': show.title,
                'year': show.year,
                'cover_image_url': show.cover_image_url if show.cover_image_url else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
                'date_watched': review.date_reviewed if review else None,
                'my_rating': str(review.rating) if review and review.rating else '0',
                'my_review': review.review_text if review else None
            })

    return shows
