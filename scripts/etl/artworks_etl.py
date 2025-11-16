"""
Artworks ETL Script
Loads artworks and AI-generated images from CSV files
"""
import csv
import sys
import uuid
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


def load_artworks_from_csv(csv_file='artworks.csv'):
    """
    Load artworks from CSV file

    Expected CSV columns:
    - Title
    - Artist
    - After
    - Year
    - Series
    - Series ID
    - file_name
    - site_approved
    - Location
    - Description
    - Medium
    - Tags

    Note: This function syncs with the CSV - artworks not in the CSV will be removed
    """
    csv_path = CSV_FOLDER / csv_file

    if not csv_path.exists():
        print(f"CSV file {csv_file} not found in {CSV_FOLDER}")
        return

    # Get all existing artwork IDs
    existing_artwork_ids = set(artwork.id for artwork in Artworks.query.all())

    # Set to store IDs of artworks in the CSV
    csv_artwork_ids = set()
    artworks_added = 0
    artworks_updated = 0

    with open(csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Check if artwork already exists
            existing_artwork = Artworks.query.filter_by(
                title=row['Title'],
                artist=row['Artist'],
                year=row['Year'] if row['Year'].strip() else None,
                series=row['Series'],
                series_id=int(row['Series ID']) if row['Series ID'].strip() else None
            ).first()

            # Prepare data for new artwork
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

            if existing_artwork:
                # Update existing artwork
                for key, value in data.items():
                    setattr(existing_artwork, key, value)
                csv_artwork_ids.add(existing_artwork.id)
                artworks_updated += 1
            else:
                # Create new artwork record
                data['id'] = str(uuid.uuid4())  # Generate a new random ID
                new_artwork = Artworks(**data)
                db.session.add(new_artwork)
                csv_artwork_ids.add(data['id'])
                artworks_added += 1

    # Remove artworks not in the CSV
    artworks_to_remove = existing_artwork_ids - csv_artwork_ids
    artworks_removed = 0
    for artwork_id in artworks_to_remove:
        artwork_to_remove = Artworks.query.get(artwork_id)
        if artwork_to_remove:
            db.session.delete(artwork_to_remove)
            artworks_removed += 1

    # Commit all changes
    db.session.commit()
    print(f"Artworks loaded: {artworks_added} added, {artworks_updated} updated, {artworks_removed} removed")

    # Move the processed file
    if not LOADED_FOLDER.exists():
        LOADED_FOLDER.mkdir(parents=True)
    current_date = datetime.now().strftime('%Y-%m-%d')
    new_file_name = f"{current_date}_{csv_file}"
    shutil.move(str(csv_path), str(LOADED_FOLDER / new_file_name))


def load_generated_images_from_csv(csv_file='generated_images.csv'):
    """
    Load AI-generated images from CSV file

    Expected CSV columns:
    - Model
    - Model Version
    - Prompt
    - Artist Palette
    - File Name

    Note: This function syncs with the CSV - images not in the CSV will be removed
    """
    csv_path = CSV_FOLDER / csv_file

    if not csv_path.exists():
        print(f"CSV file {csv_file} not found in {CSV_FOLDER}")
        return

    # Get all existing generated image IDs
    existing_image_ids = set(image.id for image in GeneratedImages.query.all())

    # Set to store IDs of generated images in the CSV
    csv_image_ids = set()
    images_added = 0
    images_updated = 0

    with open(csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Check if generated image already exists
            existing_image = GeneratedImages.query.filter_by(
                file_name=row['File Name']
            ).first()

            # Prepare data for new or existing generated image
            data = {
                'model': row['Model'],
                'model_version': int(row['Model Version']) if row['Model Version'].strip() else None,
                'prompt': row['Prompt'],
                'artist_palette': row['Artist Palette'],
                'file_name': row['File Name']
            }

            if existing_image:
                # Update existing generated image
                for key, value in data.items():
                    setattr(existing_image, key, value)
                csv_image_ids.add(existing_image.id)
                images_updated += 1
            else:
                # Create new generated image record
                data['id'] = str(uuid.uuid4())  # Generate a UUID for the id
                new_image = GeneratedImages(**data)
                db.session.add(new_image)
                csv_image_ids.add(data['id'])
                images_added += 1

    # Remove generated images not in the CSV
    images_to_remove = existing_image_ids - csv_image_ids
    images_removed = 0
    for image_id in images_to_remove:
        image_to_remove = GeneratedImages.query.get(image_id)
        if image_to_remove:
            db.session.delete(image_to_remove)
            images_removed += 1

    # Commit all changes
    db.session.commit()
    print(f"Generated images loaded: {images_added} added, {images_updated} updated, {images_removed} removed")

    # Move the processed file
    if not LOADED_FOLDER.exists():
        LOADED_FOLDER.mkdir(parents=True)
    current_date = datetime.now().strftime('%Y-%m-%d')
    new_file_name = f"{current_date}_{csv_file}"
    shutil.move(str(csv_path), str(LOADED_FOLDER / new_file_name))


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
