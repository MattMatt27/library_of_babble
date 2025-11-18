/**
 * Spotify Refresh
 * Handles Spotify playlist data refresh
 */

import { showStatus } from '../core/utilities.js';
import { closeModal } from '../core/modals.js';

/**
 * Submit Spotify playlist refresh request
 * Refreshes playlist data from Spotify API
 */
export function submitSpotifyRefresh() {
    const statusDiv = document.getElementById('spotifyStatus');

    showStatus(statusDiv, 'Refreshing Spotify playlists...', 'loading');

    fetch('/account/refresh/spotify', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            let message = `Refresh complete!\nPlaylists updated: ${data.playlists_updated}`;
            showStatus(statusDiv, message, 'success');

            setTimeout(() => {
                closeModal('spotifyModal');
                location.reload();
            }, 3000);
        } else {
            showStatus(statusDiv, data.error || 'Refresh failed', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showStatus(statusDiv, 'An error occurred during refresh', 'error');
    });
}
