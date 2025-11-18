/**
 * Letterboxd Import
 * Handles Letterboxd ratings and reviews CSV import
 */

import { showStatus } from '../core/utilities.js';

/**
 * Submit Letterboxd CSV import
 * Handles ratings and reviews file upload with optional data reset
 */
export function submitLetterboxdImport() {
    const ratingsInput = document.getElementById('letterboxdRatingsFile');
    const reviewsInput = document.getElementById('letterboxdReviewsFile');
    const statusDiv = document.getElementById('letterboxdStatus');
    const progressDiv = document.getElementById('letterboxdProgress');
    const progressBar = document.getElementById('letterboxdProgressBar');
    const progressText = document.getElementById('letterboxdProgressText');
    const importBtn = document.getElementById('letterboxdImportBtn');

    if (!ratingsInput.files[0] || !reviewsInput.files[0]) {
        showStatus(statusDiv, 'Please select both ratings.csv and reviews.csv', 'error');
        return;
    }

    // Helper function to clear file inputs
    const clearFileInputs = () => {
        const inputs = [
            { input: ratingsInput, label: 'letterboxdRatingsFileName', default: 'Click to select ratings.csv' },
            { input: reviewsInput, label: 'letterboxdReviewsFileName', default: 'Click to select reviews.csv' }
        ];

        inputs.forEach(item => {
            item.input.value = '';
            const fileNameSpan = document.getElementById(item.label);
            const dropZone = fileNameSpan.parentElement;
            fileNameSpan.textContent = item.default;
            dropZone.classList.remove('has-file');
        });
    };

    // Disable buttons during import
    importBtn.disabled = true;
    importBtn.style.opacity = '0.5';
    importBtn.style.cursor = 'not-allowed';

    // Show progress bar
    progressDiv.style.display = 'block';
    statusDiv.innerHTML = '';

    const formData = new FormData();
    formData.append('ratings_file', ratingsInput.files[0]);
    formData.append('reviews_file', reviewsInput.files[0]);

    // Add reset flag if checkbox is checked
    const resetCheckbox = document.getElementById('letterboxdResetData');
    if (resetCheckbox && resetCheckbox.checked) {
        formData.append('reset_data', 'true');
    }

    // Simulate progress updates
    progressText.textContent = 'Creating database backup...';
    progressBar.style.width = '10%';

    setTimeout(() => {
        progressText.textContent = 'Uploading files...';
        progressBar.style.width = '20%';
    }, 500);

    setTimeout(() => {
        progressText.textContent = 'Processing ratings and reviews...';
        progressBar.style.width = '40%';
    }, 1500);

    setTimeout(() => {
        progressText.textContent = 'Importing to database...';
        progressBar.style.width = '60%';
    }, 3000);

    fetch('/account/import/letterboxd', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Complete progress bar
        progressBar.style.width = '100%';
        progressText.textContent = 'Import complete!';

        // Re-enable buttons
        importBtn.disabled = false;
        importBtn.style.opacity = '1';
        importBtn.style.cursor = 'pointer';

        if (data.success) {
            const parts = [
                'Import complete!',
                `Ratings imported: ${data.ratings_imported || 0}`,
                `Reviews imported: ${data.reviews_imported || 0}`
            ];
            const message = parts.join('\n');
            showStatus(statusDiv, message, 'success');

            // Clear file inputs
            clearFileInputs();
        } else {
            const cleanError = (data.error || 'Import failed').trim().replace(/^\n+/, '');
            const errorMsg = data.rolled_back
                ? `${cleanError} (Database was automatically rolled back to previous state.)`
                : cleanError;
            showStatus(statusDiv, errorMsg, 'error');

            setTimeout(() => {
                progressDiv.style.display = 'none';
            }, 2000);

            // Clear file inputs
            clearFileInputs();
        }
    })
    .catch(error => {
        console.error('Error:', error);

        // Re-enable buttons
        importBtn.disabled = false;
        importBtn.style.opacity = '1';
        importBtn.style.cursor = 'pointer';

        showStatus(statusDiv, 'An error occurred during import', 'error');

        setTimeout(() => {
            progressDiv.style.display = 'none';
        }, 2000);

        // Clear file inputs
        clearFileInputs();
    });
}
