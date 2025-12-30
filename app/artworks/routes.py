"""
Artworks Routes
"""
from flask import render_template, request, jsonify, session
from flask_login import login_required, current_user
from app.artworks import artworks_bp
from app.artworks.models import Artworks, LikedArtworks
from app.artworks.services import get_approved_artworks_from_db, get_all_artworks
from app.extensions import db
import time


@artworks_bp.route('/pondering')
@login_required
def pondering():
    """Artwork browsing page with filters and pagination"""
    from app.artworks.models import ArtworkGallery

    # Get pagination and filter parameters from the request
    page = request.args.get('page', 1, type=int)
    per_page = 50
    sort_order = request.args.get('sort_order', 'random')
    start_date = request.args.get('start_date', None, type=int)
    end_date = request.args.get('end_date', None, type=int)
    artist_filter = request.args.getlist('artist')
    collection_filter = request.args.getlist('collection')
    selected_artists = request.args.getlist('artist')
    selected_collections = request.args.getlist('collection')

    # Generate a random seed for consistent random ordering across pagination
    # Reset seed when filters change or when switching back to random sort
    filter_key = f"{','.join(sorted(artist_filter))}_{','.join(sorted(collection_filter))}"

    if sort_order == 'random':
        # Get the previous sort order from session
        previous_sort_order = session.get('previous_sort_order')

        # Generate new seed if:
        # 1. No seed exists yet
        # 2. Filters changed
        # 3. Switching back to random from a different sort order
        if ('random_seed' not in session or
            session.get('filter_key') != filter_key or
            previous_sort_order != 'random'):
            session['random_seed'] = int(time.time() * 1000000) % 2147483647  # SQLite RANDOM() seed range
            session['filter_key'] = filter_key
        random_seed = session['random_seed']
    else:
        random_seed = None

    # Store current sort order for next request
    session['previous_sort_order'] = sort_order

    # Get user's liked artworks
    liked_artworks = {
        like.artwork_id
        for like in LikedArtworks.query.filter_by(user_id=current_user.id).all()
    }

    # Get all galleries for the filter dropdown (filter by is_public unless admin)
    if current_user.role == 'admin':
        all_galleries = ArtworkGallery.query.order_by(ArtworkGallery.display_order.asc()).all()
    else:
        all_galleries = ArtworkGallery.query.filter_by(is_public=True).order_by(ArtworkGallery.display_order.asc()).all()

    # Fetch paginated and filtered artworks
    approved_artworks, total_pages, all_artists = get_approved_artworks_from_db(
        page=page,
        per_page=per_page,
        sort_order=sort_order,
        start_date=start_date,
        end_date=end_date,
        artist_filter=artist_filter,
        collection_filter=collection_filter,
        random_seed=random_seed
    )

    return render_template(
        'artworks/pondering.html',
        approved_artworks=approved_artworks,
        current_page=page,
        total_pages=total_pages,
        all_artists=all_artists,
        all_galleries=all_galleries,
        selected_artists=selected_artists,
        selected_collections=selected_collections,
        liked_artworks=liked_artworks
    )


@artworks_bp.route('/galleries')
def galleries():
    """Curated artwork galleries page"""
    import random
    from app.artworks.models import ArtworkGallery, ArtworkGalleryItem

    # Get all galleries ordered by display_order (filter by is_public unless admin)
    if current_user.is_authenticated and current_user.role == 'admin':
        galleries_list = ArtworkGallery.query.order_by(ArtworkGallery.display_order.asc()).all()
    else:
        galleries_list = ArtworkGallery.query.filter_by(is_public=True).order_by(ArtworkGallery.display_order.asc()).all()

    # Build galleries data structure
    galleries_data = []

    # Handle liked artworks separately (user-specific)
    if current_user.is_authenticated:
        liked_artwork_ids = {
            like.artwork_id
            for like in LikedArtworks.query.filter_by(user_id=current_user.id).all()
        }
        if liked_artwork_ids:
            liked_artworks = Artworks.query.filter(
                Artworks.id.in_(liked_artwork_ids),
                Artworks.site_approved == True
            ).all()

            # Shuffle and take first 25
            random.shuffle(liked_artworks)
            display_liked = liked_artworks[:25]

            galleries_data.append({
                'id': 'liked_artworks',
                'name': 'Your Liked Artworks',
                'count': len(liked_artworks),
                'artworks': [artwork_to_dict(art) for art in display_liked]
            })

    # Process system galleries
    for gallery in galleries_list:
        # Get artworks in this gallery
        artwork_ids = [
            item.artwork_id
            for item in ArtworkGalleryItem.query.filter_by(gallery_id=gallery.id).all()
        ]

        if artwork_ids:
            artworks = Artworks.query.filter(
                Artworks.id.in_(artwork_ids),
                Artworks.site_approved == True
            ).all()

            # Shuffle and take first 25
            random.shuffle(artworks)
            display_artworks = artworks[:25]

            galleries_data.append({
                'id': gallery.id,
                'name': gallery.name,
                'count': len(artworks),
                'artworks': [artwork_to_dict(art) for art in display_artworks]
            })

    return render_template(
        'artworks/galleries.html',
        collections=galleries_data
    )


def artwork_to_dict(artwork):
    """Convert artwork object to dictionary for template"""
    return {
        'id': artwork.id,
        'title': artwork.title,
        'artist': artwork.artist,
        'filesystem_artist': artwork.artist or '',
        'year': artwork.year,
        'file_name': artwork.file_name,
        'location': artwork.location,
        'medium': artwork.medium,
        'description': artwork.description
    }


@artworks_bp.route('/like_artwork', methods=['POST'])
@login_required
def like_artwork():
    """Toggle artwork like (API endpoint)"""
    artwork_id = request.json.get('artwork_id')
    if not artwork_id:
        return jsonify({'error': 'Artwork ID is required'}), 400

    liked = LikedArtworks.query.filter_by(
        user_id=current_user.id,
        artwork_id=artwork_id
    ).first()

    if liked:
        # If already liked, remove the like
        db.session.delete(liked)
        db.session.commit()
        return jsonify({'liked': False})
    else:
        # Otherwise, add the like
        new_like = LikedArtworks(user_id=current_user.id, artwork_id=artwork_id)
        db.session.add(new_like)
        db.session.commit()
        return jsonify({'liked': True})


@artworks_bp.route('/is_liked', methods=['GET'])
@login_required
def is_liked():
    """Check if artwork is liked (API endpoint)"""
    artwork_id = request.args.get('artwork_id')
    if not artwork_id:
        return jsonify({'error': 'Artwork ID is required'}), 400

    liked = LikedArtworks.query.filter_by(
        user_id=current_user.id,
        artwork_id=artwork_id
    ).first()

    return jsonify({'liked': bool(liked)})


@artworks_bp.route('/api/artists', methods=['GET'])
@login_required
def get_artists():
    """
    Get list of unique artists.

    Query params:
        q (optional): Search query to filter artists (case-insensitive, partial match)

    Returns:
        JSON array of artist names, sorted alphabetically
    """
    query = request.args.get('q', '').strip()

    # Base query for distinct artists
    artists_query = db.session.query(Artworks.artist).filter(
        Artworks.artist.isnot(None),
        Artworks.artist != ''
    ).distinct()

    # Apply search filter if provided
    if query:
        artists_query = artists_query.filter(
            Artworks.artist.ilike(f'%{query}%')
        )

    # Execute and format results
    artists = artists_query.order_by(Artworks.artist).limit(50).all()

    return jsonify([artist[0] for artist in artists])


@artworks_bp.route('/get_artwork', methods=['GET'])
@login_required
def get_artwork():
    """Get full artwork details for editing (admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    artwork_id = request.args.get('artwork_id')
    if not artwork_id:
        return jsonify({'success': False, 'error': 'Artwork ID is required'}), 400

    artwork = Artworks.query.get(artwork_id)
    if not artwork:
        return jsonify({'success': False, 'error': 'Artwork not found'}), 404

    return jsonify({
        'success': True,
        'artwork': {
            'id': artwork.id,
            'title': artwork.title,
            'artist': artwork.artist,
            'year': artwork.year,
            'medium': artwork.medium,
            'location': artwork.location,
            'series': artwork.series,
            'description': artwork.description,
            'site_approved': artwork.site_approved,
            'file_name': artwork.file_name
        }
    })


@artworks_bp.route('/update_artwork', methods=['POST'])
@login_required
def update_artwork():
    """Update artwork metadata (admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    artwork_id = data.get('artwork_id')
    if not artwork_id:
        return jsonify({'success': False, 'error': 'Artwork ID is required'}), 400

    artwork = Artworks.query.get(artwork_id)
    if not artwork:
        return jsonify({'success': False, 'error': 'Artwork not found'}), 404

    try:
        # Update fields
        artwork.title = data.get('title', artwork.title)
        artwork.artist = data.get('artist', artwork.artist)
        artwork.year = data.get('year', artwork.year)
        artwork.medium = data.get('medium') or None
        artwork.location = data.get('location') or None
        artwork.series = data.get('series') or None
        artwork.description = data.get('description') or None
        artwork.site_approved = data.get('site_approved', artwork.site_approved)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Artwork updated successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Failed to update: {str(e)}'
        }), 500
