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
    Other values are returned as-is.
    """
    century_match = re.match(r"(\d+)(st|nd|rd|th)\s+Century", str(year), re.IGNORECASE)
    if century_match:
        century = int(century_match.group(1))
        return (century - 1) * 100

    # If it's not a century, return the year as an integer
    try:
        return int(year)
    except ValueError:
        return None


def get_approved_artworks_from_db(page=1, per_page=100, sort_order='asc',
                                  start_date=None, end_date=None, artist_filter=None):
    """
    Fetch artworks from the database with pagination, filtering, and sorting.

    Args:
        page (int): The current page number.
        per_page (int): The number of items per page.
        sort_order (str): Sort order for the `year` field ('asc', 'desc', 'random').
        start_date (int, optional): Start year for filtering.
        end_date (int, optional): End year for filtering.
        artist_filter (list, optional): List of artists to include.

    Returns:
        tuple: A tuple of (artworks, total_pages, all_artists).
    """
    # Get all unique artists
    all_artists = db.session.query(Artworks.artist).filter(
        Artworks.site_approved == True
    ).distinct().all()
    all_artists = [artist[0] for artist in all_artists if artist[0]]

    # Build base query
    query = Artworks.query.filter(Artworks.site_approved == True)

    # Apply artist filter
    if artist_filter:
        query = query.filter(Artworks.artist.in_(artist_filter))

    # For date filtering, we need to handle the complex year normalization
    # For now, we'll apply simple filtering (can be enhanced later)
    # This is a simplified version - the original used complex SQL CASE statements

    # Apply sorting
    if sort_order == "random":
        query = query.order_by(func.random())
    elif sort_order == "date_added_desc":
        query = query.order_by(Artworks.created_at.desc())
    elif sort_order == "date_added_asc":
        query = query.order_by(Artworks.created_at.asc())
    elif sort_order == "desc":
        query = query.order_by(Artworks.year.desc())
    else:  # asc
        query = query.order_by(Artworks.year.asc())

    # Get total count for pagination
    total_items = query.count()
    total_pages = (total_items + per_page - 1) // per_page

    # Apply pagination
    offset = (page - 1) * per_page
    artworks_query = query.limit(per_page).offset(offset).all()

    # Process results
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
