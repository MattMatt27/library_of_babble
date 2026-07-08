"""
Medium categorization for artworks.

The `medium` field is free text (~1,000 distinct strings across the
collection), so we bucket it into a small set of coarse categories using
ordered keyword rules rather than a literal lookup table. First matching
rule wins, so order matters: photo/print processes are checked before
generic painting/drawing terms (e.g. "gelatin silver print" must resolve
to Photograph before the bare word "print" sends it to Print).

The result is stored on Artworks.medium_category (computed on save and via
a one-time backfill) so the pondering page can filter/paginate in SQL.
Coverage on the current collection is ~99.7%; the rest fall to OTHER and
can be hand-corrected on the stored column if desired.
"""

# Canonical buckets, in the order they should appear in the filter UI.
CATEGORY_ORDER = [
    "Painting",
    "Watercolor & Gouache",
    "Drawing",
    "Print",
    "Photograph",
    "Sculpture",
    "Ceramics, Glass & Metalwork",
    "Textiles",
    "Collage & Mixed Media",
    "Other",
]

OTHER = "Other"

# Ordered (category, keywords) — FIRST match wins. This order is significant;
# see module docstring. Keywords are matched as case-insensitive substrings.
_MATCH_RULES = [
    ("Photograph", [
        "gelatin silver", "albumen", "chromogenic", "chromogentic", "dye-transfer",
        "dye transfer", "platinum print", "daguerreotype", "ambrotype", "tintype",
        "cibachrome", "c-print", "silver print", "contact print", "photo rag",
        "inkjet", "pigment print", "giclée", "giclee", "cyanotype", "cliché-verre",
        "cliche-verre", "photomechanical", "photograph", "photo ",
    ]),
    # Before Print so "cut-and-pasted printed paper" reads as collage, not print.
    ("Collage & Mixed Media", [
        "collage", "cut-and-pasted", "cut and pasted", "mixed media",
        "mixed technique", "assemblage", "découpage", "decoupage",
    ]),
    ("Print", [
        "woodblock", "woodcut", "wood engraving", "linocut", "linoleum", "etching",
        "engraving", "lithograph", "screenprint", "silk screen", "silkscreen",
        "serigraph", "aquatint", "mezzotint", "drypoint", "monotype", "monoprint",
        "chine coll", "collagraph", "intaglio", "photogravure", "relief print",
        "metalcut", "stencil", "surimono", "color plate", "print",
    ]),
    ("Painting", [
        "oil", "acrylic", "tempera", "encaustic", "fresco", "distemper", "enamel",
        "hanging scroll", "on silk", "on pith", "pigment on", "colors on", "color on",
        "painting", "painted",
    ]),
    ("Watercolor & Gouache", ["watercolor", "watercolour", "gouache"]),
    ("Drawing", [
        "graphite", "charcoal", "pastel", "chalk", "conté", "conte", "pen and",
        "pencil", "crayon", "silverpoint", "metalpoint", "sanguine", "cartoon",
        "brush and", "ink and", "ink,", "ink on", "india ink", "drawing", "wash",
    ]),
    ("Textiles", [
        "embroidery", "tapestry", "textile", "velvet", "woven", "quilt", "fiber",
        "fibre", "needlework", "weaving",
    ]),
    ("Sculpture", [
        "bronze", "marble", "terracotta", "terra cotta", "plaster", "cast ",
        "carved", "carving", "sculpt", "granite", "alabaster", "limestone",
        "ivory", "jade", "amber", "obsidian", "shell", "bone", "wax", "cinnabar",
        "wood",
    ]),
    ("Ceramics, Glass & Metalwork", [
        "ceramic", "earthenware", "creamware", "porcelain", "stoneware", "faience",
        "maiolica", "majolica", "glaze", "glass", "silver", "steel", "brass",
        "bronze", "gold", "shakudo", "niello", "lacquer", "tin", "pewter",
        "copper", "iron", "enamelware",
    ]),
]


def categorize_medium(medium):
    """Return the coarse category bucket for a free-text medium string.

    Empty/None mediums and anything unmatched return ``OTHER``.
    """
    if not medium:
        return OTHER
    s = medium.lower().strip()
    if not s:
        return OTHER
    for category, keywords in _MATCH_RULES:
        if any(k in s for k in keywords):
            return category
    return OTHER
