/**
 * File Input Handlers
 * Manages file input UI updates for drag-and-drop zones
 */

/**
 * Initialize all file input handlers
 * Sets up change event listeners for file upload UI feedback
 */
export function initializeFileInputHandlers() {
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

    // Individual artwork file handler
    const artworkFileInput = document.getElementById('artworkFile');
    if (artworkFileInput) {
        artworkFileInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name || 'Click to select image file or drag and drop';
            document.getElementById('artworkFileName').textContent = fileName;
        });
    }

    // CSV artwork file handler
    const artworkCSVInput = document.getElementById('artworkCSVFile');
    if (artworkCSVInput) {
        artworkCSVInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name || 'Click to select CSV file or drag and drop';
            document.getElementById('artworkCSVFileName').textContent = fileName;
        });
    }
}
