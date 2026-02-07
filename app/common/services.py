"""
Common Services

Cross-cutting helpers for content pairings and unified content search.
"""
from sqlalchemy import or_
from app.common.models import ContentPairing
from app.books.models import Books
from app.movies.models import Movies
from app.shows.models import TVShows
from app.extensions import db


def get_content_item(item_type, item_id):
    """
    Load a content item by type and ID.
    Returns a dict with id, type, title, subtitle, cover_image_url, detail_url.
    Returns None if not found.
    """
    if item_type == 'Book':
        item = Books.query.get(item_id)
        if item:
            return {
                'id': item.id,
                'type': 'Book',
                'title': item.title,
                'subtitle': item.author,
                'cover_image_url': item.cover_image_url,
                'detail_url': f'/books/{item.id}',
            }
    elif item_type == 'Movie':
        item = Movies.query.get(item_id)
        if item:
            return {
                'id': item.tmdb_id,
                'type': 'Movie',
                'title': item.title,
                'subtitle': item.director,
                'cover_image_url': item.cover_image_url or 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
                'detail_url': '/movies/',
            }
    elif item_type == 'TVShow':
        item = TVShows.query.get(item_id)
        if item:
            return {
                'id': item.tvdb_id,
                'type': 'TVShow',
                'title': item.title,
                'subtitle': str(item.year),
                'cover_image_url': item.cover_image_url or 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
                'detail_url': '/watching/',
            }
    return None


def get_pairings_for_page(page_content_types):
    """
    Get visible content pairings where at least one side matches the given types.
    E.g. page_content_types=['Book'] for reading, ['Movie', 'TVShow'] for watching.
    Returns list of enriched pairing dicts.
    """
    pairings = ContentPairing.query.filter(
        ContentPairing.is_visible == True,
        or_(
            ContentPairing.item_type_1.in_(page_content_types),
            ContentPairing.item_type_2.in_(page_content_types),
        )
    ).order_by(ContentPairing.updated_at.desc()).all()

    result = []
    for pairing in pairings:
        item_1 = get_content_item(pairing.item_type_1, pairing.item_id_1)
        item_2 = get_content_item(pairing.item_type_2, pairing.item_id_2)
        if item_1 and item_2:
            result.append({
                'id': pairing.id,
                'item_1': item_1,
                'item_2': item_2,
                'note': pairing.note,
                'is_visible': pairing.is_visible,
            })
    return result


def search_all_content(query):
    """
    Search across all content types by title.
    Returns unified results with type labels for the pairing modal.
    """
    if len(query) < 2:
        return []

    results = []

    books = Books.query.filter(
        db.or_(
            Books.title.ilike(f'%{query}%'),
            Books.author.ilike(f'%{query}%')
        )
    ).limit(10).all()
    for book in books:
        results.append({
            'id': str(book.id),
            'type': 'Book',
            'title': book.title,
            'subtitle': book.author,
            'cover_image_url': book.cover_image_url,
        })

    movies = Movies.query.filter(
        db.or_(
            Movies.title.ilike(f'%{query}%'),
            Movies.director.ilike(f'%{query}%')
        )
    ).limit(10).all()
    for movie in movies:
        results.append({
            'id': movie.tmdb_id,
            'type': 'Movie',
            'title': movie.title,
            'subtitle': movie.director,
            'cover_image_url': movie.cover_image_url,
        })

    shows = TVShows.query.filter(
        TVShows.title.ilike(f'%{query}%')
    ).limit(10).all()
    for show in shows:
        results.append({
            'id': show.tvdb_id,
            'type': 'TVShow',
            'title': show.title,
            'subtitle': str(show.year),
            'cover_image_url': show.cover_image_url,
        })

    return results
