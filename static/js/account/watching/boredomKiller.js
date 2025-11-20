/**
 * Boredom Killer Import
 * Handles multi-file CSV import for movies, documentaries, TV shows, and docuseries
 */

import { showStatus } from '../core/utilities.js';

/**
 * Submit Boredom Killer multi-file CSV import
 * Handles multiple file uploads with progress tracking
 */
export function submitBKImport() {
    const ratingsInput = document.getElementById('bkMoviesFile');
    const docsInput = document.getElementById('bkDocsFile');
    const tvInput = document.getElementById('bkTVFile');
    const docuseriesInput = document.getElementById('bkDocuseriesFile');
    const statusDiv = document.getElementById('bkStatus');
    const progressDiv = document.getElementById('bkProgress');
    const progressBar = document.getElementById('bkProgressBar');
    const progressText = document.getElementById('bkProgressText');
    const importBtn = document.getElementById('bkImportBtn');
    const cancelBtn = document.getElementById('bkCancelBtn');

    // Check if at least one file is selected
    const hasMovies = ratingsInput.files[0];
    const hasDocs = docsInput.files[0];
    const hasTV = tvInput.files[0];
    const hasDocuseries = docuseriesInput.files[0];

    if (!hasMovies && !hasDocs && !hasTV && !hasDocuseries) {
        showStatus(statusDiv, 'Please select at least one CSV file', 'error');
        return;
    }

    // Helper function to clear all file inputs
    const clearFileInputs = () => {
        const inputs = [
            { input: ratingsInput, label: 'bkMoviesFileName', default: 'Click to select Boredom Killer - Movies.csv' },
            { input: docsInput, label: 'bkDocsFileName', default: 'Click to select Boredom Killer - Documentaries.csv' },
            { input: tvInput, label: 'bkTVFileName', default: 'Click to select Boredom Killer - TV.csv' },
            { input: docuseriesInput, label: 'bkDocuseriesFileName', default: 'Click to select Boredom Killer - Docuseries.csv' }
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
    if (hasMovies) formData.append('movies_file', ratingsInput.files[0]);
    if (hasDocs) formData.append('docs_file', docsInput.files[0]);
    if (hasTV) formData.append('tv_file', tvInput.files[0]);
    if (hasDocuseries) formData.append('docuseries_file', docuseriesInput.files[0]);

    // Simulate progress updates
    progressText.textContent = 'Creating database backup...';
    progressBar.style.width = '10%';

    setTimeout(() => {
        progressText.textContent = 'Uploading files...';
        progressBar.style.width = '20%';
    }, 500);

    setTimeout(() => {
        progressText.textContent = 'Processing CSV data...';
        progressBar.style.width = '40%';
    }, 1500);

    setTimeout(() => {
        progressText.textContent = 'Importing to database...';
        progressBar.style.width = '60%';
    }, 3000);

    fetch('/account/import/boredom-killer', {
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
            const parts = ['Import complete!'];
            if (data.movies_added > 0) parts.push(`Movies added: ${data.movies_added}`);
            if (data.docs_added > 0) parts.push(`Documentaries added: ${data.docs_added}`);
            if (data.tv_added > 0) parts.push(`TV shows added: ${data.tv_added}`);
            if (data.docuseries_added > 0) parts.push(`Docuseries added: ${data.docuseries_added}`);
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
