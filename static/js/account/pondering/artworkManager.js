/**
 * Artwork Manager
 * Handles artwork uploads (both individual and CSV bulk import)
 */

import { showStatus } from '../core/utilities.js';

// Autocomplete state
let autocompleteTimeout = null;
let selectedIndex = -1;

/**
 * Initialize artist autocomplete
 * Call this when the upload modal is opened
 */
export function initArtistAutocomplete() {
    const input = document.getElementById('artworkArtist');
    const suggestionsDiv = document.getElementById('artistSuggestions');

    if (!input || !suggestionsDiv) return;

    // Input event with debounce
    input.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        // Clear previous timeout
        if (autocompleteTimeout) {
            clearTimeout(autocompleteTimeout);
        }

        // Hide suggestions if query is too short
        if (query.length < 2) {
            suggestionsDiv.style.display = 'none';
            return;
        }

        // Debounce the API call
        autocompleteTimeout = setTimeout(() => {
            fetchArtistSuggestions(query);
        }, 300);
    });

    // Keyboard navigation
    input.addEventListener('keydown', (e) => {
        const items = suggestionsDiv.querySelectorAll('.autocomplete-item');

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
            updateSelection(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, -1);
            updateSelection(items);
        } else if (e.key === 'Enter' && selectedIndex >= 0) {
            e.preventDefault();
            if (items[selectedIndex]) {
                selectArtist(items[selectedIndex].textContent);
            }
        } else if (e.key === 'Escape') {
            suggestionsDiv.style.display = 'none';
            selectedIndex = -1;
        }
    });

    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !suggestionsDiv.contains(e.target)) {
            suggestionsDiv.style.display = 'none';
            selectedIndex = -1;
        }
    });
}

/**
 * Fetch artist suggestions from API
 */
async function fetchArtistSuggestions(query) {
    const suggestionsDiv = document.getElementById('artistSuggestions');

    try {
        const response = await fetch(`/artworks/api/artists?q=${encodeURIComponent(query)}`);
        const artists = await response.json();

        if (artists.length === 0) {
            suggestionsDiv.style.display = 'none';
            return;
        }

        // Build suggestion items
        suggestionsDiv.innerHTML = artists.map(artist =>
            `<div class="autocomplete-item">${escapeHtml(artist)}</div>`
        ).join('');

        // Add click handlers
        suggestionsDiv.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', () => {
                selectArtist(item.textContent);
            });
        });

        suggestionsDiv.style.display = 'block';
        selectedIndex = -1;
    } catch (error) {
        console.error('Error fetching artist suggestions:', error);
        suggestionsDiv.style.display = 'none';
    }
}

/**
 * Select an artist from suggestions
 */
function selectArtist(artist) {
    const input = document.getElementById('artworkArtist');
    const suggestionsDiv = document.getElementById('artistSuggestions');

    input.value = artist;
    suggestionsDiv.style.display = 'none';
    selectedIndex = -1;

    // Move focus to next field
    const titleInput = document.getElementById('artworkTitle');
    if (titleInput) {
        titleInput.focus();
    }
}

/**
 * Update visual selection state
 */
function updateSelection(items) {
    items.forEach((item, index) => {
        if (index === selectedIndex) {
            item.classList.add('selected');
        } else {
            item.classList.remove('selected');
        }
    });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Switch between individual and CSV upload modes
 * @param {string} mode - Either 'individual' or 'csv'
 */
export function switchUploadMode(mode) {
    const csvSection = document.getElementById('csvUploadSection');
    const individualSection = document.getElementById('individualUploadSection');
    const tabs = document.querySelectorAll('[data-upload-mode]');

    // Update tab active states
    tabs.forEach(tab => {
        if (tab.getAttribute('data-upload-mode') === mode) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Toggle sections
    if (mode === 'csv') {
        csvSection.style.display = 'block';
        individualSection.style.display = 'none';
    } else {
        csvSection.style.display = 'none';
        individualSection.style.display = 'block';
    }
}

/**
 * Submit artwork upload (individual or CSV)
 * Handles both individual artwork upload and CSV bulk import
 */
export async function submitArtworkUpload() {
    const form = document.getElementById('uploadArtworkForm');
    const statusDiv = document.getElementById('uploadArtworkStatus');
    const progressDiv = document.getElementById('uploadArtworkProgress');
    const progressBar = document.getElementById('uploadArtworkProgressBar');
    const progressText = document.getElementById('uploadArtworkProgressText');
    const uploadBtn = document.getElementById('uploadArtworkBtn');
    const cancelBtn = document.getElementById('uploadArtworkCancelBtn');

    // Determine which mode is active
    const csvSection = document.getElementById('csvUploadSection');
    const isCsvMode = csvSection.style.display !== 'none';

    const formData = new FormData();
    let endpoint;

    if (isCsvMode) {
        // CSV Import mode
        const csvFileInput = document.getElementById('artworksCsvFile');

        if (!csvFileInput.files || csvFileInput.files.length === 0) {
            showStatus(statusDiv, 'Please select a CSV file', 'error');
            return;
        }

        formData.append('artworks_csv', csvFileInput.files[0]);
        endpoint = '/account/import_artworks_csv';
    } else {
        // Individual Upload mode
        const fileInput = document.getElementById('artworkFile');

        if (!fileInput.files || fileInput.files.length === 0) {
            showStatus(statusDiv, 'Please select an image file', 'error');
            return;
        }

        // Validate required fields
        const artist = document.getElementById('artworkArtist').value.trim();
        const title = document.getElementById('artworkTitle').value.trim();
        const year = document.getElementById('artworkYear').value.trim();

        if (!artist || !title || !year) {
            showStatus(statusDiv, 'Please fill in Artist, Title, and Year fields', 'error');
            return;
        }

        // Append all form fields
        formData.append('artwork_file', fileInput.files[0]);
        formData.append('artist', artist);
        formData.append('title', title);
        formData.append('year', year);
        formData.append('medium', document.getElementById('artworkMedium').value.trim());
        formData.append('location', document.getElementById('artworkLocation').value.trim());
        formData.append('series', document.getElementById('artworkSeries').value.trim());
        formData.append('description', document.getElementById('artworkDescription').value.trim());
        formData.append('site_approved', document.getElementById('artworkSiteApproved').checked ? 'true' : 'false');

        endpoint = '/account/upload_artwork';
    }

    try {
        // Show progress
        progressDiv.style.display = 'block';
        uploadBtn.disabled = true;
        cancelBtn.disabled = true;
        progressBar.style.width = '30%';
        progressText.textContent = isCsvMode ? 'Uploading CSV...' : 'Uploading artwork...';

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });

        progressBar.style.width = '70%';
        progressText.textContent = 'Processing...';

        const data = await response.json();

        progressBar.style.width = '100%';

        if (data.success) {
            if (isCsvMode) {
                showStatus(statusDiv, `Import complete!\n\nArtworks imported: ${data.imported || 0}${data.skipped ? `\nSkipped: ${data.skipped}` : ''}`, 'success');
                // Clear CSV file input
                const csvInput = document.getElementById('artworksCsvFile');
                csvInput.value = '';
                document.getElementById('artworksCsvFileName').textContent = 'Click to select CSV file';
                document.getElementById('artworksCsvFileName').parentElement.classList.remove('has-file');
            } else {
                showStatus(statusDiv, `Artwork uploaded successfully!\n\nArtist: ${data.artist}\nTitle: ${data.title}\nFile: ${data.filename}`, 'success');
                // Clear individual form
                form.reset();
                const imgInput = document.getElementById('artworkFile');
                imgInput.value = '';
                document.getElementById('artworkFileName').textContent = 'Click to select image file';
                document.getElementById('artworkFileName').parentElement.classList.remove('has-file');
            }
            progressDiv.style.display = 'none';
        } else {
            showStatus(statusDiv, `Upload failed\n\n${data.error}`, 'error');
            progressDiv.style.display = 'none';
        }
    } catch (error) {
        console.error('Upload error:', error);
        showStatus(statusDiv, `Upload failed\n\n${error.message}`, 'error');
        progressDiv.style.display = 'none';
    } finally {
        uploadBtn.disabled = false;
        cancelBtn.disabled = false;
    }
}
