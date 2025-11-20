/**
 * Publication Manager
 * Handles CRUD operations for academic and creative publications
 */

import { showStatus } from '../core/utilities.js';
import { openModal } from '../core/modals.js';

// Publication categories by section
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

// Global array to track authors for current publication
let publicationAuthors = [];

/**
 * Initialize publication management event listeners
 */
export function initializePublications() {
    // Update category options when section changes
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
}

/**
 * Update category dropdown options based on selected section
 */
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

/**
 * Switch between Add Publication and View All tabs
 */
export function switchPublicationTab(tabName) {
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

/**
 * Add author to the publication authors list
 */
export function addAuthor() {
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

/**
 * Remove author from the list
 */
export function removeAuthor(index) {
    publicationAuthors.splice(index, 1);
    renderAuthorsList();
}

/**
 * Move author up in the order
 */
export function moveAuthorUp(index) {
    if (index === 0) return;
    const temp = publicationAuthors[index];
    publicationAuthors[index] = publicationAuthors[index - 1];
    publicationAuthors[index - 1] = temp;
    renderAuthorsList();
}

/**
 * Move author down in the order
 */
export function moveAuthorDown(index) {
    if (index === publicationAuthors.length - 1) return;
    const temp = publicationAuthors[index];
    publicationAuthors[index] = publicationAuthors[index + 1];
    publicationAuthors[index + 1] = temp;
    renderAuthorsList();
}

/**
 * Render the authors list UI
 */
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

/**
 * Load all publications for management view
 */
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

        // Define category order and labels
        const ACADEMIC_CATEGORY_ORDER = ['journal_article', 'conference_talk', 'editor'];
        const CREATIVE_CATEGORY_ORDER = ['fiction', 'essay', 'poetry'];
        const CATEGORY_LABELS = {
            'journal_article': 'Journal Articles',
            'conference_talk': 'Conference Talks',
            'editor': 'Editor',
            'fiction': 'Fiction',
            'essay': 'Essays',
            'poetry': 'Poetry'
        };

        // Group by section and category
        const academic = pubs.filter(p => p.section === 'academic');
        const creative = pubs.filter(p => p.section === 'creative');

        let html = '<div style="max-height: 500px; overflow-y: auto; padding: var(--space-2);">';

        // Academic publications - grouped by category
        if (academic.length > 0) {
            html += '<h4 style="margin-bottom: var(--space-3); color: var(--text-secondary);">Academic Publications</h4>';

            ACADEMIC_CATEGORY_ORDER.forEach(category => {
                const categoryPubs = academic.filter(p => p.category === category);
                if (categoryPubs.length > 0) {
                    html += `<h5 style="margin-top: var(--space-3); margin-bottom: var(--space-2); color: var(--text-tertiary); font-size: var(--font-sm);">${CATEGORY_LABELS[category]}</h5>`;
                    html += `<div class="publications-sortable" data-section="academic" data-category="${category}">`;
                    categoryPubs.forEach(pub => {
                        html += renderPublicationItem(pub);
                    });
                    html += '</div>';
                }
            });
        }

        // Creative publications - grouped by category
        if (creative.length > 0) {
            html += '<h4 style="margin-top: var(--space-4); margin-bottom: var(--space-3); color: var(--text-secondary);">Creative Publications</h4>';

            CREATIVE_CATEGORY_ORDER.forEach(category => {
                const categoryPubs = creative.filter(p => p.category === category);
                if (categoryPubs.length > 0) {
                    html += `<h5 style="margin-top: var(--space-3); margin-bottom: var(--space-2); color: var(--text-tertiary); font-size: var(--font-sm);">${CATEGORY_LABELS[category]}</h5>`;
                    html += `<div class="publications-sortable" data-section="creative" data-category="${category}">`;
                    categoryPubs.forEach(pub => {
                        html += renderPublicationItem(pub);
                    });
                    html += '</div>';
                }
            });
        }

        html += '</div>';
        html += '<div style="margin-top: var(--space-3); padding: var(--space-3); background: var(--bg-tertiary); border-radius: var(--radius-base); text-align: center;">';
        html += '<small style="color: var(--text-secondary);">Drag publications to reorder them within their category. Changes save automatically.</small>';
        html += '</div>';

        listContainer.innerHTML = html;

        // Initialize drag-and-drop
        initPublicationsDragDrop();

    } catch (error) {
        listContainer.innerHTML = `<p style="color: var(--text-error);">Error loading publications: ${error.message}</p>`;
    }
}

/**
 * Render a single publication item
 */
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

/**
 * Initialize drag-and-drop for publication reordering
 */
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

/**
 * Get the element after which the dragged item should be inserted
 */
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

/**
 * Save the new order of publications after drag-and-drop
 */
async function savePublicationsOrder(container) {
    const pubElements = container.querySelectorAll('.pub-management-item');
    const publicationIds = Array.from(pubElements).map(el => el.dataset.pubId);

    try {
        const response = await fetch('/writing/publications/reorder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
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

/**
 * Save publication (create or update)
 */
export async function savePublication() {
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
        authors: publicationAuthors,
        venue: document.getElementById('publicationVenue').value,
        publication_date: document.getElementById('publicationDate').value,
        category: document.getElementById('publicationCategory').value,
        section: section,
        url: document.getElementById('publicationUrl').value || null,
        doi: document.getElementById('publicationDoi').value || null,
        pmid: document.getElementById('publicationPmid').value || null,
        volume_issue: document.getElementById('publicationVolumeIssue').value || null,
        badge: document.getElementById('publicationBadge').value || null,
        display_order: 0
    };

    const url = id ? `/writing/update/${id}` : '/writing/create';

    try {
        showStatus(statusDiv, 'Saving publication...', 'loading');

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
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

/**
 * Edit an existing publication
 */
export async function editPublication(publicationId) {
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

/**
 * Delete a publication
 */
export async function deletePublication(publicationId) {
    if (!confirm('Are you sure you want to delete this publication?')) {
        return;
    }

    try {
        const response = await fetch(`/writing/delete/${publicationId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
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
