/**
 * Account Page Main Entry Point
 * Imports all modules and exposes functions globally for inline onclick handlers
 */

// Core modules
import * as modals from './core/modals.js';
import { initializeFileInputHandlers } from './core/fileInputHandlers.js';

// Reading modules
import { submitGoodreadsImport } from './reading/goodreads.js';

// Watching modules
import { submitBKImport } from './watching/boredomKiller.js';
import { submitLetterboxdImport } from './watching/letterboxd.js';

// Listening modules
import { submitSpotifyRefresh } from './listening/spotify.js';

// Pondering modules
import { switchUploadMode, submitArtworkUpload } from './pondering/artworkManager.js';

// Writing modules
import {
    initializePublications,
    switchPublicationTab,
    addAuthor,
    removeAuthor,
    moveAuthorUp,
    moveAuthorDown,
    savePublication,
    editPublication,
    deletePublication
} from './writing/publicationManager.js';

/**
 * Initialize all account page functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize core functionality
    modals.initializeModals();
    initializeFileInputHandlers();

    // Initialize publications
    initializePublications();
});

/**
 * Expose functions to global scope for inline onclick handlers
 * This allows HTML onclick attributes to work with our modular code
 */
window.account = {
    // Modal functions
    openModal: modals.openModal,
    closeModal: modals.closeModal,

    // Reading functions
    submitGoodreadsImport,

    // Watching functions
    submitBKImport,
    submitLetterboxdImport,

    // Listening functions
    submitSpotifyRefresh,

    // Pondering functions
    switchUploadMode,
    submitArtworkUpload,

    // Writing functions
    switchPublicationTab,
    addAuthor,
    removeAuthor,
    moveAuthorUp,
    moveAuthorDown,
    savePublication,
    editPublication,
    deletePublication
};

// For backward compatibility, also expose functions directly on window
// This allows onclick="functionName()" to work
Object.assign(window, window.account);
