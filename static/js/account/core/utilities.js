/**
 * Core Utility Functions
 * Shared helper functions used across account modules
 */

/**
 * Display status messages with appropriate styling
 * @param {HTMLElement} element - Container element for the status message
 * @param {string} message - Message to display
 * @param {string} type - Type of message: 'loading', 'success', or 'error'
 */
export function showStatus(element, message, type) {
    const colors = {
        'loading': 'var(--accent-blue)',
        'success': '#86efac',
        'error': '#fca5a5'
    };

    element.innerHTML = `<div style="padding: var(--space-3); background: rgba(${type === 'success' ? '34, 197, 94' : type === 'error' ? '239, 68, 68' : '88, 166, 255'}, 0.1); border: 1px solid ${colors[type]}; border-radius: var(--radius-base); color: ${colors[type]}; white-space: pre-line; margin-top: var(--space-4);">${message}</div>`;
}
