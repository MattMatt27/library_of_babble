"""
Music/Playlists Routes
"""
from flask import render_template, request, jsonify
from flask_login import login_required
from app.music import music_bp
from app.music.services import (
    generate_monthly_playlists_df,
    select_playlist,
    get_site_approved_playlists
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

        monthly_playlists_df = generate_monthly_playlists_df()
        playlist_id, playlist_art, playlist_name = select_playlist(
            monthly_playlists_df,
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
        # Exclude monthly playlists when rendering the page
        monthly_playlists_df = generate_monthly_playlists_df()
        monthly_playlist_ids = monthly_playlists_df['playlist_id'].tolist() if not monthly_playlists_df.empty else []

        # Filter approved playlists
        approved_playlists = [
            playlist for playlist in approved_playlists
            if playlist['id'] not in monthly_playlist_ids
        ]

        return render_template('music/index.html', approved_playlists=approved_playlists)
