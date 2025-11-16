"""
TV Shows ETL Script
Loads TV show data from Boredom Killer CSV
"""
import csv
import sys
from pathlib import Path
from datetime import datetime
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app import create_app
from app.extensions import db
from app.shows.models import TVShows
from app.collections.models import Reviews, Collections

# Configure paths
CSV_FOLDER = Path('data/staging/')
LOADED_FOLDER = Path('data/loaded/')


def load_boredom_killer_shows(csv_file='Boredom Killer - TV.csv'):
    """
    Load TV shows from Boredom Killer CSV

    Expected CSV columns:
    - TVDB ID
    - IMDB ID
    - TV Show
    - Year
    - Poster Image
    - Collections
    - Tags
    - Plex Status
    """
    csv_path = CSV_FOLDER / csv_file

    if not csv_path.exists():
        print(f"CSV file {csv_file} not found in {CSV_FOLDER}")
        return

    # Get all existing TV show TVDB IDs
    existing_shows = {tvshow.tvdb_id: tvshow for tvshow in TVShows.query.all()}

    # Store shows by TVDB ID (deduplicate)
    csv_shows = {}
    duplicate_count = 0

    with open(csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row_number, row in enumerate(reader, start=2):
            tvdb_id = row['TVDB ID'].strip()

            # Skip rows with null or empty TVDB ID
            if not tvdb_id or not row['Year']:
                continue

            # Check for duplicates
            if tvdb_id in csv_shows:
                duplicate_count += 1
                print(f"Row {row_number}: Duplicate TVDB ID {tvdb_id}. Keeping latest entry.")

            # Prepare data for TV show
            data = {
                'tvdb_id': tvdb_id,
                'imdb_id': row['IMDB ID'].strip() if row['IMDB ID'] else None,
                'title': row['TV Show'].strip(),
                'year': int(row['Year']) if row['Year'].strip().isdigit() else None,
                'cover_image_url': row['Poster Image'].strip() if row['Poster Image'] else None,
                'collections': f"{row['Collections']}|{row['Tags']}".strip('|') if row['Collections'] or row['Tags'] else None,
                'status': row['Plex Status'].strip() if row['Plex Status'] else None
            }

            # Store the latest data for this TVDB ID
            csv_shows[tvdb_id] = data

    if duplicate_count > 0:
        print(f"Found {duplicate_count} duplicates - kept latest entries")

    # Process the deduplicated data
    shows_added = 0
    shows_updated = 0

    for tvdb_id, data in csv_shows.items():
        if tvdb_id in existing_shows:
            # Update existing show
            existing_show = existing_shows[tvdb_id]

            # Preserve fields that shouldn't be overwritten
            preserved_fields = {
                'my_rating': existing_show.my_rating,
                'my_review': existing_show.my_review,
                'date_finished': existing_show.date_finished,
                'last_watched': existing_show.last_watched
            }

            for key, value in data.items():
                if value is not None:
                    setattr(existing_show, key, value)

            # Restore preserved fields
            for key, value in preserved_fields.items():
                setattr(existing_show, key, value)

            shows_updated += 1

            # Update collections based on the new collections data
            if 'collections' in data and data['collections']:
                # Get existing collections
                existing_collections = set(
                    collection.collection_name for collection in
                    Collections.query.filter_by(item_type='TVShow', item_id=tvdb_id).all()
                )

                # Add new collections without deleting existing ones
                collection_list = data['collections'].split('|')
                for collection_name in collection_list:
                    collection_name = collection_name.strip()
                    if collection_name and collection_name not in existing_collections:
                        collection = Collections(
                            collection_name=collection_name,
                            item_type='TVShow',
                            item_id=tvdb_id
                        )
                        db.session.add(collection)
        else:
            # Create new TV show record
            new_show = TVShows(**data)
            db.session.add(new_show)
            shows_added += 1

            # Add collections if available
            if 'collections' in data and data['collections']:
                collection_list = data['collections'].split('|')
                for collection_name in collection_list:
                    collection_name = collection_name.strip()
                    if collection_name:
                        collection = Collections(
                            collection_name=collection_name,
                            item_type='TVShow',
                            item_id=tvdb_id
                        )
                        db.session.add(collection)

    # Commit all changes
    db.session.commit()
    print(f"TV shows loaded: {shows_added} added, {shows_updated} updated")

    # Move the processed file
    if not LOADED_FOLDER.exists():
        LOADED_FOLDER.mkdir(parents=True)
    current_date = datetime.now().strftime('%Y-%m-%d')
    new_file_name = f"{current_date}_{csv_file}"
    shutil.move(str(csv_path), str(LOADED_FOLDER / new_file_name))


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("TV Shows ETL Script")
        print("=" * 50)

        print("\nLoading Boredom Killer TV shows...")
        load_boredom_killer_shows()

        print("\n" + "=" * 50)
        print("TV Shows ETL Complete!")
