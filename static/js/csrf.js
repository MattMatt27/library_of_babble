/**
 * CSRF Token Utility
 *
 * Provides helper functions for including CSRF tokens in AJAX requests.
 */

/**
 * Get CSRF token from meta tag in page head
 * @returns {string} CSRF token value
 */
function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : '';
}

/**
 * Get headers object with CSRF token for fetch requests
 * @param {Object} additionalHeaders - Optional additional headers to include
 * @returns {Object} Headers object with CSRF token
 */
function getCSRFHeaders(additionalHeaders = {}) {
    return {
        'X-CSRFToken': getCSRFToken(),
        ...additionalHeaders
    };
}

/**
 * Make a POST request with CSRF token
 * @param {string} url - The URL to POST to
 * @param {Object} data - Data to send (will be JSON stringified)
 * @param {Object} options - Additional fetch options
 * @returns {Promise} Fetch promise
 */
function postWithCSRF(url, data = {}, options = {}) {
    return fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...getCSRFHeaders()
        },
        body: JSON.stringify(data),
        ...options
    });
}

/**
 * Submit FormData with CSRF token
 * @param {string} url - The URL to POST to
 * @param {FormData} formData - FormData object to submit
 * @param {Object} options - Additional fetch options
 * @returns {Promise} Fetch promise
 */
function postFormDataWithCSRF(url, formData, options = {}) {
    // Note: Don't set Content-Type header for FormData, browser will set it with boundary
    return fetch(url, {
        method: 'POST',
        headers: getCSRFHeaders(),
        body: formData,
        ...options
    });
}
