/**
 * Card Collection Modal JavaScript
 * Handles dynamic form fields, search, and CRUD operations
 */

// State
let cardSchemas = null;
let selectedCardId = null;
let isEditMode = false;
let searchTimeout = null;

// =============================================================================
// Initialization
// =============================================================================

async function initCardModal() {
    await loadCardSchemas();
    setupEventListeners();
}

async function loadCardSchemas() {
    try {
        const response = await fetch('/collecting/cards/schemas');
        if (!response.ok) throw new Error('Failed to load schemas');
        cardSchemas = await response.json();
        populateStaticFields();
    } catch (error) {
        console.error('Error loading card schemas:', error);
        showCardModalStatus('Failed to load form data. Please refresh the page.', 'error');
    }
}

function populateStaticFields() {
    if (!cardSchemas) return;

    // Categories
    const categorySelect = document.getElementById('cardCategory');
    if (categorySelect) {
        categorySelect.innerHTML = '<option value="">Select...</option>' +
            cardSchemas.category_options.map(c =>
                `<option value="${c.value}">${c.label}</option>`
            ).join('');
    }

    // Variants
    const variantSelect = document.getElementById('cardVariant');
    if (variantSelect) {
        variantSelect.innerHTML = cardSchemas.variants.map(v =>
            `<option value="${v.toLowerCase()}">${v}</option>`
        ).join('');
    }

    // Conditions
    const conditionSelects = ['copyCondition', 'editCopyCondition'];
    conditionSelects.forEach(id => {
        const select = document.getElementById(id);
        if (select) {
            select.innerHTML = cardSchemas.conditions.map(c =>
                `<option value="${c.value}">${c.label}</option>`
            ).join('');
        }
    });

    // Grading services
    const gradingSelects = ['gradingService', 'editGradingService'];
    gradingSelects.forEach(id => {
        const select = document.getElementById(id);
        if (select) {
            select.innerHTML = cardSchemas.grading_services.map(s =>
                `<option value="${s}">${s}</option>`
            ).join('');
        }
    });

    // Storage types - radio buttons for add modal
    const storageTypeGroup = document.getElementById('storageTypeGroup');
    if (storageTypeGroup) {
        storageTypeGroup.innerHTML = cardSchemas.storage_types.map((s, i) =>
            `<label class="radio-label">
                <input type="radio" name="storageType" value="${s.value}" ${i === 0 ? 'checked' : ''}>
                <span>${s.label}</span>
            </label>`
        ).join('');
    }

    // Storage types - select for edit modal
    const editStorageType = document.getElementById('editStorageType');
    if (editStorageType) {
        editStorageType.innerHTML = cardSchemas.storage_types.map(s =>
            `<option value="${s.value}">${s.label}</option>`
        ).join('');
    }

    // Visibility - radio buttons for add modal
    const visibilityGroup = document.getElementById('visibilityGroup');
    if (visibilityGroup) {
        visibilityGroup.innerHTML = cardSchemas.visibility_options.map((v, i) =>
            `<label class="radio-label">
                <input type="radio" name="visibility" value="${v.value}" ${i === 0 ? 'checked' : ''}>
                <span>${v.label}</span>
            </label>`
        ).join('');
    }

    // Visibility - select for edit modal
    const editVisibility = document.getElementById('editVisibility');
    if (editVisibility) {
        editVisibility.innerHTML = cardSchemas.visibility_options.map(v =>
            `<option value="${v.value}">${v.label}</option>`
        ).join('');
    }

    // Storage locations datalist
    const datalist = document.getElementById('storageLocationsList');
    if (datalist && cardSchemas.storage_locations) {
        datalist.innerHTML = cardSchemas.storage_locations.map(loc =>
            `<option value="${loc}">`
        ).join('');
    }
}

function setupEventListeners() {
    // Category change - update dynamic fields
    const categorySelect = document.getElementById('cardCategory');
    if (categorySelect) {
        categorySelect.addEventListener('change', updateCategoryFields);
    }

    // Card search
    const searchInput = document.getElementById('cardSearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounceSearch);
        searchInput.addEventListener('focus', () => {
            if (searchInput.value.length >= 2) {
                searchExistingCards(searchInput.value);
            }
        });
    }

    // Graded checkbox toggle
    const gradedCheckbox = document.getElementById('copyGraded');
    if (gradedCheckbox) {
        gradedCheckbox.addEventListener('change', () => {
            document.getElementById('gradedFields').style.display =
                gradedCheckbox.checked ? 'block' : 'none';
        });
    }

    const editGradedCheckbox = document.getElementById('editCopyGraded');
    if (editGradedCheckbox) {
        editGradedCheckbox.addEventListener('change', () => {
            document.getElementById('editGradedFields').style.display =
                editGradedCheckbox.checked ? 'block' : 'none';
        });
    }

    // Featured checkbox toggle
    const featuredCheckbox = document.getElementById('copyFeatured');
    if (featuredCheckbox) {
        featuredCheckbox.addEventListener('change', () => {
            document.getElementById('imageUploadFields').style.display =
                featuredCheckbox.checked ? 'block' : 'none';
        });
    }

    // File input change handlers
    const imageFront = document.getElementById('imageFront');
    if (imageFront) {
        imageFront.addEventListener('change', (e) => handleFileSelect(e, 'Front'));
    }

    const imageBack = document.getElementById('imageBack');
    if (imageBack) {
        imageBack.addEventListener('change', (e) => handleFileSelect(e, 'Back'));
    }

    // Close on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closeCardModal();
            }
        });
    });

    // Close search results when clicking outside
    document.addEventListener('click', (e) => {
        const searchResults = document.getElementById('cardSearchResults');
        const searchInput = document.getElementById('cardSearch');
        if (searchResults && !searchResults.contains(e.target) && e.target !== searchInput) {
            searchResults.innerHTML = '';
        }
    });
}

// =============================================================================
// Modal Open/Close
// =============================================================================

function openAddCardModal() {
    resetCardModal();
    isEditMode = false;
    document.getElementById('cardModalTitle').textContent = 'Add Trading Card';
    document.getElementById('saveAndAddBtn').style.display = 'inline-flex';
    openModal('addCardModal');
}

function openEditCardModal(cardId) {
    resetCardModal();
    isEditMode = true;
    selectedCardId = cardId;
    document.getElementById('cardModalTitle').textContent = 'Edit Trading Card';
    document.getElementById('saveAndAddBtn').style.display = 'none';

    // Load card data and populate form
    loadCardForEdit(cardId);
    openModal('addCardModal');
}

function closeCardModal() {
    closeModal('addCardModal');
    resetCardModal();
}

function resetCardModal() {
    selectedCardId = null;
    isEditMode = false;

    // Clear search
    const searchInput = document.getElementById('cardSearch');
    if (searchInput) searchInput.value = '';
    const searchResults = document.getElementById('cardSearchResults');
    if (searchResults) searchResults.innerHTML = '';

    // Clear card identity fields
    ['cardName', 'cardNumber', 'cardBrand', 'cardSetName', 'cardSetYear'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });

    const categorySelect = document.getElementById('cardCategory');
    if (categorySelect) categorySelect.value = '';

    const variantSelect = document.getElementById('cardVariant');
    if (variantSelect) variantSelect.selectedIndex = 0;

    // Clear dynamic fields
    const categoryFields = document.getElementById('categoryFields');
    if (categoryFields) categoryFields.innerHTML = '';
    const specialFeatures = document.getElementById('specialFeatures');
    if (specialFeatures) specialFeatures.innerHTML = '';

    // Reset copy fields
    const conditionSelect = document.getElementById('copyCondition');
    if (conditionSelect) conditionSelect.selectedIndex = 1; // Near Mint default

    const gradedCheckbox = document.getElementById('copyGraded');
    if (gradedCheckbox) {
        gradedCheckbox.checked = false;
        document.getElementById('gradedFields').style.display = 'none';
    }

    const featuredCheckbox = document.getElementById('copyFeatured');
    if (featuredCheckbox) {
        featuredCheckbox.checked = false;
        document.getElementById('imageUploadFields').style.display = 'none';
    }

    // Clear other copy fields
    ['storageLocation', 'copyGrade', 'copyNotes', 'dateAcquired'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });

    // Reset radio buttons
    const storageRadios = document.querySelectorAll('input[name="storageType"]');
    if (storageRadios.length) storageRadios[0].checked = true;

    const visibilityRadios = document.querySelectorAll('input[name="visibility"]');
    if (visibilityRadios.length) visibilityRadios[0].checked = true;

    // Clear file inputs and previews
    ['imageFront', 'imageBack'].forEach(id => {
        const input = document.getElementById(id);
        if (input) input.value = '';
    });
    ['imageFrontName', 'imageBackName'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = 'Click to select image';
    });
    ['imageFrontPreview', 'imageBackPreview'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '';
    });

    // Enable card identity panel
    const identityPanel = document.getElementById('cardIdentityPanel');
    if (identityPanel) identityPanel.classList.remove('disabled');

    // Clear status
    const status = document.getElementById('cardModalStatus');
    if (status) status.innerHTML = '';
}

// =============================================================================
// Dynamic Fields
// =============================================================================

function updateCategoryFields() {
    const category = document.getElementById('cardCategory').value;
    const categoryFieldsContainer = document.getElementById('categoryFields');
    const specialFeaturesContainer = document.getElementById('specialFeatures');

    if (!category || !cardSchemas) {
        categoryFieldsContainer.innerHTML = '';
        specialFeaturesContainer.innerHTML = '';
        return;
    }

    // Category-specific fields
    const fields = cardSchemas.categories[category] || [];
    if (fields.length > 0) {
        const categoryLabel = cardSchemas.category_options.find(c => c.value === category)?.label || category;
        categoryFieldsContainer.innerHTML = `
            <h5>${categoryLabel} Details</h5>
            <div class="dynamic-fields-grid">
                ${fields.map(f => renderField(f, 'detail_')).join('')}
            </div>
        `;
    } else {
        categoryFieldsContainer.innerHTML = '';
    }

    // Special features (same for all categories - autographs, memorabilia, etc. apply to any card type)
    specialFeaturesContainer.innerHTML = `
        <h5>Special Features</h5>
        <div class="dynamic-fields-grid">
            ${cardSchemas.special_features.map(f => renderField(f, 'feature_')).join('')}
        </div>
    `;

    // Setup conditional field visibility (all start hidden/unchecked)
    setupConditionalFields();
}

function renderField(field, prefix) {
    const id = prefix + field.key;
    const showIf = field.show_if ? `data-show-if="${prefix}${field.show_if}"` : '';
    const hideStyle = field.show_if ? 'style="display: none;"' : '';

    switch (field.type) {
        case 'boolean':
            return `
                <div class="form-group inline-checkbox" ${showIf} ${hideStyle}>
                    <label class="checkbox-label">
                        <input type="checkbox" id="${id}" onchange="handleConditionalChange('${id}')">
                        <span>${field.label}</span>
                    </label>
                </div>
            `;
        case 'select':
            return `
                <div class="form-group" ${showIf} ${hideStyle}>
                    <label for="${id}">${field.label}</label>
                    <select id="${id}" class="form-input">
                        <option value="">Select...</option>
                        ${field.options.map(o => `<option value="${o}">${o}</option>`).join('')}
                    </select>
                </div>
            `;
        case 'textarea':
            return `
                <div class="form-group" ${showIf} ${hideStyle}>
                    <label for="${id}">${field.label}</label>
                    <textarea id="${id}" class="form-input" rows="2"></textarea>
                </div>
            `;
        case 'number':
            return `
                <div class="form-group" ${showIf} ${hideStyle}>
                    <label for="${id}">${field.label}</label>
                    <input type="number" id="${id}" class="form-input">
                </div>
            `;
        default:
            return `
                <div class="form-group" ${showIf} ${hideStyle}>
                    <label for="${id}">${field.label}</label>
                    <input type="text" id="${id}" class="form-input">
                </div>
            `;
    }
}

function setupConditionalFields() {
    document.querySelectorAll('[data-show-if]').forEach(el => {
        const dependsOn = el.dataset.showIf;
        const checkbox = document.getElementById(dependsOn);
        if (checkbox) {
            el.style.display = checkbox.checked ? '' : 'none';
        }
    });
}

function handleConditionalChange(changedId) {
    document.querySelectorAll(`[data-show-if="${changedId}"]`).forEach(el => {
        const checkbox = document.getElementById(changedId);
        el.style.display = checkbox.checked ? '' : 'none';
    });
}

// =============================================================================
// Card Search
// =============================================================================

function debounceSearch(e) {
    clearTimeout(searchTimeout);
    const query = e.target.value.trim();

    if (query.length < 2) {
        document.getElementById('cardSearchResults').innerHTML = '';
        return;
    }

    searchTimeout = setTimeout(() => {
        searchExistingCards(query);
    }, 300);
}

async function searchExistingCards(query) {
    const resultsContainer = document.getElementById('cardSearchResults');

    try {
        const response = await fetch(`/collecting/cards/search?q=${encodeURIComponent(query)}&per_page=10`);
        if (!response.ok) throw new Error('Search failed');

        const data = await response.json();

        if (data.cards.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results">No cards found - create a new one below</div>';
            return;
        }

        resultsContainer.innerHTML = data.cards.map(card => `
            <div class="search-result-item" onclick="selectExistingCard(${card.id}, '${escapeHtml(card.name)}')">
                <div class="result-info">
                    <div class="result-name">${escapeHtml(card.name)}</div>
                    <div class="result-meta">
                        ${card.set_name || ''}
                        ${card.card_number ? '#' + card.card_number : ''}
                        ${card.variant && card.variant !== 'base' ? '(' + card.variant + ')' : ''}
                    </div>
                </div>
                <div class="result-copies">${card.copies.length} cop${card.copies.length === 1 ? 'y' : 'ies'}</div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Search error:', error);
        resultsContainer.innerHTML = '<div class="no-results">Search error - please try again</div>';
    }
}

function selectExistingCard(cardId, cardName) {
    selectedCardId = cardId;

    // Disable card identity fields
    document.getElementById('cardIdentityPanel').classList.add('disabled');

    // Update search to show selected card
    document.getElementById('cardSearch').value = '';
    document.getElementById('cardSearchResults').innerHTML = `
        <div class="selected-card-notice">
            <span>Selected: <strong>${escapeHtml(cardName)}</strong></span>
            <button type="button" class="btn-clear" onclick="clearSelectedCard()">Clear</button>
        </div>
    `;
}

function clearSelectedCard() {
    selectedCardId = null;
    document.getElementById('cardIdentityPanel').classList.remove('disabled');
    document.getElementById('cardSearchResults').innerHTML = '';
    document.getElementById('cardSearch').value = '';
}

// =============================================================================
// Save Operations
// =============================================================================

async function saveCardAndCopy(addAnother) {
    const csrfToken = getCSRFToken();

    // Validate
    if (!selectedCardId) {
        const name = document.getElementById('cardName').value.trim();
        const category = document.getElementById('cardCategory').value;

        if (!name) {
            showCardModalStatus('Please enter a card name', 'error');
            return;
        }
        if (!category) {
            showCardModalStatus('Please select a category', 'error');
            return;
        }
    }

    showCardModalStatus('Saving...', 'info');

    try {
        let cardId = selectedCardId;

        // Create card if needed
        if (!cardId) {
            const cardData = collectCardData();
            const cardResponse = await fetch('/collecting/cards', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(cardData)
            });

            const cardResult = await cardResponse.json();
            if (!cardResult.success) {
                showCardModalStatus(cardResult.error || 'Failed to create card', 'error');
                return;
            }
            cardId = cardResult.card_id;
        }

        // Create copy
        const copyData = collectCopyData();
        const copyResponse = await fetch(`/collecting/cards/${cardId}/copies`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(copyData)
        });

        const copyResult = await copyResponse.json();
        if (!copyResult.success) {
            showCardModalStatus(copyResult.error || 'Failed to add copy', 'error');
            return;
        }

        // Upload images if featured
        if (document.getElementById('copyFeatured').checked) {
            await uploadCardImages(copyResult.copy_id);
        }

        if (addAnother) {
            // Keep card selected, clear copy fields
            showCardModalStatus('Card saved! Add another copy.', 'success');
            clearCopyFields();
            selectedCardId = cardId;
        } else {
            closeCardModal();
            // Reload page to show new card
            if (typeof refreshCardList === 'function') {
                refreshCardList();
            } else {
                location.reload();
            }
        }

    } catch (error) {
        console.error('Error saving card:', error);
        showCardModalStatus('An error occurred. Please try again.', 'error');
    }
}

function collectCardData() {
    const details = {};

    // Collect category-specific fields
    document.querySelectorAll('#categoryFields [id^="detail_"]').forEach(el => {
        const key = el.id.replace('detail_', '');
        if (el.type === 'checkbox') {
            if (el.checked) details[key] = true;
        } else if (el.value) {
            details[key] = el.value;
        }
    });

    // Collect special features
    document.querySelectorAll('#specialFeatures [id^="feature_"]').forEach(el => {
        const key = el.id.replace('feature_', '');
        if (el.type === 'checkbox') {
            if (el.checked) details[key] = true;
        } else if (el.value) {
            details[key] = el.value;
        }
    });

    const setYear = document.getElementById('cardSetYear').value;

    return {
        name: document.getElementById('cardName').value.trim(),
        brand: document.getElementById('cardBrand').value.trim() || null,
        set_name: document.getElementById('cardSetName').value.trim() || null,
        set_year: setYear ? parseInt(setYear) : null,
        card_number: document.getElementById('cardNumber').value.trim() || null,
        category: document.getElementById('cardCategory').value,
        variant: document.getElementById('cardVariant').value || 'base',
        details: details
    };
}

function collectCopyData() {
    const storageType = document.querySelector('input[name="storageType"]:checked');
    const visibility = document.querySelector('input[name="visibility"]:checked');

    return {
        condition: document.getElementById('copyCondition').value,
        is_graded: document.getElementById('copyGraded').checked,
        grading_service: document.getElementById('gradingService').value || null,
        grade: document.getElementById('copyGrade').value.trim() || null,
        storage_location: document.getElementById('storageLocation').value.trim() || null,
        storage_type: storageType ? storageType.value : 'binder',
        visibility: visibility ? visibility.value : 'public',
        is_featured: document.getElementById('copyFeatured').checked,
        notes: document.getElementById('copyNotes').value.trim() || null,
        date_acquired: document.getElementById('dateAcquired').value || null
    };
}

async function uploadCardImages(copyId) {
    const csrfToken = getCSRFToken();

    const frontFile = document.getElementById('imageFront').files[0];
    const backFile = document.getElementById('imageBack').files[0];

    if (frontFile) {
        const formData = new FormData();
        formData.append('file', frontFile);
        formData.append('side', 'front');

        await fetch(`/collecting/copies/${copyId}/upload-image`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
            body: formData
        });
    }

    if (backFile) {
        const formData = new FormData();
        formData.append('file', backFile);
        formData.append('side', 'back');

        await fetch(`/collecting/copies/${copyId}/upload-image`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
            body: formData
        });
    }
}

function clearCopyFields() {
    const conditionSelect = document.getElementById('copyCondition');
    if (conditionSelect) conditionSelect.selectedIndex = 1;

    const gradedCheckbox = document.getElementById('copyGraded');
    if (gradedCheckbox) {
        gradedCheckbox.checked = false;
        document.getElementById('gradedFields').style.display = 'none';
    }

    const featuredCheckbox = document.getElementById('copyFeatured');
    if (featuredCheckbox) {
        featuredCheckbox.checked = false;
        document.getElementById('imageUploadFields').style.display = 'none';
    }

    ['copyGrade', 'copyNotes', 'dateAcquired'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });

    ['imageFront', 'imageBack'].forEach(id => {
        const input = document.getElementById(id);
        if (input) input.value = '';
    });
    ['imageFrontName', 'imageBackName'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = 'Click to select image';
    });
    ['imageFrontPreview', 'imageBackPreview'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '';
    });
}

// =============================================================================
// Edit Copy Modal
// =============================================================================

function openEditCopyModal(copyId, copyData) {
    document.getElementById('editCopyId').value = copyId;

    // Populate fields
    document.getElementById('editCopyCondition').value = copyData.condition || 'near_mint';
    document.getElementById('editCopyGraded').checked = copyData.is_graded || false;
    document.getElementById('editGradedFields').style.display = copyData.is_graded ? 'block' : 'none';
    document.getElementById('editGradingService').value = copyData.grading_service || 'PSA';
    document.getElementById('editCopyGrade').value = copyData.grade || '';
    document.getElementById('editStorageLocation').value = copyData.storage_location || '';
    document.getElementById('editStorageType').value = copyData.storage_type || 'binder';
    document.getElementById('editVisibility').value = copyData.visibility || 'public';
    document.getElementById('editCopyFeatured').checked = copyData.is_featured || false;
    document.getElementById('editCopyNotes').value = copyData.notes || '';

    openModal('editCopyModal');
}

async function saveEditedCopy() {
    const copyId = document.getElementById('editCopyId').value;
    const csrfToken = getCSRFToken();

    const data = {
        condition: document.getElementById('editCopyCondition').value,
        is_graded: document.getElementById('editCopyGraded').checked,
        grading_service: document.getElementById('editGradingService').value || null,
        grade: document.getElementById('editCopyGrade').value.trim() || null,
        storage_location: document.getElementById('editStorageLocation').value.trim() || null,
        storage_type: document.getElementById('editStorageType').value,
        visibility: document.getElementById('editVisibility').value,
        is_featured: document.getElementById('editCopyFeatured').checked,
        notes: document.getElementById('editCopyNotes').value.trim() || null
    };

    try {
        const response = await fetch(`/collecting/copies/${copyId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (!result.success) {
            document.getElementById('editCopyStatus').innerHTML =
                `<div class="flash-message error">${result.error || 'Failed to update'}</div>`;
            return;
        }

        closeModal('editCopyModal');
        location.reload();

    } catch (error) {
        console.error('Error updating copy:', error);
        document.getElementById('editCopyStatus').innerHTML =
            '<div class="flash-message error">An error occurred</div>';
    }
}

async function deleteCopy(copyId) {
    if (!confirm('Are you sure you want to delete this copy?')) return;

    const csrfToken = getCSRFToken();

    try {
        const response = await fetch(`/collecting/copies/${copyId}`, {
            method: 'DELETE',
            headers: { 'X-CSRFToken': csrfToken }
        });

        const result = await response.json();
        if (!result.success) {
            alert(result.error || 'Failed to delete');
            return;
        }

        location.reload();

    } catch (error) {
        console.error('Error deleting copy:', error);
        alert('An error occurred');
    }
}

// =============================================================================
// Utilities
// =============================================================================

function handleFileSelect(event, side) {
    const file = event.target.files[0];
    if (!file) return;

    const nameEl = document.getElementById(`image${side}Name`);
    const previewEl = document.getElementById(`image${side}Preview`);

    nameEl.textContent = file.name;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        previewEl.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
    };
    reader.readAsDataURL(file);
}

function showCardModalStatus(message, type) {
    const statusEl = document.getElementById('cardModalStatus');
    if (statusEl) {
        statusEl.innerHTML = `<div class="flash-message ${type}">${escapeHtml(message)}</div>`;
        if (type === 'success') {
            setTimeout(() => { statusEl.innerHTML = ''; }, 3000);
        }
    }
}

function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initCardModal);
