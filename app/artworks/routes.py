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
    # Get pagination and filter parameters from the request
    page = request.args.get('page', 1, type=int)
    per_page = 50
    sort_order = request.args.get('sort_order', 'random')
    start_date = request.args.get('start_date', None, type=int)
    end_date = request.args.get('end_date', None, type=int)
    artist_filter = request.args.getlist('artist')
    selected_artists = request.args.getlist('artist')

    # Get user's liked artworks
    liked_artworks = {
        like.artwork_id
        for like in LikedArtworks.query.filter_by(user_id=current_user.id).all()
    }

    # Fetch paginated and filtered artworks
    approved_artworks, total_pages, all_artists = get_approved_artworks_from_db(
        page=page,
        per_page=per_page,
        sort_order=sort_order,
        start_date=start_date,
        end_date=end_date,
        artist_filter=artist_filter
    )

    return render_template(
        'artworks/pondering.html',
        approved_artworks=approved_artworks,
        current_page=page,
        total_pages=total_pages,
        all_artists=all_artists,
        selected_artists=selected_artists,
        liked_artworks=liked_artworks
    )


@artworks_bp.route('/galleries')
def galleries():
    """Curated artwork galleries page"""
    all_artworks = get_all_artworks()

    # Get liked artworks
    liked_artwork_ids = set()
    if current_user.is_authenticated:
        liked_artwork_ids = {
            like.artwork_id
            for like in LikedArtworks.query.filter_by(user_id=current_user.id).all()
        }

    # Get artworks by location/medium
    at_boston_museums_ids = {
        work.id
        for work in Artworks.query.filter(Artworks.location.like('%Boston%')).all()
    }
    worcester_artwork_ids = {
        work.id
        for work in Artworks.query.filter_by(location="Worcester Art Museum, Worcester, MA").all()
    }
    oil_on_canvas_artwork_ids = {
        work.id
        for work in Artworks.query.filter_by(medium="Oil on canvas").all()
    }
    watercolor_artwork_ids = {
        work.id
        for work in Artworks.query.filter(Artworks.medium.like('%watercolor%')).all()
    }

    # Filter artworks based on these IDs
    liked_artworks = [art for art in all_artworks if art['id'] in liked_artwork_ids]
    at_boston_museums = [art for art in all_artworks if art['id'] in at_boston_museums_ids]
    worcester_artworks = [art for art in all_artworks if art['id'] in worcester_artwork_ids]
    oil_on_canvas_artworks = [art for art in all_artworks if art['id'] in oil_on_canvas_artwork_ids]
    watercolor_artworks = [art for art in all_artworks if art['id'] in watercolor_artwork_ids]

    # Shuffle and take first 25
    import random
    random.shuffle(all_artworks)

    display_liked_artworks = [art for art in all_artworks if art['id'] in liked_artwork_ids][:25]
    display_at_boston_museums = [art for art in all_artworks if art['id'] in at_boston_museums_ids][:25]
    display_worcester_artworks = [art for art in all_artworks if art['id'] in worcester_artwork_ids][:25]
    display_oil_on_canvas_artworks = [art for art in all_artworks if art['id'] in oil_on_canvas_artwork_ids][:25]
    display_watercolor_artworks = [art for art in all_artworks if art['id'] in watercolor_artwork_ids][:25]

    return render_template(
        'artworks/galleries.html',
        liked_artworks_count=len(liked_artworks),
        at_boston_museums_count=len(at_boston_museums),
        worcester_artworks_count=len(worcester_artworks),
        oil_on_canvas_artworks_count=len(oil_on_canvas_artworks),
        watercolor_artworks_count=len(watercolor_artworks),
        display_liked_artworks=display_liked_artworks,
        display_at_boston_museums=display_at_boston_museums,
        display_worcester_artworks=display_worcester_artworks,
        display_oil_on_canvas_artworks=display_oil_on_canvas_artworks,
        display_watercolor_artworks=display_watercolor_artworks
    )


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
