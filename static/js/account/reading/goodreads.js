/**
 * Goodreads Import
 * Handles CSV import of Goodreads book data
 */

import { showStatus } from '../core/utilities.js';

/**
 * Submit Goodreads CSV import
 * Handles file upload, progress tracking, and result display
 */
export function submitGoodreadsImport() {
    const form = document.getElementById('goodreadsForm');
    const fileInput = document.getElementById('goodreadsFile');
    const statusDiv = document.getElementById('goodreadsStatus');
    const progressDiv = document.getElementById('goodreadsProgress');
    const progressBar = document.getElementById('goodreadsProgressBar');
    const progressText = document.getElementById('goodreadsProgressText');
    const importBtn = document.getElementById('goodreadsImportBtn');
    const cancelBtn = document.getElementById('goodreadsCancelBtn');

    if (!fileInput.files[0]) {
        showStatus(statusDiv, 'Please select a file', 'error');
        return;
    }

    // Helper function to clear file input
    const clearFileInput = () => {
        fileInput.value = '';
        const fileNameSpan = document.getElementById('goodreadsFileName');
        const dropZone = fileNameSpan.parentElement;
        fileNameSpan.textContent = 'Click to select CSV file or drag and drop';
        dropZone.classList.remove('has-file');
    };

    // Disable buttons during import
    importBtn.disabled = true;
    importBtn.style.opacity = '0.5';
    importBtn.style.cursor = 'not-allowed';

    // Show progress bar
    progressDiv.style.display = 'block';
    statusDiv.innerHTML = '';

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    // Simulate progress updates (since we can't get real progress from subprocess)
    progressText.textContent = 'Creating database backup...';
    progressBar.style.width = '10%';

    setTimeout(() => {
        progressText.textContent = 'Uploading file...';
        progressBar.style.width = '20%';
    }, 500);

    setTimeout(() => {
        progressText.textContent = 'Processing CSV data...';
        progressBar.style.width = '40%';
    }, 1500);

    setTimeout(() => {
        progressText.textContent = 'Importing books to database...';
        progressBar.style.width = '60%';
    }, 3000);

    fetch('/account/import/goodreads', {
        method: 'POST',
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
            let message = `Import complete! Added: ${data.added}, Updated: ${data.updated}, Conflicts: ${data.conflicts}`;

            if (data.conflicts > 0 && data.report_url) {
                message += ' Conflict report downloaded.';
            }

            showStatus(statusDiv, message, 'success');

            // Download conflict report if available
            if (data.report_url) {
                window.location.href = data.report_url;
            }

            // Clear file input
            clearFileInput();
        } else {
            // Clean up error message - remove leading/trailing whitespace and newlines
            const cleanError = (data.error || 'Import failed').trim().replace(/^\n+/, '');
            const errorMsg = data.rolled_back
                ? `${cleanError} (Database was automatically rolled back to previous state.)`
                : cleanError;
            showStatus(statusDiv, errorMsg, 'error');

            // Hide progress bar on error
            setTimeout(() => {
                progressDiv.style.display = 'none';
            }, 2000);

            // Clear file input
            clearFileInput();
        }
    })
    .catch(error => {
        console.error('Error:', error);

        // Re-enable buttons
        importBtn.disabled = false;
        importBtn.style.opacity = '1';
        importBtn.style.cursor = 'pointer';

        showStatus(statusDiv, 'An error occurred during import', 'error');

        // Hide progress bar on error
        setTimeout(() => {
            progressDiv.style.display = 'none';
        }, 2000);

        // Clear file input
        clearFileInput();
    });
}
