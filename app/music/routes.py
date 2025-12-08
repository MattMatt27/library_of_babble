"""
Music/Playlists Routes
"""
from flask import render_template, request, jsonify
from flask_login import login_required
from app.music import music_bp
from app.music.services import (
    generate_monthly_playlists,
    select_playlist,
    get_site_approved_playlists,
    get_approved_playlist_collections
)


@music_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """Listening page with playlists and date picker"""
    approved_playlists = get_site_approved_playlists()

    if request.method == 'POST':
        selected_month = request.json['month']
        selected_year = request.json['year']
        search_term = request.json['playlist_code']

        monthly_playlists = generate_monthly_playlists()
        playlist_id, playlist_art, playlist_name = select_playlist(
            monthly_playlists,
            search_term
        )

        if playlist_id is not None:
            playlist_data = {
                'playlist_id': playlist_id,
                'playlist_art': playlist_art,
                'playlist_name': playlist_name,
            }
            return jsonify(playlist_data)
        else:
            return jsonify({
                'error': 'Playlist not found for the selected month and year.'
            }), 404
    else:
        # Get monthly playlist IDs to exclude from other sections
        monthly_playlists = generate_monthly_playlists()
        monthly_playlist_ids = [p['playlist_id'] for p in monthly_playlists]

        # Get collections with playlists
        playlist_collections = get_approved_playlist_collections()

        # Get individual approved playlists (not in any collection)
        approved_playlists = get_site_approved_playlists()

        # Find which playlists are already in collections
        playlists_in_collections = set()
        for collection_data in playlist_collections.values():
            for playlist in collection_data['playlists']:
                playlists_in_collections.add(playlist['id'])

        # Filter: exclude monthly playlists AND playlists already in collections
        other_playlists = [
            playlist for playlist in approved_playlists
            if playlist['id'] not in monthly_playlist_ids
            and playlist['id'] not in playlists_in_collections
        ]

        return render_template(
            'music/index.html',
            playlist_collections=playlist_collections,
            other_playlists=other_playlists
        )
