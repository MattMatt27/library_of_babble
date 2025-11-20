/**
 * Star Rating Component
 *
 * Provides interactive star rating functionality for movies and books
 */

// Star SVG template
const STAR_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="star-empty">
  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
</svg>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="star-filled">
  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
</svg>
`;

/**
 * Create a star rating component
 * @param {number} rating - Current rating (0-5, can be 0.5 increments)
 * @param {boolean} interactive - Whether stars are clickable
 * @param {string} size - Size class: 'small', 'large', or default
 * @param {Function} onChange - Callback when rating changes (rating) => void
 * @returns {HTMLElement} The star rating element
 */
function createStarRating(rating = 0, interactive = false, size = '', onChange = null) {
  const container = document.createElement('div');
  container.className = `star-rating ${interactive ? 'interactive' : ''} ${size}`;
  container.setAttribute('data-rating', rating);

  // Create 5 stars
  for (let i = 1; i <= 5; i++) {
    const star = document.createElement('span');
    star.className = 'star';
    star.setAttribute('data-star-index', i);
    star.innerHTML = STAR_SVG;

    // Add half-star click zones for interactive mode
    if (interactive) {
      const leftZone = document.createElement('span');
      leftZone.className = 'star-half-left';
      leftZone.setAttribute('data-value', i - 0.5);

      const rightZone = document.createElement('span');
      rightZone.className = 'star-half-right';
      rightZone.setAttribute('data-value', i);

      star.appendChild(leftZone);
      star.appendChild(rightZone);

      // Click handlers
      leftZone.addEventListener('click', (e) => {
        e.stopPropagation();
        const newRating = parseFloat(leftZone.getAttribute('data-value'));
        updateStarDisplay(container, newRating);
        if (onChange) onChange(newRating);
      });

      rightZone.addEventListener('click', (e) => {
        e.stopPropagation();
        const newRating = parseFloat(rightZone.getAttribute('data-value'));
        updateStarDisplay(container, newRating);
        if (onChange) onChange(newRating);
      });

      // Hover effects
      star.addEventListener('mouseenter', function() {
        const starIndex = parseInt(this.getAttribute('data-star-index'));
        highlightStars(container, starIndex);
      });

      leftZone.addEventListener('mouseenter', function(e) {
        e.stopPropagation();
        const value = parseFloat(this.getAttribute('data-value'));
        highlightStars(container, value);
      });

      rightZone.addEventListener('mouseenter', function(e) {
        e.stopPropagation();
        const value = parseFloat(this.getAttribute('data-value'));
        highlightStars(container, value);
      });

      container.addEventListener('mouseleave', function() {
        const currentRating = parseFloat(this.getAttribute('data-rating'));
        updateStarDisplay(container, currentRating);
      });
    }

    container.appendChild(star);
  }

  // Set initial display
  updateStarDisplay(container, rating);

  return container;
}

/**
 * Update the visual display of stars based on rating
 * @param {HTMLElement} container - The star rating container
 * @param {number} rating - The rating to display
 */
function updateStarDisplay(container, rating) {
  container.setAttribute('data-rating', rating);
  const stars = container.querySelectorAll('.star');

  stars.forEach((star, index) => {
    const starValue = index + 1;
    star.classList.remove('empty', 'half', 'full', 'hover');

    if (rating >= starValue) {
      star.classList.add('full');
    } else if (rating >= starValue - 0.5) {
      star.classList.add('half');
    } else {
      star.classList.add('empty');
    }
  });
}

/**
 * Highlight stars on hover
 * @param {HTMLElement} container - The star rating container
 * @param {number} value - The value to highlight up to
 */
function highlightStars(container, value) {
  const stars = container.querySelectorAll('.star');

  stars.forEach((star, index) => {
    const starValue = index + 1;
    star.classList.remove('empty', 'half', 'full', 'hover');

    if (value >= starValue) {
      star.classList.add('full', 'hover');
    } else if (value >= starValue - 0.5) {
      star.classList.add('half', 'hover');
    } else {
      star.classList.add('empty');
    }
  });
}

/**
 * Initialize star ratings on the page
 * Looks for elements with data-star-rating attribute
 */
function initializeStarRatings() {
  document.querySelectorAll('[data-star-rating]').forEach(element => {
    const rating = parseFloat(element.getAttribute('data-star-rating')) || 0;
    const interactive = element.hasAttribute('data-interactive');
    const size = element.getAttribute('data-size') || '';
    const itemType = element.getAttribute('data-item-type');
    const itemId = element.getAttribute('data-item-id');

    // Create star rating component
    const starRating = createStarRating(rating, interactive, size, (newRating) => {
      // Handle rating change
      if (interactive && itemType && itemId) {
        updateRating(itemType, itemId, newRating);
      }
    });

    // Replace the placeholder element
    element.replaceWith(starRating);
  });
}

/**
 * Update rating via AJAX
 * @param {string} itemType - 'movie' or 'book'
 * @param {string} itemId - The item ID
 * @param {number} rating - The new rating
 */
async function updateRating(itemType, itemId, rating) {
  try {
    const endpoint = itemType === 'movie'
      ? `/movies/update_rating/${itemId}`
      : `/books/update_rating/${itemId}`;

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      },
      body: JSON.stringify({ rating: rating })
    });

    if (!response.ok) {
      throw new Error('Failed to update rating');
    }

    const data = await response.json();
    console.log(`Rating updated successfully: ${rating} stars`);

    // Optional: Show a success message
    // You could add a toast notification here

  } catch (error) {
    console.error('Error updating rating:', error);
    alert('Failed to update rating. Please try again.');
  }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeStarRatings);
} else {
  initializeStarRatings();
}

// Export for use in other scripts
window.StarRating = {
  create: createStarRating,
  initialize: initializeStarRatings,
  updateDisplay: updateStarDisplay
};
