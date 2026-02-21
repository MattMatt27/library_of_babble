"""
Card Collection Services

Business logic for card collection management.
"""
from flask_login import current_user
from app.extensions import db
from app.collecting.models import Card, CardCopy
from app.utils.security import sanitize_html


def search_cards(query='', category=None, set_name=None, brand=None,
                 page=1, per_page=50, include_hidden=False):
    """
    Search cards with filtering and pagination.

    Args:
        query: Search term for name, set, or player
        category: Filter by category
        set_name: Filter by set name
        brand: Filter by brand
        page: Page number
        per_page: Results per page
        include_hidden: Whether to include hidden cards (admin only)

    Returns:
        Tuple of (cards list, total count, total pages)
    """
    cards_query = db.session.query(Card).join(CardCopy)

    # Exclude hidden cards unless admin
    if not include_hidden:
        cards_query = cards_query.filter(CardCopy.visibility != 'hidden')

    # Apply search filter
    if query:
        search_term = f"%{query}%"
        cards_query = cards_query.filter(
            db.or_(
                Card.name.ilike(search_term),
                Card.set_name.ilike(search_term),
                Card.brand.ilike(search_term),
                Card.details['player'].astext.ilike(search_term),
                Card.external_api_id.ilike(search_term),
            )
        )

    # Apply category filter
    if category:
        cards_query = cards_query.filter(Card.category == category)

    # Apply set filter
    if set_name:
        cards_query = cards_query.filter(Card.set_name.ilike(f"%{set_name}%"))

    # Apply brand filter
    if brand:
        cards_query = cards_query.filter(Card.brand.ilike(f"%{brand}%"))

    # Distinct cards (not copies)
    cards_query = cards_query.distinct(Card.id).order_by(Card.id.desc())

    total = cards_query.count()
    cards = cards_query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    return cards, total, total_pages


def get_card_by_id(card_id):
    """Get a card by ID."""
    return Card.query.get_or_404(card_id)


def get_card_copy_by_id(copy_id):
    """Get a card copy by ID."""
    return CardCopy.query.get_or_404(copy_id)


def create_card(name, category, brand=None, set_name=None, set_year=None,
                card_number=None, variant=None, details=None, created_by=None,
                external_api_id=None, external_image_url=None,
                external_market_data=None):
    """
    Create a new card record.

    Args:
        name: Card name/subject (required)
        category: Card category (required)
        brand: Card brand (Topps, Panini, etc.)
        set_name: Set name
        set_year: Set year
        card_number: Card number in set
        variant: Card variant (base, foil, etc.)
        details: Category-specific details dict
        created_by: User ID of creator
        external_api_id: External API identifier (e.g., Pokemon TCG API)
        external_image_url: Hi-res image URL from external API
        external_market_data: Price/market data snapshot from external API

    Returns:
        Created Card object
    """
    card = Card(
        name=name,
        brand=brand,
        set_name=set_name,
        set_year=set_year,
        card_number=card_number,
        category=category,
        variant=variant,
        details=details or {},
        created_by=created_by,
        external_api_id=external_api_id,
        external_image_url=external_image_url,
        external_market_data=external_market_data,
    )
    db.session.add(card)
    db.session.commit()
    return card


def update_card(card_id, **kwargs):
    """
    Update an existing card.

    Args:
        card_id: ID of card to update
        **kwargs: Fields to update

    Returns:
        Updated Card object
    """
    card = Card.query.get_or_404(card_id)

    allowed_fields = ['name', 'brand', 'set_name', 'set_year', 'card_number',
                      'category', 'variant', 'details',
                      'external_api_id', 'external_image_url',
                      'external_market_data']

    for field in allowed_fields:
        if field in kwargs:
            setattr(card, field, kwargs[field])

    db.session.commit()
    return card


def delete_card(card_id):
    """
    Delete a card and all its copies.

    Args:
        card_id: ID of card to delete

    Returns:
        True if successful
    """
    card = Card.query.get_or_404(card_id)
    db.session.delete(card)
    db.session.commit()
    return True


def add_card_copy(card_id, condition=None, is_graded=False, grading_service=None,
                  grade=None, storage_location=None, storage_type=None,
                  visibility='public', is_featured=False, notes=None, date_acquired=None):
    """
    Add a physical copy of a card.

    Args:
        card_id: ID of the card
        condition: Card condition
        is_graded: Whether card is professionally graded
        grading_service: Grading service (PSA, BGS, etc.)
        grade: Grade value
        storage_location: Physical storage location
        storage_type: Type of storage
        visibility: Visibility level
        is_featured: Whether to feature in gallery
        notes: Additional notes
        date_acquired: Date card was acquired

    Returns:
        Created CardCopy object
    """
    # Verify card exists
    card = Card.query.get_or_404(card_id)

    copy = CardCopy(
        card_id=card.id,
        condition=condition,
        is_graded=is_graded,
        grading_service=grading_service if is_graded else None,
        grade=grade if is_graded else None,
        storage_location=storage_location,
        storage_type=storage_type,
        visibility=visibility,
        is_featured=is_featured,
        notes=sanitize_html(notes) if notes else None,
        date_acquired=date_acquired
    )
    db.session.add(copy)
    db.session.commit()
    return copy


def update_card_copy(copy_id, **kwargs):
    """
    Update an existing card copy.

    Args:
        copy_id: ID of copy to update
        **kwargs: Fields to update

    Returns:
        Updated CardCopy object
    """
    copy = CardCopy.query.get_or_404(copy_id)

    allowed_fields = ['condition', 'is_graded', 'grading_service', 'grade',
                      'storage_location', 'storage_type', 'visibility',
                      'is_featured', 'notes', 'date_acquired',
                      'image_front_url', 'image_back_url']

    for field in allowed_fields:
        if field in kwargs:
            value = kwargs[field]
            # Sanitize notes
            if field == 'notes' and value:
                value = sanitize_html(value)
            setattr(copy, field, value)

    # Clear grading fields if not graded
    if 'is_graded' in kwargs and not kwargs['is_graded']:
        copy.grading_service = None
        copy.grade = None

    db.session.commit()
    return copy


def delete_card_copy(copy_id):
    """
    Delete a card copy.

    Args:
        copy_id: ID of copy to delete

    Returns:
        True if successful
    """
    copy = CardCopy.query.get_or_404(copy_id)
    db.session.delete(copy)
    db.session.commit()
    return True


def format_card_for_response(card, include_hidden=False):
    """
    Format a card for JSON response.

    Args:
        card: Card object
        include_hidden: Whether to include hidden copies

    Returns:
        Dict representation of card
    """
    copies = [c for c in card.copies
              if c.visibility != 'hidden' or include_hidden]

    return {
        'id': card.id,
        'name': card.name,
        'brand': card.brand,
        'set_name': card.set_name,
        'set_year': card.set_year,
        'card_number': card.card_number,
        'category': card.category,
        'variant': card.variant,
        'details': card.details,
        'external_api_id': card.external_api_id,
        'external_image_url': card.external_image_url,
        'external_market_data': card.external_market_data,
        'copies': [format_copy_for_response(c) for c in copies]
    }


def format_copy_for_response(copy):
    """
    Format a card copy for JSON response.

    Args:
        copy: CardCopy object

    Returns:
        Dict representation of copy
    """
    return {
        'id': copy.id,
        'card_id': copy.card_id,
        'condition': copy.condition,
        'is_graded': copy.is_graded,
        'grading_service': copy.grading_service,
        'grade': copy.grade,
        'grade_display': f"{copy.grading_service} {copy.grade}" if copy.is_graded else None,
        'storage_location': copy.storage_location,
        'storage_type': copy.storage_type,
        'visibility': copy.visibility,
        'is_featured': copy.is_featured,
        'image_front_url': copy.image_front_url,
        'image_back_url': copy.image_back_url,
        'notes': copy.notes,
        'date_added': copy.date_added.isoformat() if copy.date_added else None,
        'date_acquired': copy.date_acquired.isoformat() if copy.date_acquired else None,
    }


def get_all_storage_locations():
    """
    Get all unique storage locations for autocomplete.

    Returns:
        List of storage location strings
    """
    locations = db.session.query(CardCopy.storage_location)\
        .filter(CardCopy.storage_location.isnot(None))\
        .distinct()\
        .order_by(CardCopy.storage_location)\
        .all()
    return [loc[0] for loc in locations]


def get_card_stats():
    """
    Get collection statistics.

    Returns:
        Dict with collection stats
    """
    total_cards = Card.query.count()
    total_copies = CardCopy.query.count()
    featured_count = CardCopy.query.filter_by(is_featured=True).count()

    # Category breakdown
    category_counts = db.session.query(
        Card.category,
        db.func.count(Card.id)
    ).group_by(Card.category).all()

    return {
        'total_cards': total_cards,
        'total_copies': total_copies,
        'featured_count': featured_count,
        'by_category': {cat: count for cat, count in category_counts}
    }


def get_featured_cards(limit=20):
    """
    Get featured cards for gallery display.

    Args:
        limit: Maximum number of cards to return

    Returns:
        List of CardCopy objects with their Card data
    """
    copies = CardCopy.query\
        .filter_by(is_featured=True, visibility='public')\
        .order_by(CardCopy.date_added.desc())\
        .limit(limit)\
        .all()
    return copies


def get_cards_by_category(category, page=1, per_page=50, include_hidden=False):
    """
    Get cards filtered by category.

    Args:
        category: Category to filter by
        page: Page number
        per_page: Results per page
        include_hidden: Whether to include hidden cards

    Returns:
        Tuple of (cards list, total count, total pages)
    """
    return search_cards(
        category=category,
        page=page,
        per_page=per_page,
        include_hidden=include_hidden
    )
