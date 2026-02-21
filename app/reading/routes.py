"""
Reading Routes
Main reading page with recommendations and recently read content
"""
import random
from flask import render_template, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy import func
from app.reading import reading_bp
from app.books.models import Books, BookQuote, BookPairing, LikedQuotes
from app.books.services import (
    get_recently_read_books,
    read_books_from_db,
    get_books_from_bookshelf
)
from app.common.models import Collection, CollectionItem, ContentPairing
from app.common.services import get_pairings_for_page, search_all_content, get_content_item
from app.utils.security import page_visible
from app.extensions import db


@reading_bp.route('/')
@page_visible('reading')
def index():
    """Reading page with recently read and recommendations"""
    recently_read_books = get_recently_read_books()

    # Get all approved Book collections, ordered by sort_order
    book_collections = Collection.query.filter_by(
        collection_type='Book',
        site_approved=True
    ).order_by(Collection.sort_order.asc().nullslast(), Collection.collection_name).all()

    # Build shelves data from collections
    shelves = []
    for collection in book_collections:
        books = get_books_from_bookshelf(collection.collection_name)
        if books:  # Only include shelves that have books
            shelves.append({
                'id': collection.id,
                'name': collection.collection_name,
                'display_name': collection.description or collection.collection_name.replace('-', ' ').title(),
                'books': books
            })

    # Get all visible pairings where at least one side is a Book
    content_pairings = get_pairings_for_page(['Book'])

    # Get a random short quote (under 300 chars) for the quote card
    short_quotes = BookQuote.query.filter(
        func.length(BookQuote.quote_text) <= 300
    ).all()

    random_quote = None
    if short_quotes:
        quote = random.choice(short_quotes)
        book = Books.query.get(quote.book_id)
        if book:
            random_quote = {
                'id': quote.id,
                'text': quote.quote_text,
                'book_title': book.title,
                'book_author': book.author,
                'book_id': book.id,
                'chapter': quote.chapter,
                'page_number': quote.page_number
            }

    return render_template(
        'books/reading.html',
        recently_read_books=recently_read_books,
        shelves=shelves,
        content_pairings=content_pairings,
        random_quote=random_quote,
        current_user=current_user
    )


@reading_bp.route('/books')
@page_visible('books')
def books():
    """List all books"""
    books_data = read_books_from_db()
    return render_template('books/index.html', books=books_data)


@reading_bp.route('/api/pairing', methods=['GET'])
@login_required
def get_pairing():
    """Get most recent content pairing"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    pairing = ContentPairing.query.order_by(ContentPairing.updated_at.desc()).first()
    if pairing:
        item_1 = get_content_item(pairing.item_type_1, pairing.item_id_1)
        item_2 = get_content_item(pairing.item_type_2, pairing.item_id_2)
        if item_1 and item_2:
            return jsonify({
                'item_type_1': pairing.item_type_1,
                'item_id_1': pairing.item_id_1,
                'item_title_1': item_1['title'],
                'item_subtitle_1': item_1['subtitle'],
                'item_type_2': pairing.item_type_2,
                'item_id_2': pairing.item_id_2,
                'item_title_2': item_2['title'],
                'item_subtitle_2': item_2['subtitle'],
                'note': pairing.note
            })
    return jsonify({'item_id_1': None, 'item_id_2': None, 'note': None})


@reading_bp.route('/api/pairing', methods=['POST'])
@login_required
def set_pairing():
    """Create or update content pairing (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    pairing_id = data.get('id')
    item_type_1 = data.get('item_type_1')
    item_id_1 = str(data.get('item_id_1'))
    item_type_2 = data.get('item_type_2')
    item_id_2 = str(data.get('item_id_2'))
    note = data.get('note', '').strip()
    is_visible = data.get('is_visible', True)

    if not item_id_1 or not item_id_2 or not note:
        return jsonify({'error': 'Two items and a note are required'}), 400

    if item_type_1 == item_type_2 and item_id_1 == item_id_2:
        return jsonify({'error': 'Please select two different items'}), 400

    # Verify both items exist
    item_1 = get_content_item(item_type_1, item_id_1)
    item_2 = get_content_item(item_type_2, item_id_2)
    if not item_1 or not item_2:
        return jsonify({'error': 'One or both items not found'}), 404

    if pairing_id:
        pairing = ContentPairing.query.get(pairing_id)
        if not pairing:
            return jsonify({'error': 'Pairing not found'}), 404
        pairing.item_type_1 = item_type_1
        pairing.item_id_1 = item_id_1
        pairing.item_type_2 = item_type_2
        pairing.item_id_2 = item_id_2
        pairing.note = note
        pairing.is_visible = is_visible
        pairing.updated_by = current_user.id
    else:
        pairing = ContentPairing(
            item_type_1=item_type_1,
            item_id_1=item_id_1,
            item_type_2=item_type_2,
            item_id_2=item_id_2,
            note=note,
            is_visible=is_visible,
            updated_by=current_user.id
        )
        db.session.add(pairing)

    db.session.commit()
    return jsonify({'success': True})


@reading_bp.route('/api/content/search', methods=['GET'])
@login_required
def search_content():
    """Search across all content types for the pairing modal"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    query = request.args.get('q', '').strip()
    return jsonify(search_all_content(query))


@reading_bp.route('/api/books/search', methods=['GET'])
@login_required
def search_books():
    """Search books (backward compat, also used by shelf modal)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])

    books = Books.query.filter(
        db.or_(
            Books.title.ilike(f'%{query}%'),
            Books.author.ilike(f'%{query}%')
        )
    ).limit(20).all()

    return jsonify([{
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'cover_image_url': book.cover_image_url
    } for book in books])


@reading_bp.route('/quotes')
@page_visible('reading-quotes')
def quotes():
    """Quotes exploration page with pagination"""
    from flask import session
    import time

    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 100
    sort_order = request.args.get('sort', 'random')
    book_filter = request.args.get('book', None, type=int)
    liked_only = request.args.get('liked', 'false') == 'true'

    # Generate a random seed for consistent random ordering across pagination
    filter_key = f"{book_filter}_{liked_only}"

    if sort_order == 'random':
        previous_sort = session.get('quotes_previous_sort')
        if ('quotes_random_seed' not in session or
            session.get('quotes_filter_key') != filter_key or
            previous_sort != 'random'):
            session['quotes_random_seed'] = int(time.time() * 1000000) % 2147483647
            session['quotes_filter_key'] = filter_key
        random_seed = session['quotes_random_seed']
    else:
        random_seed = None

    session['quotes_previous_sort'] = sort_order

    # Get user's liked quotes (if authenticated)
    liked_quote_ids = set()
    if current_user.is_authenticated:
        liked_quotes = LikedQuotes.query.filter_by(
            user_id=current_user.id
        ).all()
        liked_quote_ids = {like.quote_id for like in liked_quotes}

    # Build query with filters
    query = BookQuote.query

    if book_filter:
        query = query.filter(BookQuote.book_id == str(book_filter))

    # Get all matching quotes first (for liked filter and sorting)
    all_quotes = query.all()

    # Build quotes data with book info
    quotes_data = []
    for quote in all_quotes:
        book = Books.query.get(quote.book_id)
        if book:
            is_liked = quote.id in liked_quote_ids
            # Skip if liked_only filter is active and quote is not liked
            if liked_only and not is_liked:
                continue
            quotes_data.append({
                'id': quote.id,
                'text': quote.quote_text,
                'book_id': book.id,
                'book_title': book.title,
                'book_author': book.author,
                'book_cover': book.cover_image_url,
                'book_year': book.original_publication_year,
                'chapter': quote.chapter,
                'page_number': quote.page_number,
                'is_liked': is_liked
            })

    # Apply sorting
    if sort_order == 'random' and random_seed:
        random.seed(random_seed)
        random.shuffle(quotes_data)
    elif sort_order == 'book-title':
        quotes_data.sort(key=lambda q: q['book_title'].lower())
    elif sort_order == 'book-year-asc':
        quotes_data.sort(key=lambda q: q['book_year'] or 0)
    elif sort_order == 'book-year-desc':
        quotes_data.sort(key=lambda q: q['book_year'] or 0, reverse=True)

    # Calculate pagination
    total_quotes = len(quotes_data)
    total_pages = max(1, (total_quotes + per_page - 1) // per_page)
    page = min(page, total_pages)  # Don't go past last page

    # Slice for current page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_quotes = quotes_data[start_idx:end_idx]

    # Get unique books for filtering (from all quotes, not filtered)
    all_book_ids = [q.book_id for q in BookQuote.query.all()]
    books_with_quotes = Books.query.filter(
        Books.id.in_(all_book_ids)
    ).order_by(Books.title).all()

    return render_template(
        'books/quotes.html',
        quotes=paginated_quotes,
        books_with_quotes=books_with_quotes,
        current_page=page,
        total_pages=total_pages,
        total_quotes=total_quotes,
        sort_order=sort_order,
        book_filter=book_filter,
        liked_only=liked_only,
        current_user=current_user
    )


@reading_bp.route('/api/shelf', methods=['POST'])
@login_required
def create_shelf():
    """Create a new book shelf/collection (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    name = data.get('name', '').strip()
    display_name = data.get('display_name', '').strip()

    if not name:
        return jsonify({'error': 'Shelf name is required'}), 400

    # Convert display name to slug for collection_name
    collection_name = name.lower().replace(' ', '-')

    # Check if collection already exists
    existing = Collection.query.filter_by(collection_name=collection_name).first()
    if existing:
        return jsonify({'error': 'A shelf with this name already exists'}), 400

    # Get max sort_order for Book collections
    max_order = db.session.query(func.max(Collection.sort_order)).filter_by(
        collection_type='Book'
    ).scalar() or 0

    collection = Collection(
        collection_name=collection_name,
        description=display_name or name,
        collection_type='Book',
        site_approved=True,
        sort_order=max_order + 1
    )
    db.session.add(collection)
    db.session.commit()

    return jsonify({
        'success': True,
        'id': collection.id,
        'name': collection.collection_name,
        'display_name': collection.description
    })


@reading_bp.route('/api/shelf/<int:shelf_id>', methods=['PUT'])
@login_required
def update_shelf(shelf_id):
    """Update an existing book shelf/collection (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    collection = Collection.query.get(shelf_id)
    if not collection:
        return jsonify({'error': 'Shelf not found'}), 404

    data = request.get_json()
    display_name = data.get('display_name', '').strip()

    if not display_name:
        return jsonify({'error': 'Shelf name is required'}), 400

    collection.description = display_name
    db.session.commit()

    return jsonify({
        'success': True,
        'id': collection.id,
        'name': collection.collection_name,
        'display_name': collection.description
    })


@reading_bp.route('/api/shelf/<int:shelf_id>/books', methods=['GET'])
@login_required
def get_shelf_books(shelf_id):
    """Get all books in a shelf (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    collection = Collection.query.get(shelf_id)
    if not collection:
        return jsonify({'error': 'Shelf not found'}), 404

    items = CollectionItem.query.filter_by(
        collection_id=shelf_id,
        item_type='Book'
    ).order_by(CollectionItem.item_order.asc().nullslast()).all()

    books = []
    for item in items:
        book = Books.query.get(item.item_id)
        if book:
            books.append({
                'item_id': item.id,
                'book_id': book.id,
                'title': book.title,
                'author': book.author,
                'cover_image_url': book.cover_image_url,
                'order': item.item_order
            })

    return jsonify(books)


@reading_bp.route('/api/shelf/<int:shelf_id>/books', methods=['POST'])
@login_required
def add_book_to_shelf(shelf_id):
    """Add a book to a shelf (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    collection = Collection.query.get(shelf_id)
    if not collection:
        return jsonify({'error': 'Shelf not found'}), 404

    data = request.get_json()
    book_id = data.get('book_id')

    if not book_id:
        return jsonify({'error': 'Book ID is required'}), 400

    book = Books.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    # Check if book already in shelf
    existing = CollectionItem.query.filter_by(
        collection_id=shelf_id,
        item_type='Book',
        item_id=str(book_id)
    ).first()

    if existing:
        return jsonify({'error': 'Book is already on this shelf'}), 400

    # Get max order
    max_order = db.session.query(func.max(CollectionItem.item_order)).filter_by(
        collection_id=shelf_id
    ).scalar() or 0

    item = CollectionItem(
        collection_id=shelf_id,
        item_type='Book',
        item_id=str(book_id),
        item_order=max_order + 1
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({
        'success': True,
        'item_id': item.id,
        'book_id': book.id,
        'title': book.title,
        'author': book.author,
        'cover_image_url': book.cover_image_url,
        'order': item.item_order
    })


@reading_bp.route('/api/shelf/<int:shelf_id>/books/<int:item_id>', methods=['DELETE'])
@login_required
def remove_book_from_shelf(shelf_id, item_id):
    """Remove a book from a shelf (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    item = CollectionItem.query.filter_by(
        id=item_id,
        collection_id=shelf_id
    ).first()

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({'success': True})


@reading_bp.route('/api/shelf/<int:shelf_id>/reorder', methods=['POST'])
@login_required
def reorder_shelf_books(shelf_id):
    """Reorder books in a shelf (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    collection = Collection.query.get(shelf_id)
    if not collection:
        return jsonify({'error': 'Shelf not found'}), 404

    data = request.get_json()
    item_ids = data.get('item_ids', [])

    for index, item_id in enumerate(item_ids):
        item = CollectionItem.query.filter_by(
            id=item_id,
            collection_id=shelf_id
        ).first()
        if item:
            item.item_order = index + 1

    db.session.commit()

    return jsonify({'success': True})


@reading_bp.route('/api/shelves', methods=['GET'])
@login_required
def get_all_shelves():
    """Get all book shelves for reordering (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    collections = Collection.query.filter_by(
        collection_type='Book',
        site_approved=True
    ).order_by(Collection.sort_order.asc().nullslast(), Collection.collection_name).all()

    return jsonify([{
        'id': c.id,
        'name': c.collection_name,
        'display_name': c.description or c.collection_name.replace('-', ' ').title(),
        'sort_order': c.sort_order
    } for c in collections])


@reading_bp.route('/api/shelves/reorder', methods=['POST'])
@login_required
def reorder_shelves():
    """Reorder shelves (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    shelf_ids = data.get('shelf_ids', [])

    for index, shelf_id in enumerate(shelf_ids):
        collection = Collection.query.get(shelf_id)
        if collection:
            collection.sort_order = index + 1

    db.session.commit()

    return jsonify({'success': True})
