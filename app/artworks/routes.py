"""
Artworks Routes
"""
from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.artworks import artworks_bp
from app.artworks.models import Artworks, LikedArtworks
from app.artworks.services import get_approved_artworks_from_db, get_all_artworks
from app.extensions import db


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
        collection_filter=collection_filter
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
