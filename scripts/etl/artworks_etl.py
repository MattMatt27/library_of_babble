"""
Artworks ETL Script
Loads artworks and AI-generated images from CSV files

INCREMENTAL IMPORT STRATEGY:
- Database is source of truth
- Existing artworks are locked - only report conflicts if data differs
- New artworks are added
- NEVER deletes existing artworks (even if not in CSV)
"""
import csv
import sys
import uuid
import json
from pathlib import Path
from datetime import datetime
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app import create_app
from app.extensions import db
from app.artworks.models import Artworks, GeneratedImages

# Configure paths
CSV_FOLDER = Path('data/staging/')
LOADED_FOLDER = Path('data/loaded/')
REPORTS_FOLDER = Path('data/reports/')


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


def load_artworks_from_csv(csv_file='artworks.csv'):
    """
    Load artworks from CSV file (INCREMENTAL)

    Strategy:
    - Existing artworks are locked - compare and report conflicts if data differs
    - New artworks are added
    - NEVER deletes artworks (database is source of truth)
    """
    csv_path = CSV_FOLDER / csv_file

    if not csv_path.exists():
        print(f"CSV file {csv_file} not found in {CSV_FOLDER}")
        return

    # Build a map of existing artworks by their unique key
    existing_artworks = {}
    for artwork in Artworks.query.all():
        key = (artwork.title, artwork.artist, artwork.year, artwork.series, artwork.series_id)
        existing_artworks[key] = artwork

    conflicts = []
    artworks_added = 0
    artworks_skipped = 0

    with open(csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row_num, row in enumerate(reader, start=2):
            # Prepare data for artwork
            data = {
                'title': row['Title'],
                'artist': row['Artist'],
                'after': row['After'],
                'year': row['Year'] if row['Year'].strip() else None,
                'series': row['Series'],
                'series_id': int(row['Series ID']) if row['Series ID'].strip() else None,
                'file_name': row['file_name'],
                'site_approved': bool(int(row['site_approved'])) if row['site_approved'].strip() else False,
                'location': row['Location'],
                'description': row['Description'],
                'medium': row['Medium'],
                'collections': row['Tags']  # Mapping Tags to collections
            }

            # Create unique key
            key = (data['title'], data['artist'], data['year'], data['series'], data['series_id'])

            if key in existing_artworks:
                # Artwork exists - compare data
                existing_artwork = existing_artworks[key]
                has_conflict = False
                conflict_fields = {}

                for field_key, csv_value in data.items():
                    db_value = getattr(existing_artwork, field_key)

                    if csv_value != db_value:
                        has_conflict = True
                        conflict_fields[field_key] = {
                            'db_value': db_value,
                            'csv_value': csv_value
                        }

                if has_conflict:
                    conflicts.append({
                        'row': row_num,
                        'title': data['title'],
                        'artist': data['artist'],
                        'year': data['year'],
                        'issue': 'Artwork data differs from database',
                        'conflicting_fields': conflict_fields
                    })

                artworks_skipped += 1
            else:
                # New artwork - add it
                data['id'] = str(uuid.uuid4())  # Generate a new random ID
                new_artwork = Artworks(**data)
                db.session.add(new_artwork)
                artworks_added += 1

    # Commit all changes
    db.session.commit()

    print(f"\n🖼️  Artworks Import Summary:")
    print(f"  Artworks added: {artworks_added}")
    print(f"  Artworks skipped (unchanged): {artworks_skipped - len(conflicts)}")
    print(f"  Conflicts detected: {len(conflicts)}")
    print(f"  Note: Artworks in database but not in CSV are preserved (never deleted)")

    # Generate conflict report if needed
    if conflicts:
        generate_conflict_report(csv_file, 'artworks', conflicts)

    # Move the processed file
    if not LOADED_FOLDER.exists():
        LOADED_FOLDER.mkdir(parents=True)
    current_date = datetime.now().strftime('%Y-%m-%d')
    new_file_name = f"{current_date}_{csv_file}"
    shutil.move(str(csv_path), str(LOADED_FOLDER / new_file_name))

    return {'added': artworks_added, 'conflicts': len(conflicts)}


def load_generated_images_from_csv(csv_file='generated_images.csv'):
    """
    Load AI-generated images from CSV file (INCREMENTAL)

    Strategy:
    - Existing images are locked - compare and report conflicts if data differs
    - New images are added
    - NEVER deletes images (database is source of truth)
    """
    csv_path = CSV_FOLDER / csv_file

    if not csv_path.exists():
        print(f"CSV file {csv_file} not found in {CSV_FOLDER}")
        return

    # Build a map of existing images by file_name
    existing_images = {}
    for image in GeneratedImages.query.all():
        existing_images[image.file_name] = image

    conflicts = []
    images_added = 0
    images_skipped = 0

    with open(csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row_num, row in enumerate(reader, start=2):
            # Prepare data for generated image
            data = {
                'model': row['Model'],
                'model_version': int(row['Model Version']) if row['Model Version'].strip() else None,
                'prompt': row['Prompt'],
                'artist_palette': row['Artist Palette'],
                'file_name': row['File Name']
            }

            file_name = data['file_name']

            if file_name in existing_images:
                # Image exists - compare data
                existing_image = existing_images[file_name]
                has_conflict = False
                conflict_fields = {}

                for field_key, csv_value in data.items():
                    db_value = getattr(existing_image, field_key)

                    if csv_value != db_value:
                        has_conflict = True
                        conflict_fields[field_key] = {
                            'db_value': db_value,
                            'csv_value': csv_value
                        }

                if has_conflict:
                    conflicts.append({
                        'row': row_num,
                        'file_name': file_name,
                        'model': data['model'],
                        'issue': 'Generated image data differs from database',
                        'conflicting_fields': conflict_fields
                    })

                images_skipped += 1
            else:
                # New generated image - add it
                data['id'] = str(uuid.uuid4())  # Generate a UUID for the id
                new_image = GeneratedImages(**data)
                db.session.add(new_image)
                images_added += 1

    # Commit all changes
    db.session.commit()

    print(f"\n🎨 Generated Images Import Summary:")
    print(f"  Images added: {images_added}")
    print(f"  Images skipped (unchanged): {images_skipped - len(conflicts)}")
    print(f"  Conflicts detected: {len(conflicts)}")
    print(f"  Note: Images in database but not in CSV are preserved (never deleted)")

    # Generate conflict report if needed
    if conflicts:
        generate_conflict_report(csv_file, 'generated_images', conflicts)

    # Move the processed file
    if not LOADED_FOLDER.exists():
        LOADED_FOLDER.mkdir(parents=True)
    current_date = datetime.now().strftime('%Y-%m-%d')
    new_file_name = f"{current_date}_{csv_file}"
    shutil.move(str(csv_path), str(LOADED_FOLDER / new_file_name))

    return {'added': images_added, 'conflicts': len(conflicts)}


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("Artworks ETL Script")
        print("=" * 50)

        print("\n1. Loading artworks from CSV...")
        load_artworks_from_csv()

        print("\n2. Loading generated images from CSV...")
        load_generated_images_from_csv()

        print("\n" + "=" * 50)
        print("Artworks ETL Complete!")
