/**
 * Account Page JavaScript
 * Handles modals, imports, and admin tools
 */

// Modal management
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Close modal on overlay click
document.addEventListener('DOMContentLoaded', function() {
    const overlays = document.querySelectorAll('.modal-overlay');
    overlays.forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                closeModal(overlay.id);
            }
        });
    });

    // Close modal on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal-overlay.active');
            if (activeModal) {
                closeModal(activeModal.id);
            }
        }
    });

    // File input handling for Goodreads
    const goodreadsFileInput = document.getElementById('goodreadsFile');
    if (goodreadsFileInput) {
        goodreadsFileInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name || 'Click to select CSV file or drag and drop';
            const fileNameSpan = document.getElementById('goodreadsFileName');
            const dropZone = fileNameSpan.parentElement;

            if (e.target.files[0]) {
                fileNameSpan.textContent = fileName;
                dropZone.classList.add('has-file');
            } else {
                fileNameSpan.textContent = 'Click to select CSV file or drag and drop';
                dropZone.classList.remove('has-file');
            }
        });
    }

    // File input handlers for Boredom Killer
    const bkFileInputs = [
        { input: 'bkMoviesFile', label: 'bkMoviesFileName', default: 'Click to select Boredom Killer - Movies.csv' },
        { input: 'bkDocsFile', label: 'bkDocsFileName', default: 'Click to select Boredom Killer - Documentaries.csv' },
        { input: 'bkTVFile', label: 'bkTVFileName', default: 'Click to select Boredom Killer - TV.csv' },
        { input: 'bkDocuseriesFile', label: 'bkDocuseriesFileName', default: 'Click to select Boredom Killer - Docuseries.csv' }
    ];

    bkFileInputs.forEach(item => {
        const fileInput = document.getElementById(item.input);
        if (fileInput) {
            fileInput.addEventListener('change', function(e) {
                const fileName = e.target.files[0]?.name || item.default;
                const fileNameSpan = document.getElementById(item.label);
                const dropZone = fileNameSpan.parentElement;

                if (e.target.files[0]) {
                    fileNameSpan.textContent = fileName;
                    dropZone.classList.add('has-file');
                } else {
                    fileNameSpan.textContent = item.default;
                    dropZone.classList.remove('has-file');
                }
            });
        }
    });

    // File input handlers for Letterboxd
    const letterboxdRatingsInput = document.getElementById('letterboxdRatingsFile');
    if (letterboxdRatingsInput) {
        letterboxdRatingsInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name || 'Click to select ratings.csv';
            const fileNameSpan = document.getElementById('letterboxdRatingsFileName');
            const dropZone = fileNameSpan.parentElement;

            if (e.target.files[0]) {
                fileNameSpan.textContent = fileName;
                dropZone.classList.add('has-file');
            } else {
                fileNameSpan.textContent = 'Click to select ratings.csv';
                dropZone.classList.remove('has-file');
            }
        });
    }

    const letterboxdReviewsInput = document.getElementById('letterboxdReviewsFile');
    if (letterboxdReviewsInput) {
        letterboxdReviewsInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name || 'Click to select reviews.csv';
            const fileNameSpan = document.getElementById('letterboxdReviewsFileName');
            const dropZone = fileNameSpan.parentElement;

            if (e.target.files[0]) {
                fileNameSpan.textContent = fileName;
                dropZone.classList.add('has-file');
            } else {
                fileNameSpan.textContent = 'Click to select reviews.csv';
                dropZone.classList.remove('has-file');
            }
        });
    }
});

// Goodreads Import
function submitGoodreadsImport() {
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

// Boredom Killer Import
function submitBKImport() {
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

// Letterboxd Import
function submitLetterboxdImport() {
    const ratingsInput = document.getElementById('letterboxdRatingsFile');
    const reviewsInput = document.getElementById('letterboxdReviewsFile');
    const statusDiv = document.getElementById('letterboxdStatus');
    const progressDiv = document.getElementById('letterboxdProgress');
    const progressBar = document.getElementById('letterboxdProgressBar');
    const progressText = document.getElementById('letterboxdProgressText');
    const importBtn = document.getElementById('letterboxdImportBtn');
    const cancelBtn = document.getElementById('letterboxdCancelBtn');

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

// TV Shows Import
function submitShowsImport() {
    const fileInput = document.getElementById('showsFile');
    const statusDiv = document.getElementById('showsStatus');

    if (!fileInput.files[0]) {
        showStatus(statusDiv, 'Please select a file', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    showStatus(statusDiv, 'Uploading and processing...', 'loading');

    fetch('/account/import/shows', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            let message = `Import complete!\nAdded: ${data.added}\nUpdated: ${data.updated}\nConflicts: ${data.conflicts}`;
            showStatus(statusDiv, message, 'success');

            setTimeout(() => {
                closeModal('showsModal');
                location.reload();
            }, 3000);
        } else {
            showStatus(statusDiv, data.error || 'Import failed', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showStatus(statusDiv, 'An error occurred during import', 'error');
    });
}

// Spotify Refresh
function submitSpotifyRefresh() {
    const statusDiv = document.getElementById('spotifyStatus');

    showStatus(statusDiv, 'Refreshing Spotify playlists...', 'loading');

    fetch('/account/refresh/spotify', {
        method: 'POST'
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

// Upload mode switcher for artwork modal
function switchUploadMode(mode) {
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

// Artwork upload handler
async function submitArtworkUpload() {
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

// File input display handler for individual artwork
document.getElementById('artworkFile')?.addEventListener('change', function() {
    const fileName = this.files[0]?.name || 'Click to select image file';
    document.getElementById('artworkFileName').textContent = fileName;
    if (this.files.length > 0) {
        document.getElementById('artworkFileName').parentElement.classList.add('has-file');
    }
});

// File input display handler for CSV artwork import
document.getElementById('artworksCsvFile')?.addEventListener('change', function() {
    const fileName = this.files[0]?.name || 'Click to select CSV file';
    document.getElementById('artworksCsvFileName').textContent = fileName;
    if (this.files.length > 0) {
        document.getElementById('artworksCsvFileName').parentElement.classList.add('has-file');
    }
});

// Helper function to show status messages
function showStatus(element, message, type) {
    const colors = {
        'loading': 'var(--accent-blue)',
        'success': '#86efac',
        'error': '#fca5a5'
    };

    element.innerHTML = `<div style="padding: var(--space-3); background: rgba(${type === 'success' ? '34, 197, 94' : type === 'error' ? '239, 68, 68' : '88, 166, 255'}, 0.1); border: 1px solid ${colors[type]}; border-radius: var(--radius-base); color: ${colors[type]}; white-space: pre-line; margin-top: var(--space-4);">${message}</div>`;
}

// ========================================
// Publications Management Functions
// ========================================

const PUBLICATION_CATEGORIES = {
    academic: [
        { value: 'journal_article', label: 'Journal Article' },
        { value: 'conference_talk', label: 'Conference Talk' },
        { value: 'editor', label: 'Editor' }
    ],
    creative: [
        { value: 'fiction', label: 'Fiction' },
        { value: 'essay', label: 'Essay' },
        { value: 'poetry', label: 'Poetry' }
    ]
};

// Global array to track authors
let publicationAuthors = [];

// Update category options when section changes
document.addEventListener('DOMContentLoaded', function() {
    const sectionSelect = document.getElementById('publicationSection');
    if (sectionSelect) {
        sectionSelect.addEventListener('change', function() {
            updatePublicationCategoryOptions(this.value);
        });
        // Initialize on page load
        updatePublicationCategoryOptions(sectionSelect.value);
    }

    // Allow pressing Enter to add author
    const newAuthorInput = document.getElementById('newAuthorName');
    if (newAuthorInput) {
        newAuthorInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addAuthor();
            }
        });
    }
});

function updatePublicationCategoryOptions(section) {
    const categorySelect = document.getElementById('publicationCategory');
    if (!categorySelect) return;

    categorySelect.innerHTML = '<option value="">Select category...</option>';

    PUBLICATION_CATEGORIES[section].forEach(cat => {
        const option = document.createElement('option');
        option.value = cat.value;
        option.textContent = cat.label;
        categorySelect.appendChild(option);
    });
}

function switchPublicationTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.review-tab').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });

    if (tabName === 'addPublication') {
        document.getElementById('addPublicationTab').classList.add('active');
        document.getElementById('savePublicationBtn').style.display = 'inline-block';
    } else if (tabName === 'viewPublications') {
        document.getElementById('viewPublicationsTab').classList.add('active');
        document.getElementById('savePublicationBtn').style.display = 'none';
        loadPublications();
    }
}

function addAuthor() {
    const nameInput = document.getElementById('newAuthorName');
    const isYouCheckbox = document.getElementById('newAuthorIsYou');

    const name = nameInput.value.trim();
    if (!name) return;

    publicationAuthors.push({
        name: name,
        is_you: isYouCheckbox.checked
    });

    // Clear inputs
    nameInput.value = '';
    isYouCheckbox.checked = false;

    renderAuthorsList();
}

function removeAuthor(index) {
    publicationAuthors.splice(index, 1);
    renderAuthorsList();
}

function moveAuthorUp(index) {
    if (index === 0) return;
    const temp = publicationAuthors[index];
    publicationAuthors[index] = publicationAuthors[index - 1];
    publicationAuthors[index - 1] = temp;
    renderAuthorsList();
}

function moveAuthorDown(index) {
    if (index === publicationAuthors.length - 1) return;
    const temp = publicationAuthors[index];
    publicationAuthors[index] = publicationAuthors[index + 1];
    publicationAuthors[index + 1] = temp;
    renderAuthorsList();
}

function renderAuthorsList() {
    const container = document.getElementById('authorsList');
    if (!container) return;

    if (publicationAuthors.length === 0) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = publicationAuthors.map((author, index) => `
        <div class="author-item">
            <span class="author-drag-handle">
                ${index > 0 ? `<span onclick="moveAuthorUp(${index})" style="cursor: pointer;">↑</span>` : '<span style="opacity: 0.3;">↑</span>'}
                ${index < publicationAuthors.length - 1 ? `<span onclick="moveAuthorDown(${index})" style="cursor: pointer;">↓</span>` : '<span style="opacity: 0.3;">↓</span>'}
            </span>
            <span class="author-name">${author.name}</span>
            ${author.is_you ? '<span class="author-badge">Me</span>' : ''}
            <span class="author-remove" onclick="removeAuthor(${index})">×</span>
        </div>
    `).join('');
}

async function loadPublications() {
    const listContainer = document.getElementById('publicationsList');
    listContainer.innerHTML = '<p>Loading publications...</p>';

    try {
        const response = await fetch('/writing/publications/all');
        const result = await response.json();

        if (!result.success || result.publications.length === 0) {
            listContainer.innerHTML = '<p>No publications found. Add some using the form above!</p>';
            return;
        }

        const pubs = result.publications;

        // Group by section
        const academic = pubs.filter(p => p.section === 'academic');
        const creative = pubs.filter(p => p.section === 'creative');

        let html = '<div style="max-height: 500px; overflow-y: auto; padding: var(--space-2);">';

        // Academic publications
        if (academic.length > 0) {
            html += '<h4 style="margin-bottom: var(--space-3); color: var(--text-secondary);">Academic Publications</h4>';
            html += '<div class="publications-sortable" data-section="academic">';
            academic.forEach(pub => {
                html += renderPublicationItem(pub);
            });
            html += '</div>';
        }

        // Creative publications
        if (creative.length > 0) {
            html += '<h4 style="margin-top: var(--space-4); margin-bottom: var(--space-3); color: var(--text-secondary);">Creative Publications</h4>';
            html += '<div class="publications-sortable" data-section="creative">';
            creative.forEach(pub => {
                html += renderPublicationItem(pub);
            });
            html += '</div>';
        }

        html += '</div>';
        html += '<div style="margin-top: var(--space-3); padding: var(--space-3); background: var(--bg-tertiary); border-radius: var(--radius-base); text-align: center;">';
        html += '<small style="color: var(--text-secondary);">Drag publications to reorder them within their section. Changes save automatically.</small>';
        html += '</div>';

        listContainer.innerHTML = html;

        // Initialize drag-and-drop
        initPublicationsDragDrop();

    } catch (error) {
        listContainer.innerHTML = `<p style="color: var(--text-error);">Error loading publications: ${error.message}</p>`;
    }
}

function renderPublicationItem(pub) {
    const authorsText = pub.authors.map(a => a.is_you ? `<strong>${a.name}</strong>` : a.name).join(', ');

    return `
        <div class="pub-management-item" data-pub-id="${pub.id}" draggable="true">
            <span class="pub-drag-handle">⋮⋮</span>
            <div class="pub-info">
                <div class="pub-title">${pub.title}</div>
                <div class="pub-meta">${authorsText} • ${pub.venue}</div>
            </div>
            <div class="pub-actions">
                <button class="btn-icon" onclick="editPublication('${pub.id}')" title="Edit">✎</button>
                <button class="btn-icon" onclick="deletePublication('${pub.id}')" title="Delete">×</button>
            </div>
        </div>
    `;
}

function initPublicationsDragDrop() {
    const containers = document.querySelectorAll('.publications-sortable');

    containers.forEach(container => {
        let draggedElement = null;

        container.addEventListener('dragstart', function(e) {
            if (e.target.classList.contains('pub-management-item')) {
                draggedElement = e.target;
                e.target.style.opacity = '0.5';
            }
        });

        container.addEventListener('dragend', function(e) {
            if (e.target.classList.contains('pub-management-item')) {
                e.target.style.opacity = '';
                draggedElement = null;
            }
        });

        container.addEventListener('dragover', function(e) {
            e.preventDefault();
            const afterElement = getDragAfterElement(container, e.clientY);
            if (afterElement == null) {
                container.appendChild(draggedElement);
            } else {
                container.insertBefore(draggedElement, afterElement);
            }
        });

        container.addEventListener('drop', function(e) {
            e.preventDefault();
            savePublicationsOrder(container);
        });
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.pub-management-item:not(.dragging)')];

    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;

        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

async function savePublicationsOrder(container) {
    const pubElements = container.querySelectorAll('.pub-management-item');
    const publicationIds = Array.from(pubElements).map(el => el.dataset.pubId);

    try {
        const response = await fetch('/writing/publications/reorder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ publication_ids: publicationIds })
        });

        const result = await response.json();

        if (!result.success) {
            console.error('Error saving order:', result.error);
        }
    } catch (error) {
        console.error('Error saving order:', error.message);
    }
}

async function savePublication() {
    const id = document.getElementById('publicationId').value;
    const section = document.getElementById('publicationSection').value;
    const statusDiv = document.getElementById('publicationStatus');

    // Validate authors
    if (publicationAuthors.length === 0) {
        showStatus(statusDiv, 'Please add at least one author', 'error');
        return;
    }

    const data = {
        title: document.getElementById('publicationTitle').value,
        authors: publicationAuthors,  // Send authors array
        venue: document.getElementById('publicationVenue').value,
        publication_date: document.getElementById('publicationDate').value,
        category: document.getElementById('publicationCategory').value,
        section: section,
        url: document.getElementById('publicationUrl').value || null,
        doi: document.getElementById('publicationDoi').value || null,
        pmid: document.getElementById('publicationPmid').value || null,
        volume_issue: document.getElementById('publicationVolumeIssue').value || null,
        badge: document.getElementById('publicationBadge').value || null,
        display_order: 0  // Will be set via drag-and-drop in View All tab
    };

    const url = id ? `/writing/update/${id}` : '/writing/create';

    try {
        showStatus(statusDiv, 'Saving publication...', 'loading');

        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showStatus(statusDiv, id ? 'Publication updated successfully!' : 'Publication created successfully!', 'success');

            // Reset form after a delay
            setTimeout(() => {
                document.getElementById('publicationForm').reset();
                document.getElementById('publicationId').value = '';
                publicationAuthors = [];
                renderAuthorsList();
                statusDiv.innerHTML = '';
            }, 2000);
        } else {
            showStatus(statusDiv, 'Error: ' + result.error, 'error');
        }
    } catch (error) {
        showStatus(statusDiv, 'Error saving publication: ' + error.message, 'error');
    }
}

async function editPublication(publicationId) {
    const statusDiv = document.getElementById('publicationStatus');

    try {
        const response = await fetch(`/writing/get/${publicationId}`);
        const result = await response.json();

        if (result.success) {
            const pub = result.publication;

            // Switch to add tab
            switchPublicationTab('addPublication');

            // Clear any status messages
            statusDiv.innerHTML = '';

            // Populate form
            document.getElementById('publicationId').value = pub.id;
            document.getElementById('publicationTitle').value = pub.title;
            document.getElementById('publicationVenue').value = pub.venue;
            document.getElementById('publicationDate').value = pub.publication_date;
            document.getElementById('publicationUrl').value = pub.url || '';
            document.getElementById('publicationDoi').value = pub.doi || '';
            document.getElementById('publicationPmid').value = pub.pmid || '';
            document.getElementById('publicationVolumeIssue').value = pub.volume_issue || '';
            document.getElementById('publicationBadge').value = pub.badge || '';
            document.getElementById('publicationSection').value = pub.section;

            updatePublicationCategoryOptions(pub.section);
            document.getElementById('publicationCategory').value = pub.category;

            // Load authors
            publicationAuthors = pub.authors || [];
            renderAuthorsList();

            // Open modal
            openModal('managePublicationsModal');
        }
    } catch (error) {
        showStatus(statusDiv, 'Error loading publication: ' + error.message, 'error');
    }
}

async function deletePublication(publicationId) {
    if (!confirm('Are you sure you want to delete this publication?')) {
        return;
    }

    try {
        const response = await fetch(`/writing/delete/${publicationId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            // Reload the publications list
            loadPublications();
        } else {
            console.error('Error deleting publication:', result.error);
        }
    } catch (error) {
        console.error('Error deleting publication:', error.message);
    }
}
