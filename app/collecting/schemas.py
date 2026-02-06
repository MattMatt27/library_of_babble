"""
Card Collection Schemas

Category-specific field schemas and constants for the card collection system.
"""

# Category-specific fields rendered dynamically in the modal
CARD_CATEGORY_SCHEMAS = {
    'sports': [
        {'key': 'player', 'label': 'Player', 'type': 'text'},
        {'key': 'team', 'label': 'Team', 'type': 'text'},
        {'key': 'position', 'label': 'Position', 'type': 'text'},
        {'key': 'sport', 'label': 'Sport', 'type': 'select',
         'options': ['Baseball', 'Football', 'Basketball', 'Hockey', 'Soccer', 'Golf', 'Other']},
        {'key': 'is_rookie', 'label': 'Rookie Card', 'type': 'boolean'},
    ],
    'pokemon': [
        {'key': 'pokemon_name', 'label': 'Pokemon', 'type': 'text'},
        {'key': 'pokemon_type', 'label': 'Type', 'type': 'text'},
        {'key': 'hp', 'label': 'HP', 'type': 'number'},
        {'key': 'stage', 'label': 'Stage', 'type': 'select',
         'options': ['Basic', 'Stage 1', 'Stage 2', 'VMAX', 'V', 'EX', 'GX', 'Other']},
        {'key': 'is_first_edition', 'label': 'First Edition', 'type': 'boolean'},
    ],
    'tcg': [
        {'key': 'game', 'label': 'Game', 'type': 'text'},  # Magic, Yu-Gi-Oh
        {'key': 'card_type', 'label': 'Card Type', 'type': 'text'},
        {'key': 'rarity', 'label': 'Rarity', 'type': 'text'},
        {'key': 'is_first_edition', 'label': 'First Edition', 'type': 'boolean'},
    ],
    'historical': [
        {'key': 'subject', 'label': 'Subject', 'type': 'text'},
        {'key': 'era', 'label': 'Era', 'type': 'text'},
        {'key': 'description', 'label': 'Description', 'type': 'textarea'},
    ],
    'advertising': [
        {'key': 'company', 'label': 'Brand/Company', 'type': 'text'},
        {'key': 'product', 'label': 'Product', 'type': 'text'},
        {'key': 'era', 'label': 'Era', 'type': 'text'},
    ],
    'other': [
        {'key': 'description', 'label': 'Description', 'type': 'textarea'},
    ],
}

# Special features - appear for ALL categories
CARD_SPECIAL_FEATURES = [
    {'key': 'autographed', 'label': 'Autographed', 'type': 'boolean'},
    {'key': 'autograph_subject', 'label': 'Signed By', 'type': 'text', 'show_if': 'autographed'},
    {'key': 'autograph_type', 'label': 'Auto Type', 'type': 'select',
     'options': ['On-Card', 'Sticker', 'Cut Signature'], 'show_if': 'autographed'},

    {'key': 'memorabilia', 'label': 'Memorabilia/Relic', 'type': 'boolean'},
    {'key': 'memorabilia_type', 'label': 'Type', 'type': 'select',
     'options': ['Jersey', 'Patch', 'Bat', 'Ball', 'Glove', 'Helmet', 'Other'], 'show_if': 'memorabilia'},
    {'key': 'game_used', 'label': 'Game-Used', 'type': 'boolean', 'show_if': 'memorabilia'},

    {'key': 'serial_numbered', 'label': 'Serial Numbered', 'type': 'text'},  # "/99" or "45/99"

    {'key': 'printing_plate', 'label': 'Printing Plate', 'type': 'boolean'},
    {'key': 'plate_color', 'label': 'Color', 'type': 'select',
     'options': ['Cyan', 'Magenta', 'Yellow', 'Black'], 'show_if': 'printing_plate'},

    {'key': 'is_insert', 'label': 'Insert/Chase Card', 'type': 'boolean'},

    {'key': 'additional', 'label': 'Additional Attributes', 'type': 'textarea'},
]

# Card variant options
CARD_VARIANTS = [
    'Base', 'Foil', 'Refractor', 'Holo', 'Parallel', 'Prizm',
    'Chrome', 'Gold', 'Silver', 'Bronze', 'Rainbow', 'Black',
    'Printing Plate', 'Error', '1/1', 'Other'
]

# Card categories
CARD_CATEGORIES = [
    {'value': 'sports', 'label': 'Sports'},
    {'value': 'pokemon', 'label': 'Pokemon'},
    {'value': 'tcg', 'label': 'TCG (Magic, Yu-Gi-Oh, etc.)'},
    {'value': 'historical', 'label': 'Historical'},
    {'value': 'advertising', 'label': 'Advertising'},
    {'value': 'other', 'label': 'Other'},
]

# Card condition options
CARD_CONDITIONS = [
    {'value': 'mint', 'label': 'Mint (M)'},
    {'value': 'near_mint', 'label': 'Near Mint (NM)'},
    {'value': 'excellent', 'label': 'Excellent (EX)'},
    {'value': 'very_good', 'label': 'Very Good (VG)'},
    {'value': 'good', 'label': 'Good (G)'},
    {'value': 'poor', 'label': 'Poor (P)'},
]

# Grading services
GRADING_SERVICES = ['PSA', 'BGS', 'CGC', 'SGC', 'HGA', 'Other']

# Storage type options
STORAGE_TYPES = [
    {'value': 'binder', 'label': 'Binder'},
    {'value': 'box', 'label': 'Box'},
    {'value': 'display_case', 'label': 'Display Case'},
    {'value': 'framed', 'label': 'Framed'},
    {'value': 'toploader', 'label': 'Toploader'},
    {'value': 'slab', 'label': 'Graded Slab'},
]

# Visibility options
CARD_VISIBILITY_OPTIONS = [
    {'value': 'public', 'label': 'Public'},
    {'value': 'for_trade', 'label': 'For Trade'},
    {'value': 'for_sale', 'label': 'For Sale'},
    {'value': 'hidden', 'label': 'Hidden'},
]


def get_category_choices():
    """Return category choices for form select."""
    return [(c['value'], c['label']) for c in CARD_CATEGORIES]


def get_condition_choices():
    """Return condition choices for form select."""
    return [(c['value'], c['label']) for c in CARD_CONDITIONS]


def get_storage_type_choices():
    """Return storage type choices for form select."""
    return [(s['value'], s['label']) for s in STORAGE_TYPES]


def get_visibility_choices():
    """Return visibility choices for form select."""
    return [(v['value'], v['label']) for v in CARD_VISIBILITY_OPTIONS]
