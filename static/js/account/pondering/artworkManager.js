/**
 * Artwork Manager
 * Handles artwork uploads (both individual and CSV bulk import)
 */

import { showStatus } from '../core/utilities.js';

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
