"""
Writing Routes
"""
from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.writing import writing_bp
from app.writing.models import Publication, Author, PublicationAuthor
from app.extensions import db
from functools import wraps
import uuid
from datetime import datetime


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


# Category display names (hardcoded)
CATEGORY_NAMES = {
    'journal_article': 'Journal Articles',
    'conference_talk': 'Conference Talks',
    'editor': 'Editor',
    'fiction': 'Fiction',
    'essay': 'Essays',
    'poetry': 'Poetry'
}


@writing_bp.route('/')
def index():
    """Writing page with publications"""

    # Define category order
    ACADEMIC_CATEGORY_ORDER = ['journal_article', 'conference_talk', 'editor']
    CREATIVE_CATEGORY_ORDER = ['fiction', 'essay', 'poetry']

    # Get all publications
    all_pubs = Publication.query.order_by(
        Publication.display_order.asc(),
        Publication.publication_date.desc()
    ).all()

    # Group by section, then by category
    grouped = {
        'academic': {},
        'creative': {}
    }

    for pub in all_pubs:
        if pub.category not in grouped[pub.section]:
            grouped[pub.section][pub.category] = []
        grouped[pub.section][pub.category].append(pub)

    # Sort categories in the correct order
    academic_pubs = {cat: grouped['academic'][cat] for cat in ACADEMIC_CATEGORY_ORDER if cat in grouped['academic']}
    creative_pubs = {cat: grouped['creative'][cat] for cat in CREATIVE_CATEGORY_ORDER if cat in grouped['creative']}

    return render_template(
        'writing/index.html',
        academic_pubs=academic_pubs,
        creative_pubs=creative_pubs,
        category_names=CATEGORY_NAMES
    )


@writing_bp.route('/create', methods=['POST'])
@admin_required
def create_publication():
    """Create a new publication"""
    data = request.get_json()

    # Validate required fields
    required = ['title', 'authors', 'venue', 'publication_date', 'category', 'section']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate section
    if data['section'] not in ['academic', 'creative']:
        return jsonify({'error': 'Invalid section'}), 400

    # Validate authors is a list
    if not isinstance(data['authors'], list) or len(data['authors']) == 0:
        return jsonify({'error': 'Authors must be a non-empty list'}), 400

    try:
        # Helper function to safely strip strings
        def safe_strip(value):
            if value is None or value == '':
                return None
            return value.strip() if isinstance(value, str) else str(value).strip()

        publication = Publication(
            id=str(uuid.uuid4()),
            title=data['title'].strip(),
            venue=data['venue'].strip(),
            publication_date=data['publication_date'].strip(),
            url=safe_strip(data.get('url')) or None,
            doi=safe_strip(data.get('doi')) or None,
            pmid=safe_strip(data.get('pmid')) or None,
            volume_issue=safe_strip(data.get('volume_issue')) or None,
            badge=safe_strip(data.get('badge')) or None,
            category=data['category'],
            section=data['section'],
            display_order=data.get('display_order', 0)
        )

        db.session.add(publication)
        db.session.flush()  # Get publication ID before adding authors

        # Add authors
        for order, author_data in enumerate(data['authors'], start=1):
            author_name = author_data['name'].strip()

            # Check if author exists, create if not
            author = Author.query.filter_by(name=author_name).first()
            if not author:
                author = Author(
                    id=str(uuid.uuid4()),
                    name=author_name,
                    is_you=author_data.get('is_you', False)
                )
                db.session.add(author)
                db.session.flush()

            # Create publication-author relationship
            pub_author = PublicationAuthor(
                id=str(uuid.uuid4()),
                publication_id=publication.id,
                author_id=author.id,
                author_order=order
            )
            db.session.add(pub_author)

        db.session.commit()

        return jsonify({
            'success': True,
            'publication_id': publication.id,
            'message': 'Publication created successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@writing_bp.route('/get/<publication_id>', methods=['GET'])
@admin_required
def get_publication(publication_id):
    """Get publication data for editing"""
    publication = Publication.query.get(publication_id)
    if not publication:
        return jsonify({'error': 'Publication not found'}), 404

    return jsonify({
        'success': True,
        'publication': publication.to_dict()
    })


@writing_bp.route('/update/<publication_id>', methods=['POST'])
@admin_required
def update_publication(publication_id):
    """Update an existing publication"""
    publication = Publication.query.get(publication_id)
    if not publication:
        return jsonify({'error': 'Publication not found'}), 404

    data = request.get_json()

    try:
        # Helper function to safely strip strings
        def safe_strip(value):
            if value is None or value == '':
                return None
            return value.strip() if isinstance(value, str) else str(value).strip()

        # Update basic fields
        publication.title = data.get('title', publication.title).strip()
        publication.venue = data.get('venue', publication.venue).strip()
        publication.publication_date = data.get('publication_date', publication.publication_date).strip()
        publication.url = safe_strip(data.get('url')) or None
        publication.doi = safe_strip(data.get('doi')) or None
        publication.pmid = safe_strip(data.get('pmid')) or None
        publication.volume_issue = safe_strip(data.get('volume_issue')) or None
        publication.badge = safe_strip(data.get('badge')) or None
        publication.category = data.get('category', publication.category)
        publication.section = data.get('section', publication.section)
        publication.display_order = data.get('display_order', publication.display_order)
        publication.updated_at = datetime.utcnow()

        # Update authors if provided
        if 'authors' in data:
            if not isinstance(data['authors'], list) or len(data['authors']) == 0:
                return jsonify({'error': 'Authors must be a non-empty list'}), 400

            # Remove existing author relationships
            PublicationAuthor.query.filter_by(publication_id=publication.id).delete()

            # Add new author relationships
            for order, author_data in enumerate(data['authors'], start=1):
                author_name = author_data['name'].strip()

                # Check if author exists, create if not
                author = Author.query.filter_by(name=author_name).first()
                if not author:
                    author = Author(
                        id=str(uuid.uuid4()),
                        name=author_name,
                        is_you=author_data.get('is_you', False)
                    )
                    db.session.add(author)
                    db.session.flush()

                # Create publication-author relationship
                pub_author = PublicationAuthor(
                    id=str(uuid.uuid4()),
                    publication_id=publication.id,
                    author_id=author.id,
                    author_order=order
                )
                db.session.add(pub_author)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Publication updated successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@writing_bp.route('/delete/<publication_id>', methods=['DELETE'])
@admin_required
def delete_publication(publication_id):
    """Delete a publication"""
    publication = Publication.query.get(publication_id)
    if not publication:
        return jsonify({'error': 'Publication not found'}), 404

    try:
        db.session.delete(publication)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Publication deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@writing_bp.route('/authors', methods=['GET'])
@admin_required
def get_authors():
    """Get all authors for autocomplete"""
    authors = Author.query.order_by(Author.name).all()
    return jsonify({
        'success': True,
        'authors': [author.to_dict() for author in authors]
    })


@writing_bp.route('/authors/search', methods=['GET'])
@admin_required
def search_authors():
    """Search authors by name"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'success': True, 'authors': []})

    authors = Author.query.filter(
        Author.name.ilike(f'%{query}%')
    ).order_by(Author.name).limit(10).all()

    return jsonify({
        'success': True,
        'authors': [author.to_dict() for author in authors]
    })


@writing_bp.route('/publications/all', methods=['GET'])
@admin_required
def get_all_publications():
    """Get all publications for management interface"""
    publications = Publication.query.order_by(
        Publication.section.asc(),
        Publication.category.asc(),
        Publication.display_order.asc()
    ).all()

    return jsonify({
        'success': True,
        'publications': [pub.to_dict() for pub in publications]
    })


@writing_bp.route('/publications/reorder', methods=['POST'])
@admin_required
def reorder_publications():
    """Update display order for publications"""
    data = request.get_json()

    if not isinstance(data.get('publication_ids'), list):
        return jsonify({'error': 'publication_ids must be a list'}), 400

    try:
        for index, pub_id in enumerate(data['publication_ids']):
            publication = Publication.query.get(pub_id)
            if publication:
                publication.display_order = index
                publication.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Publication order updated successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
