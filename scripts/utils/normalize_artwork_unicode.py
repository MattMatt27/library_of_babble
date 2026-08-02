"""
One-time backfill: NFC-normalize Artworks.artist and Artworks.file_name.

Image URLs are built as images/artists/<artist>/<file_name>. When the DB and
the S3 key disagree on Unicode composition (NFC vs NFD) for accented names,
the URL 404s. New writes are normalized to NFC in the routes; this fixes
existing rows. Pair it with the S3 key rename (scripts/utils that renames
non-NFC S3 objects to NFC) so both sides match.

Idempotent. Targets whatever DB the app config points at (DATABASE_URL), so
run it explicitly against prod at deploy time.

Usage (repo root, with venv):
    .venv/bin/python -m scripts.utils.normalize_artwork_unicode --dry-run
    .venv/bin/python -m scripts.utils.normalize_artwork_unicode
"""
import sys
import unicodedata

from app import create_app
from app.extensions import db
from app.artworks.models import Artworks


def run(dry_run=False):
    app = create_app()
    with app.app_context():
        artworks = Artworks.query.all()
        changed_artist = changed_file = 0
        for art in artworks:
            if art.artist:
                nfc = unicodedata.normalize('NFC', art.artist)
                if nfc != art.artist:
                    changed_artist += 1
                    if not dry_run:
                        art.artist = nfc
            if art.file_name:
                nfc = unicodedata.normalize('NFC', art.file_name)
                if nfc != art.file_name:
                    changed_file += 1
                    if not dry_run:
                        art.file_name = nfc
        if not dry_run:
            db.session.commit()

        print(f"{'[dry-run] ' if dry_run else ''}artworks: {len(artworks)} | "
              f"artist normalized: {changed_artist} | file_name normalized: {changed_file}")


if __name__ == "__main__":
    run(dry_run="--dry-run" in sys.argv)
