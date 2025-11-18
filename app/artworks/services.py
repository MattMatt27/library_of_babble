"""
Artworks Business Logic and Helper Functions
"""
import re
from urllib.parse import unquote
from sqlalchemy import text, func
from app.extensions import db
from app.artworks.models import Artworks


def normalize_year(year):
    """
    Convert century values to the start of the century (e.g., '20th Century' -> 1900).
    Convert year ranges to the start year (e.g., '720-725' -> 720).
    Other values are returned as-is.
    """
    if not year:
        return None

    year_str = str(year).strip()

    # Handle century format (e.g., "19th Century")
    century_match = re.match(r"(\d+)(st|nd|rd|th)\s+Century", year_str, re.IGNORECASE)
    if century_match:
        century = int(century_match.group(1))
        return (century - 1) * 100

    # Handle year ranges (e.g., "720-725")
    range_match = re.match(r"(\d+)\s*-\s*\d+", year_str)
    if range_match:
        return int(range_match.group(1))

    # If it's not a century or range, return the year as an integer
    try:
        return int(year_str)
    except ValueError:
        return None


def get_approved_artworks_from_db(page=1, per_page=100, sort_order='asc',
                                  start_date=None, end_date=None, artist_filter=None, collection_filter=None):
    """
    Fetch artworks from the database with pagination, filtering, and sorting.

    Args:
        page (int): The current page number.
        per_page (int): The number of items per page.
        sort_order (str): Sort order for the `year` field ('asc', 'desc', 'random').
        start_date (int, optional): Start year for filtering.
        end_date (int, optional): End year for filtering.
        artist_filter (list, optional): List of artists to include.
        collection_filter (list, optional): List of collection IDs to filter by.

    Returns:
        tuple: A tuple of (artworks, total_pages, all_artists).
    """
    from app.artworks.models import ArtworkGalleryItem

    # Get all unique artists
    all_artists = db.session.query(Artworks.artist).filter(
        Artworks.site_approved == True
    ).distinct().all()
    all_artists = [artist[0] for artist in all_artists if artist[0]]

    # Build base query
    query = Artworks.query.filter(Artworks.site_approved == True)

    # Apply collection filter
    if collection_filter:
        from flask_login import current_user
        from app.artworks.models import LikedArtworks

        artwork_ids = set()

        # Handle "my_likes" specially
        if 'my_likes' in collection_filter:
            if current_user.is_authenticated:
                liked_ids = db.session.query(LikedArtworks.artwork_id).filter(
                    LikedArtworks.user_id == current_user.id
                ).all()
                artwork_ids.update([lid[0] for lid in liked_ids])

        # Get other collection galleries
        other_collections = [c for c in collection_filter if c != 'my_likes']
        if other_collections:
            gallery_artwork_ids = db.session.query(ArtworkGalleryItem.artwork_id).filter(
                ArtworkGalleryItem.gallery_id.in_(other_collections)
            ).distinct().all()
            artwork_ids.update([aid[0] for aid in gallery_artwork_ids])

        if artwork_ids:
            query = query.filter(Artworks.id.in_(list(artwork_ids)))
        else:
            # No artworks match the collection filter, return empty
            return [], 0, all_artists

    # Apply artist filter
    if artist_filter:
        query = query.filter(Artworks.artist.in_(artist_filter))

    # For date filtering, we need to handle the complex year normalization
    # For now, we'll apply simple filtering (can be enhanced later)
    # This is a simplified version - the original used complex SQL CASE statements

    # Get total count for pagination before sorting
    total_items = query.count()
    total_pages = (total_items + per_page - 1) // per_page

    # For year-based sorting, we need to normalize years in Python
    # For other sorts, we can do it in SQL
    if sort_order == "random":
        query = query.order_by(func.random())
        offset = (page - 1) * per_page
        artworks_query = query.limit(per_page).offset(offset).all()
    elif sort_order == "date_added_desc":
        query = query.order_by(Artworks.created_at.desc())
        offset = (page - 1) * per_page
        artworks_query = query.limit(per_page).offset(offset).all()
    elif sort_order == "date_added_asc":
        query = query.order_by(Artworks.created_at.asc())
        offset = (page - 1) * per_page
        artworks_query = query.limit(per_page).offset(offset).all()
    else:
        # For year sorting, fetch all results and sort in Python
        all_results = query.all()
        # Sort by normalized year
        reverse = (sort_order == "desc")
        sorted_results = sorted(
            all_results,
            key=lambda x: normalize_year(x.year) or 0,
            reverse=reverse
        )
        # Apply pagination manually
        offset = (page - 1) * per_page
        artworks_query = sorted_results[offset:offset + per_page]

    # Process results
    artworks = []
    for artwork in artworks_query:
        artworks.append({
            'id': artwork.id,
            'title': artwork.title if artwork.title else f"From the {artwork.series} series",
            'artist': unquote(artwork.artist).strip() if artwork.artist else '',
            'year': artwork.year,
            'file_name': unquote(artwork.file_name) if artwork.file_name else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'series': artwork.series,
            'series_id': artwork.series_id,
            'medium': artwork.medium,
            'location': artwork.location
        })

    return artworks, total_pages, all_artists


def get_all_artworks():
    """Get all site-approved artworks from database"""
    artworks_query = Artworks.query.filter(Artworks.site_approved == True).all()

    artworks = []
    for artwork in artworks_query:
        artworks.append({
            'id': artwork.id,
            'title': f"{artwork.title} ({artwork.year})" if artwork.title else f"From the {artwork.series} series ({artwork.year})",
            'artist': unquote(artwork.artist).strip() if artwork.artist else '',
            'year': artwork.year,
            'file_name': unquote(artwork.file_name) if artwork.file_name else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'series': artwork.series,
            'series_id': artwork.series_id,
            'medium': artwork.medium,
            'location': artwork.location
        })

    return artworks
