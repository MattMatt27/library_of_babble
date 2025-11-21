"""
TV Shows ETL Script
Loads TV show data from Boredom Killer CSV

INCREMENTAL IMPORT STRATEGY:
- Database is source of truth
- Watched shows (has date_finished, last_watched, or my_rating) are locked - only report conflicts if data differs
- Unwatched shows can be updated (metadata corrections)
- New shows are added
- Never deletes existing data
"""
import csv
import sys
import json
from pathlib import Path
from datetime import datetime
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app import create_app
from app.extensions import db
from app.shows.models import TVShows
from app.common.models import Reviews, Collection, CollectionItem

# Configure paths
CSV_FOLDER = Path('data/staging/')
LOADED_FOLDER = Path('data/loaded/')
REPORTS_FOLDER = Path('data/reports/')


def add_item_to_collection(collection_name, item_type, item_id):
    """
    Add an item to a collection. Creates the collection if it doesn't exist.
    Returns True if item was added, False if it already existed.
    """
    # Get or create the collection
    collection = Collection.query.filter_by(collection_name=collection_name).first()
    if not collection:
        collection = Collection(
            collection_name=collection_name,
            site_approved=False  # New collections default to not approved
        )
        db.session.add(collection)
        db.session.flush()  # Get the ID

    # Check if item already exists in this collection
    existing_item = CollectionItem.query.filter_by(
        collection_id=collection.id,
        item_type=item_type,
        item_id=item_id
    ).first()

    if not existing_item:
        collection_item = CollectionItem(
            collection_id=collection.id,
            item_type=item_type,
            item_id=item_id
        )
        db.session.add(collection_item)
        return True

    return False


def generate_conflict_report(source_file, import_type, conflicts):
    """Generate a JSON conflict report and save to reports folder"""
    if not conflicts:
        return None

    if not REPORTS_FOLDER.exists():
        REPORTS_FOLDER.mkdir(parents=True)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    report_data = {
        'import_type': import_type,
        'source_file': source_file,
        'timestamp': timestamp,
        'summary': {
            'total_conflicts': len(conflicts)
        },
        'conflicts': conflicts
    }

    report_filename = f"{import_type}_conflicts_{timestamp}.json"
    report_path = REPORTS_FOLDER / report_filename

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"\n⚠️  Conflict report generated: {report_path}")
    return report_path


def load_boredom_killer_shows(csv_file='Boredom Killer - TV.csv', csv_folder=None):
    """
    Load TV shows from Boredom Killer CSV (INCREMENTAL)

    Strategy:
    - Watched shows (has date_finished, last_watched, or my_rating) are locked: compare and report conflicts if different
    - Unwatched shows can be updated (metadata corrections)
    - New shows are added
    """
    folder = Path(csv_folder) if csv_folder else CSV_FOLDER
    csv_path = folder / csv_file

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
            # Handle both 'TV Show' (for TV shows) and 'Docuseries' (for docuseries) columns
            title = row.get('TV Show') or row.get('Docuseries', '')

            data = {
                'tvdb_id': tvdb_id,
                'imdb_id': row['IMDB ID'].strip() if row['IMDB ID'] else None,
                'title': title.strip(),
                'year': int(row['Year']) if row['Year'].strip().isdigit() else None,
                'cover_image_url': row['Poster Image'].strip() if row['Poster Image'] else None,
                'collections': f"{row['Collections']}|{row['Tags']}".strip('|') if row['Collections'] or row['Tags'] else None,
                'status': row['Plex Status'].strip() if row['Plex Status'] else None
            }

            # Store the latest data for this TVDB ID, along with row number
            csv_shows[tvdb_id] = {'data': data, 'row': row_number}

    if duplicate_count > 0:
        print(f"Found {duplicate_count} duplicates - kept latest entries")

    # Process the deduplicated data
    conflicts = []
    shows_added = 0
    shows_updated = 0
    shows_skipped = 0
    collections_added = 0

    for tvdb_id, entry in csv_shows.items():
        data = entry['data']
        row_num = entry['row']

        if tvdb_id in existing_shows:
            existing_show = existing_shows[tvdb_id]

            # Check if show is watched (locked)
            is_watched = existing_show.date_finished or existing_show.last_watched or existing_show.my_rating

            if is_watched:
                # Show is watched - it's locked
                # Only compare metadata fields (not user-specific fields)
                has_conflict = False
                conflict_fields = {}

                metadata_fields = ['title', 'year', 'cover_image_url', 'imdb_id', 'status']

                for key in metadata_fields:
                    if key in data:
                        csv_value = data[key]
                        db_value = getattr(existing_show, key)

                        if csv_value != db_value:
                            has_conflict = True
                            conflict_fields[key] = {
                                'db_value': db_value,
                                'csv_value': csv_value
                            }

                if has_conflict:
                    conflicts.append({
                        'row': row_num,
                        'tvdb_id': tvdb_id,
                        'title': data['title'],
                        'year': data['year'],
                        'issue': 'Watched show metadata differs from database',
                        'conflicting_fields': conflict_fields
                    })

                shows_skipped += 1
            else:
                # Show is not watched - allow metadata update
                for key, value in data.items():
                    if key != 'collections' and value is not None:
                        setattr(existing_show, key, value)
                db.session.add(existing_show)
                shows_updated += 1

            # Update collections (always incremental, even for watched shows)
            if data.get('collections'):
                collection_list = data['collections'].split('|')
                for collection_name in collection_list:
                    collection_name = collection_name.strip()
                    if collection_name:
                        if add_item_to_collection(collection_name, 'TVShow', tvdb_id):
                            collections_added += 1
        else:
            # Create new TV show record
            new_show = TVShows(**data)
            db.session.add(new_show)
            shows_added += 1

            # Add collections if available
            if data.get('collections'):
                collection_list = data['collections'].split('|')
                for collection_name in collection_list:
                    collection_name = collection_name.strip()
                    if collection_name:
                        if add_item_to_collection(collection_name, 'TVShow', tvdb_id):
                            collections_added += 1

    # Commit all changes
    db.session.commit()

    print(f"\n📺 Boredom Killer TV Shows Import Summary:")
    print(f"  Shows added: {shows_added}")
    print(f"  Shows updated: {shows_updated}")
    print(f"  Shows skipped (watched, unchanged): {shows_skipped - len(conflicts)}")
    print(f"  Conflicts detected: {len(conflicts)}")
    print(f"  Collections added: {collections_added}")

    # Generate conflict report if needed
    if conflicts:
        generate_conflict_report(csv_file, 'boredom_killer_shows', conflicts)

    # Move the processed file (only in interactive mode, not for web uploads)
    if csv_folder is None:
        if not LOADED_FOLDER.exists():
            LOADED_FOLDER.mkdir(parents=True)
        current_date = datetime.now().strftime('%Y-%m-%d')
        new_file_name = f"{current_date}_{csv_file}"
        shutil.move(str(csv_path), str(LOADED_FOLDER / new_file_name))

    return {'added': shows_added, 'updated': shows_updated, 'conflicts': len(conflicts)}


def reset_sequence(table_name):
    """Reset the auto-increment sequence for a table to avoid conflicts"""
    # Whitelist allowed table names to prevent SQL injection
    ALLOWED_TABLES = {'shows', 'reviews', 'collections'}

    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Table {table_name} not in whitelist")

    try:
        # Safe to use f-string now that table_name is validated against whitelist
        # Note: PostgreSQL doesn't support parameters for table/column names in this context
        db.session.execute(db.text(f"""
            SELECT setval(pg_get_serial_sequence('{table_name}', 'id'),
                         COALESCE((SELECT MAX(id) FROM {table_name}), 1),
                         true);
        """))
        db.session.commit()
    except Exception as e:
        # Silently fail for SQLite (doesn't need this)
        db.session.rollback()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='TV Shows ETL Script')
    parser.add_argument('file_path', nargs='?', help='Path to CSV file')
    parser.add_argument('--bk-tv', action='store_true', help='Import Boredom Killer TV Shows CSV')
    parser.add_argument('--bk-docuseries', action='store_true', help='Import Boredom Killer Docuseries CSV (goes to shows table)')
    parser.add_argument('--use-transaction', action='store_true', help='Run in transaction mode with automatic rollback on error')

    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        try:
            # Reset sequences to prevent ID conflicts
            reset_sequence('reviews')
            reset_sequence('collections')

            # Interactive mode (no arguments)
            if not any([args.bk_tv, args.bk_docuseries]):
                print("TV Shows ETL Script")
                print("=" * 50)

                print("\nLoading Boredom Killer TV shows...")
                load_boredom_killer_shows()

                print("\n" + "=" * 50)
                print("TV Shows ETL Complete!")
                sys.exit(0)

            # CLI mode
            if args.use_transaction:
                print("Running in transaction mode - all changes will be rolled back on error")

            # Boredom Killer TV Shows
            if args.bk_tv:
                if not args.file_path:
                    print("Error: file_path required for --bk-tv")
                    sys.exit(1)

                print(f"Importing Boredom Killer TV Shows from: {args.file_path}")
                file_path = Path(args.file_path)
                result = load_boredom_killer_shows(file_path.name, csv_folder=str(file_path.parent))

                if result:
                    print(f"TV shows added: {result.get('added', 0)}")
                    print(f"TV shows updated: {result.get('updated', 0)}")
                    print(f"Conflicts reported: {result.get('conflicts', 0)}")

            # Boredom Killer Docuseries (goes to shows table)
            if args.bk_docuseries:
                if not args.file_path:
                    print("Error: file_path required for --bk-docuseries")
                    sys.exit(1)

                print(f"Importing Boredom Killer Docuseries from: {args.file_path}")
                file_path = Path(args.file_path)
                result = load_boredom_killer_shows(file_path.name, csv_folder=str(file_path.parent))

                if result:
                    print(f"Docuseries added: {result.get('added', 0)}")
                    print(f"Docuseries updated: {result.get('updated', 0)}")
                    print(f"Conflicts reported: {result.get('conflicts', 0)}")

            # Commit if transaction mode
            if args.use_transaction:
                db.session.commit()
                print("✓ Transaction committed successfully")

            sys.exit(0)

        except Exception as e:
            print(f"Error during import: {str(e)}", file=sys.stderr)
            if args.use_transaction:
                db.session.rollback()
                print("✗ Transaction rolled back due to error", file=sys.stderr)
            sys.exit(1)
