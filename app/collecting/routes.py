"""
Collecting Routes

Handles pins, alcohol labels, trading cards, and general collecting page
"""
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user
from app.collecting import collecting_bp
from app.extensions import db
from app.utils.security import admin_required, validate_image_file
from app.services.storage import storage
from app.collecting.services import (
    get_recently_added_pins,
    get_recently_added_labels,
    get_all_pins,
    get_all_labels,
    get_pin_by_id,
    get_label_by_id,
    send_offer_email
)
from app.collecting.card_services import (
    search_cards,
    get_card_by_id,
    get_card_copy_by_id,
    create_card,
    update_card,
    delete_card,
    add_card_copy,
    update_card_copy,
    delete_card_copy,
    format_card_for_response,
    format_copy_for_response,
    get_all_storage_locations,
    get_card_stats,
    get_featured_cards,
)
from app.collecting.schemas import (
    CARD_CATEGORY_SCHEMAS,
    CARD_SPECIAL_FEATURES,
    CARD_VARIANTS,
    CARD_CATEGORIES,
    CARD_CONDITIONS,
    GRADING_SERVICES,
    STORAGE_TYPES,
    CARD_VISIBILITY_OPTIONS,
)


@collecting_bp.route('/')
def index():
    """Main collecting page with recent pins and labels"""
    recently_added_pins = get_recently_added_pins()
    recently_added_labels = get_recently_added_labels()

    return render_template(
        'collecting/index.html',
        recently_added_pins=recently_added_pins,
        recently_added_labels=recently_added_labels
    )


@collecting_bp.route('/pins')
def pins():
    """Full pins collection page"""
    pins_data = get_all_pins()
    return render_template('collecting/pins.html', pins=pins_data)


@collecting_bp.route('/pins/<int:pin_id>')
def pin_detail(pin_id):
    """Individual pin detail page"""
    pin = get_pin_by_id(pin_id)
    return render_template('collecting/pin_detail.html', pin=pin)


@collecting_bp.route('/alcohol-labels')
def alcohol_labels():
    """Full alcohol labels collection page"""
    labels_data = get_all_labels()
    return render_template('collecting/alcohol_labels.html', labels=labels_data)


@collecting_bp.route('/alcohol-labels/<int:label_id>')
def label_detail(label_id):
    """Individual alcohol label detail page"""
    label = get_label_by_id(label_id)
    return render_template('collecting/alcohol_label_detail.html', label=label)


@collecting_bp.route('/submit-offer', methods=['POST'])
def submit_offer():
    """Handle offer submissions"""
    item_id = request.form.get('item_id')
    item_type = request.form.get('item_type')
    item_name = request.form.get('item_name')
    name = request.form.get('name')
    email = request.form.get('email')
    amount = request.form.get('amount')
    message = request.form.get('message', '')

    # Send email notification
    success = send_offer_email(
        item_id=item_id,
        item_type=item_type,
        item_name=item_name,
        customer_name=name,
        customer_email=email,
        offer_amount=amount,
        customer_message=message
    )

    if success:
        flash('Your offer has been submitted successfully! We\'ll be in touch soon.', 'success')
    else:
        flash('There was an error submitting your offer. Please try again later.', 'error')

    # Redirect back to the appropriate page
    if item_type == 'pin':
        return redirect(url_for('collecting.pins'))
    else:
        return redirect(url_for('collecting.alcohol_labels'))


# =============================================================================
# Card Collection Routes
# =============================================================================

# ============ Public Card Endpoints ============

@collecting_bp.route('/cards')
def cards_index():
    """Card collection gallery page"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    query = request.args.get('q', '').strip()

    include_hidden = current_user.is_authenticated and current_user.is_admin

    cards, total, total_pages = search_cards(
        query=query,
        category=category,
        page=page,
        per_page=24,
        include_hidden=include_hidden
    )

    featured = get_featured_cards(limit=10)
    stats = get_card_stats()

    return render_template(
        'collecting/cards.html',
        cards=cards,
        featured=featured,
        stats=stats,
        page=page,
        total_pages=total_pages,
        total=total,
        category=category,
        query=query,
        categories=CARD_CATEGORIES,
    )


@collecting_bp.route('/cards/search')
def cards_search_api():
    """
    Search cards API - public endpoint for visitors to find cards.
    Only returns cards with visibility != 'hidden' unless admin.
    """
    query = request.args.get('q', '').strip()
    category = request.args.get('category')
    set_name = request.args.get('set')
    brand = request.args.get('brand')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # Cap per_page at 100
    per_page = min(per_page, 100)

    # Admins can see hidden cards
    include_hidden = current_user.is_authenticated and current_user.is_admin

    cards, total, total_pages = search_cards(
        query=query,
        category=category,
        set_name=set_name,
        brand=brand,
        page=page,
        per_page=per_page,
        include_hidden=include_hidden
    )

    results = [format_card_for_response(card, include_hidden) for card in cards]

    return jsonify({
        'cards': results,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages
    })


@collecting_bp.route('/cards/<int:card_id>')
def card_detail(card_id):
    """Individual card detail page"""
    card = get_card_by_id(card_id)
    include_hidden = current_user.is_authenticated and current_user.is_admin

    return render_template(
        'collecting/card_detail.html',
        card=card,
        include_hidden=include_hidden,
    )


# ============ Card Schema Endpoint ============

@collecting_bp.route('/cards/schemas')
def cards_schemas():
    """Return category schemas for modal rendering"""
    return jsonify({
        'categories': CARD_CATEGORY_SCHEMAS,
        'category_options': CARD_CATEGORIES,
        'special_features': CARD_SPECIAL_FEATURES,
        'variants': CARD_VARIANTS,
        'conditions': CARD_CONDITIONS,
        'grading_services': GRADING_SERVICES,
        'storage_types': STORAGE_TYPES,
        'visibility_options': CARD_VISIBILITY_OPTIONS,
        'storage_locations': get_all_storage_locations(),
    })


# ============ Card CRUD (Admin Only) ============

@collecting_bp.route('/cards', methods=['POST'])
@admin_required
def create_card_route():
    """Create a new card (admin only)"""
    data = request.get_json()

    # Validate required fields
    if not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    if not data.get('category'):
        return jsonify({'error': 'Category is required'}), 400

    # Validate category
    valid_categories = [c['value'] for c in CARD_CATEGORIES]
    if data['category'] not in valid_categories:
        return jsonify({'error': f'Invalid category. Must be one of: {valid_categories}'}), 400

    card = create_card(
        name=data['name'],
        category=data['category'],
        brand=data.get('brand'),
        set_name=data.get('set_name'),
        set_year=data.get('set_year'),
        card_number=data.get('card_number'),
        variant=data.get('variant'),
        details=data.get('details', {}),
        created_by=current_user.id
    )

    return jsonify({
        'success': True,
        'card_id': card.id,
        'card': format_card_for_response(card, include_hidden=True)
    })


@collecting_bp.route('/cards/<int:card_id>', methods=['PUT'])
@admin_required
def update_card_route(card_id):
    """Update an existing card (admin only)"""
    data = request.get_json()

    # Validate category if provided
    if 'category' in data:
        valid_categories = [c['value'] for c in CARD_CATEGORIES]
        if data['category'] not in valid_categories:
            return jsonify({'error': f'Invalid category. Must be one of: {valid_categories}'}), 400

    card = update_card(card_id, **data)

    return jsonify({
        'success': True,
        'card': format_card_for_response(card, include_hidden=True)
    })


@collecting_bp.route('/cards/<int:card_id>', methods=['DELETE'])
@admin_required
def delete_card_route(card_id):
    """Delete a card and all its copies (admin only)"""
    delete_card(card_id)
    return jsonify({'success': True})


# ============ Card Copy CRUD (Admin Only) ============

@collecting_bp.route('/cards/<int:card_id>/copies', methods=['POST'])
@admin_required
def add_card_copy_route(card_id):
    """Add a copy of an existing card (admin only)"""
    data = request.get_json()

    # Parse date if provided
    date_acquired = None
    if data.get('date_acquired'):
        from datetime import datetime
        try:
            date_acquired = datetime.strptime(data['date_acquired'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    copy = add_card_copy(
        card_id=card_id,
        condition=data.get('condition'),
        is_graded=data.get('is_graded', False),
        grading_service=data.get('grading_service'),
        grade=data.get('grade'),
        storage_location=data.get('storage_location'),
        storage_type=data.get('storage_type'),
        visibility=data.get('visibility', 'public'),
        is_featured=data.get('is_featured', False),
        notes=data.get('notes'),
        date_acquired=date_acquired
    )

    return jsonify({
        'success': True,
        'copy_id': copy.id,
        'copy': format_copy_for_response(copy)
    })


@collecting_bp.route('/copies/<int:copy_id>', methods=['PUT'])
@admin_required
def update_card_copy_route(copy_id):
    """Update a card copy (admin only)"""
    data = request.get_json()

    # Parse date if provided
    if 'date_acquired' in data and data['date_acquired']:
        from datetime import datetime
        try:
            data['date_acquired'] = datetime.strptime(data['date_acquired'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    copy = update_card_copy(copy_id, **data)

    return jsonify({
        'success': True,
        'copy': format_copy_for_response(copy)
    })


@collecting_bp.route('/copies/<int:copy_id>', methods=['DELETE'])
@admin_required
def delete_card_copy_route(copy_id):
    """Delete a card copy (admin only)"""
    delete_card_copy(copy_id)
    return jsonify({'success': True})


# ============ Card Image Upload (Admin Only) ============

@collecting_bp.route('/copies/<int:copy_id>/upload-image', methods=['POST'])
@admin_required
def upload_card_image(copy_id):
    """Upload front/back image for a card copy (admin only)"""
    from werkzeug.utils import secure_filename
    from pathlib import Path
    import uuid

    copy = get_card_copy_by_id(copy_id)
    side = request.form.get('side')  # 'front' or 'back'

    if side not in ('front', 'back'):
        return jsonify({'error': 'Invalid side parameter. Must be "front" or "back"'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Validate file type using security utils
    is_valid, error = validate_image_file(file.stream, file.filename)
    if not is_valid:
        return jsonify({'error': error}), 400

    # Reset file stream after validation
    file.stream.seek(0)

    # Generate path: images/cards/{card_id}/{copy_id}_{side}_{uuid}.{ext}
    ext = Path(file.filename).suffix.lower()
    filename = f"{copy.id}_{side}_{uuid.uuid4().hex[:8]}{ext}"
    relative_path = f"images/cards/{copy.card_id}/{filename}"

    # Save via storage service (handles S3 or local)
    result = storage.save_file(file, relative_path)

    if not result.get('success'):
        return jsonify({'error': result.get('error', 'Upload failed')}), 500

    # Update copy record
    if side == 'front':
        copy.image_front_url = relative_path
    else:
        copy.image_back_url = relative_path

    copy.is_featured = True  # Auto-feature cards with images
    db.session.commit()

    return jsonify({
        'success': True,
        'path': relative_path,
        'url': result.get('url', relative_path)
    })


# ============ Card Collection Endpoints ============
# Uses existing Collection/CollectionItem from app/common/models.py

@collecting_bp.route('/card-collections')
def list_card_collections():
    """List public card collections"""
    from app.common.models import Collection

    collections = Collection.query.filter_by(
        collection_type='Card',
        site_approved=True
    ).order_by(Collection.sort_order).all()

    return jsonify([{
        'id': c.id,
        'name': c.collection_name,
        'description': c.description,
        'item_count': len(c.items)
    } for c in collections])


@collecting_bp.route('/card-collections', methods=['POST'])
@admin_required
def create_card_collection():
    """Create a new card collection (admin only)"""
    from app.common.models import Collection

    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': 'Collection name is required'}), 400

    collection = Collection(
        collection_name=data['name'],
        description=data.get('description'),
        collection_type='Card',
        site_approved=data.get('is_public', True)
    )

    db.session.add(collection)
    db.session.commit()

    return jsonify({
        'success': True,
        'collection_id': collection.id
    })


@collecting_bp.route('/card-collections/<int:collection_id>/items', methods=['POST'])
@admin_required
def add_card_to_collection(collection_id):
    """Add a card copy to a collection (admin only)"""
    from app.common.models import Collection, CollectionItem
    from app.collecting.models import CardCopy

    collection = Collection.query.get_or_404(collection_id)
    data = request.get_json()

    if not data.get('card_copy_id'):
        return jsonify({'error': 'card_copy_id is required'}), 400

    # Verify the card copy exists
    copy = CardCopy.query.get_or_404(data['card_copy_id'])

    # Check if already in collection
    existing = CollectionItem.query.filter_by(
        collection_id=collection_id,
        item_type='CardCopy',
        item_id=str(copy.id)
    ).first()

    if existing:
        return jsonify({'error': 'Card is already in this collection'}), 400

    # Get max order
    max_order = db.session.query(db.func.max(CollectionItem.item_order))\
        .filter_by(collection_id=collection_id).scalar() or 0

    item = CollectionItem(
        collection_id=collection_id,
        item_type='CardCopy',
        item_id=str(copy.id),
        item_order=max_order + 1
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({'success': True})
