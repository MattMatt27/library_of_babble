"""
One-time backfill for Artworks.medium_category.

Populates the coarse `medium_category` bucket for every artwork from its
free-text `medium` using app.artworks.medium_categories.categorize_medium().
Idempotent: re-running re-derives categories (safe after rule tweaks).

Usage (from repo root, with the venv):
    .venv/bin/python -m scripts.utils.backfill_medium_category          # apply
    .venv/bin/python -m scripts.utils.backfill_medium_category --dry-run

Targets whatever database the app config points at (DATABASE_URL), so run
it against prod explicitly at deploy time.
"""
import sys
from collections import Counter

from app import create_app
from app.extensions import db
from app.artworks.models import Artworks
from app.artworks.medium_categories import categorize_medium


def run(dry_run=False):
    app = create_app()
    with app.app_context():
        artworks = Artworks.query.all()
        counts = Counter()
        changed = 0
        for art in artworks:
            new_cat = categorize_medium(art.medium)
            counts[new_cat] += 1
            if art.medium_category != new_cat:
                changed += 1
                if not dry_run:
                    art.medium_category = new_cat
        if not dry_run:
            db.session.commit()

        print(f"{'[dry-run] ' if dry_run else ''}artworks: {len(artworks)} | "
              f"updated: {changed}")
        for cat, c in counts.most_common():
            print(f"  {c:5}  {cat}")


if __name__ == "__main__":
    run(dry_run="--dry-run" in sys.argv)
