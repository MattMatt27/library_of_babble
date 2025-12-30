"""
Artworks Business Logic and Helper Functions
"""
import re
import random
from urllib.parse import unquote
from sqlalchemy import text, func
from app.extensions import db
from app.artworks.models import Artworks


def normalize_year(year):
    """
    Convert various year formats to a normalized integer for sorting.

    Handles:
    - Century formats: "19th Century" -> 1800, "1st Century" -> 0
    - Multi-century: "18-19th century" -> 1700, "5-6th Century" -> 400
    - Decade formats: "1890s" -> 1890
    - BCE/CE ranges: "200 BCE-500 CE" -> -200, "664-332 BCE" -> -664
    - Year ranges: "720-725" -> 720, "200–500" (em dash) -> 200
    """
    if not year:
        return None

    # Strip all whitespace including non-breaking spaces, and normalize internal spaces
    year_str = ' '.join(str(year).split())

    # Handle BCE year ranges (e.g., "664-332 BCE") - must check before general BCE
    bce_range_match = re.match(r"(\d+)\s*[-–]\s*\d+\s*BCE", year_str, re.IGNORECASE)
    if bce_range_match:
        # Use the earlier (more negative) year for BCE ranges
        return -int(bce_range_match.group(1))

    # Handle BCE/CE year ranges (e.g., "200 BCE-500 CE")
    bce_ce_match = re.match(r"(\d+)\s*BCE\s*[-–]\s*\d+\s*CE", year_str, re.IGNORECASE)
    if bce_ce_match:
        # Use the BCE year (more negative)
        return -int(bce_ce_match.group(1))

    # Handle single BCE years (e.g., "500 BCE")
    bce_match = re.match(r"(\d+)\s*BCE", year_str, re.IGNORECASE)
    if bce_match:
        return -int(bce_match.group(1))

    # Handle multi-century format (e.g., "18-19th century", "5-6th Century", "19th-20th Century", "19th - 20th Century")
    # This regex needs to match both "5-6th" and "19th-20th" patterns, with optional spaces around dash
    multi_century_match = re.match(r"(\d+)(?:st|nd|rd|th)?\s*[-–]\s*(\d+)(st|nd|rd|th)\s+[Cc]entury", year_str)
    if multi_century_match:
        # Use the earlier century
        century = int(multi_century_match.group(1))
        return (century - 1) * 100

    # Handle single century format (e.g., "19th Century", "1st Century")
    century_match = re.match(r"(\d+)(st|nd|rd|th)\s+[Cc]entury", year_str)
    if century_match:
        century = int(century_match.group(1))
        return (century - 1) * 100

    # Handle decade format (e.g., "1890s")
    decade_match = re.match(r"(\d{3,4})0s", year_str)
    if decade_match:
        return int(decade_match.group(1) + "0")

    # Handle year ranges with em dash or en dash (e.g., "200–500", "720-725")
    range_match = re.match(r"(\d+)\s*[-–]\s*\d+", year_str)
    if range_match:
        return int(range_match.group(1))

    # If it's not a special format, try to parse as plain integer
    try:
        return int(year_str)
    except ValueError:
        return None


def get_approved_artworks_from_db(page=1, per_page=100, sort_order='asc',
                                  start_date=None, end_date=None, artist_filter=None, collection_filter=None, random_seed=None):
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

    # Apply collection filter (AND logic - artwork must be in ALL selected collections)
    if collection_filter:
        from flask_login import current_user
        from app.artworks.models import LikedArtworks

        # Collect artwork ID sets for each collection
        collection_sets = []

        # Handle "my_likes" specially
        if 'my_likes' in collection_filter:
            if current_user.is_authenticated:
                liked_ids = db.session.query(LikedArtworks.artwork_id).filter(
                    LikedArtworks.user_id == current_user.id
                ).all()
                collection_sets.append(set(lid[0] for lid in liked_ids))
            else:
                # User not authenticated but requested my_likes - empty set
                collection_sets.append(set())

        # Get artwork IDs for each gallery collection separately
        other_collections = [c for c in collection_filter if c != 'my_likes']
        for collection_id in other_collections:
            gallery_artwork_ids = db.session.query(ArtworkGalleryItem.artwork_id).filter(
                ArtworkGalleryItem.gallery_id == collection_id
            ).all()
            collection_sets.append(set(aid[0] for aid in gallery_artwork_ids))

        # Intersect all sets (AND logic)
        if collection_sets:
            artwork_ids = collection_sets[0]
            for s in collection_sets[1:]:
                artwork_ids = artwork_ids.intersection(s)

            if artwork_ids:
                query = query.filter(Artworks.id.in_(list(artwork_ids)))
            else:
                # No artworks match ALL collections, return empty
                return [], 0, all_artists
        else:
            # No valid collections to filter by
            return [], 0, all_artists

    # Apply artist filter
    if artist_filter:
        query = query.filter(Artworks.artist.in_(artist_filter))

    # For date filtering, we need to handle the complex year normalization
    # For now, we'll apply simple filtering (can be enhanced later)
    # This is a simplified version - my original manula approach used complex SQL CASE statements

    # Get total count for pagination before sorting
    total_items = query.count()
    total_pages = (total_items + per_page - 1) // per_page

    # For year-based sorting, we need to normalize years in Python
    # For other sorts, we can do it in SQL
    if sort_order == "random":
        # Use seeded random for consistent ordering across pagination
        # We'll fetch all IDs, shuffle them with the seed, then paginate
        all_ids = [row.id for row in query.with_entities(Artworks.id).all()]

        rng = random.Random(random_seed)
        rng.shuffle(all_ids)

        # Paginate the shuffled IDs
        offset = (page - 1) * per_page
        page_ids = all_ids[offset:offset + per_page]

        # Fetch the actual artworks in the shuffled order
        if page_ids:
            artworks_query = query.filter(Artworks.id.in_(page_ids)).all()
            # Sort by the order of page_ids
            id_to_artwork = {artwork.id: artwork for artwork in artworks_query}
            artworks_query = [id_to_artwork[id] for id in page_ids if id in id_to_artwork]
        else:
            artworks_query = []
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
        artist_display = unquote(artwork.artist).strip() if artwork.artist else ''
        artworks.append({
            'id': artwork.id,
            'title': artwork.title if artwork.title else f"From the {artwork.series} series",
            'artist': artist_display,
            'filesystem_artist': artist_display, 
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
        artist_display = unquote(artwork.artist).strip() if artwork.artist else ''
        artworks.append({
            'id': artwork.id,
            'title': f"{artwork.title} ({artwork.year})" if artwork.title else f"From the {artwork.series} series ({artwork.year})",
            'artist': artist_display,
            'filesystem_artist': artist_display, 
            'year': artwork.year,
            'file_name': unquote(artwork.file_name) if artwork.file_name else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'series': artwork.series,
            'series_id': artwork.series_id,
            'medium': artwork.medium,
            'location': artwork.location
        })

    return artworks
