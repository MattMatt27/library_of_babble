"""
Movies ETL Script
Loads movie data from Boredom Killer CSV and Letterboxd exports
"""
import csv
import sys
from pathlib import Path
from datetime import datetime
import shutil
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app import create_app
from app.extensions import db
from app.movies.models import Movies
from app.collections.models import Reviews, Collections

# Configure paths
CSV_FOLDER = Path('data/staging/')
LETTERBOXD_FOLDER = Path('data/staging/letterboxd/')
LOADED_FOLDER = Path('data/loaded/')


def parse_date(date_str):
    """Parse date from various formats"""
    for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Date format for '{date_str}' is not recognized")


def load_boredom_killer_movies(csv_file='Boredom Killer - Movies.csv'):
    """
    Load movies from Boredom Killer CSV

    Expected CSV columns:
    - TMDB ID
    - IMDB ID
    - Letterboxd ID
    - Movie
    - Director(s)
    - Year
    - Language
    - Image (cover image URL)
    - Collections
    - Tags
    - Plex Status
    """
    csv_path = CSV_FOLDER / csv_file

    if not csv_path.exists():
        print(f"CSV file {csv_file} not found in {CSV_FOLDER}")
        return

    # Get all existing movie TMDb IDs
    existing_movies = {movie.tmdb_id: movie for movie in Movies.query.all()}

    # Store movies by TMDB ID (deduplicate)
    csv_movies = {}
    duplicate_count = 0

    with open(csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row_number, row in enumerate(reader, start=2):
            tmdb_id = row['TMDB ID'].strip()

            # Skip rows with null or empty TMDB ID
            if not tmdb_id or not row['Year']:
                continue

            # Check for duplicates
            if tmdb_id in csv_movies:
                duplicate_count += 1
                print(f"Row {row_number}: Duplicate TMDB ID {tmdb_id}. Keeping latest entry.")

            # Prepare data for movie
            data = {
                'tmdb_id': tmdb_id,
                'imdb_id': row['IMDB ID'].strip() if row['IMDB ID'] else None,
                'letterboxd_id': row['Letterboxd ID'].strip() if row['Letterboxd ID'] else None,
                'title': row['Movie'].strip(),
                'director': row['Director(s)'].strip() if row['Director(s)'] else None,
                'year': int(row['Year']) if row['Year'].strip().isdigit() else None,
                'language': row['Language'].strip() if row['Language'] else None,
                'cover_image_url': row['Image'].strip() if row['Image'] else None,
                'collections': f"{row['Collections']}|{row['Tags']}".strip('|') if row['Collections'] or row['Tags'] else None,
                'status': row['Plex Status'].strip() if row['Plex Status'] else None
            }

            # Store the latest data for this TMDB ID
            csv_movies[tmdb_id] = data

    if duplicate_count > 0:
        print(f"Found {duplicate_count} duplicates - kept latest entries")

    # Process the deduplicated data
    movies_added = 0
    movies_updated = 0

    for tmdb_id, data in csv_movies.items():
        if tmdb_id in existing_movies:
            # Update existing movie
            existing_movie = existing_movies[tmdb_id]

            # Preserve fields that shouldn't be overwritten
            preserved_fields = {
                'my_rating': existing_movie.my_rating,
                'my_review': existing_movie.my_review,
                'date_watched': existing_movie.date_watched
            }

            for key, value in data.items():
                if value is not None:
                    setattr(existing_movie, key, value)

            # Restore preserved fields
            for key, value in preserved_fields.items():
                setattr(existing_movie, key, value)

            movies_updated += 1

            # Update collections based on the new collections data
            if 'collections' in data and data['collections']:
                # Get existing collections
                existing_collections = set(
                    collection.collection_name for collection in
                    Collections.query.filter_by(item_type='Movie', item_id=tmdb_id).all()
                )

                # Add new collections without deleting existing ones
                collection_list = data['collections'].split('|')
                for collection_name in collection_list:
                    collection_name = collection_name.strip()
                    if collection_name and collection_name not in existing_collections:
                        collection = Collections(
                            collection_name=collection_name,
                            item_type='Movie',
                            item_id=tmdb_id
                        )
                        db.session.add(collection)
        else:
            # Create new movie record
            new_movie = Movies(**data)
            db.session.add(new_movie)
            movies_added += 1

            # Add collections if available
            if 'collections' in data and data['collections']:
                collection_list = data['collections'].split('|')
                for collection_name in collection_list:
                    collection_name = collection_name.strip()
                    if collection_name:
                        collection = Collections(
                            collection_name=collection_name,
                            item_type='Movie',
                            item_id=tmdb_id
                        )
                        db.session.add(collection)

    # Commit all changes
    db.session.commit()
    print(f"Movies loaded: {movies_added} added, {movies_updated} updated")

    # Move the processed file
    if not LOADED_FOLDER.exists():
        LOADED_FOLDER.mkdir(parents=True)
    current_date = datetime.now().strftime('%Y-%m-%d')
    new_file_name = f"{current_date}_{csv_file}"
    shutil.move(str(csv_path), str(LOADED_FOLDER / new_file_name))


def load_letterboxd_export():
    """
    Load movie ratings and reviews from Letterboxd export

    Expected folder structure in data/staging/letterboxd/:
    - ratings.csv (Name, Year, Letterboxd URI, Rating)
    - reviews.csv (Name, Year, Letterboxd URI, Review, Watched Date)
    """
    ratings_path = LETTERBOXD_FOLDER / 'ratings.csv'
    reviews_path = LETTERBOXD_FOLDER / 'reviews.csv'

    if not ratings_path.exists() or not reviews_path.exists():
        print(f"Letterboxd export files not found in {LETTERBOXD_FOLDER}")
        print("Expected: ratings.csv and reviews.csv")
        return

    # Combine ratings and reviews
    combined_data = defaultdict(lambda: {'ratings': [], 'reviews': []})

    # Process ratings
    with open(ratings_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            key = (row['Name'], row['Year'])
            combined_data[key]['ratings'].append({
                'letterboxd_id': row['Letterboxd URI'].replace('https://boxd.it/', ''),
                'my_rating': row['Rating']
            })

    # Process reviews
    with open(reviews_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            key = (row['Name'], row['Year'])
            combined_data[key]['reviews'].append({
                'letterboxd_id': row['Letterboxd URI'].replace('https://boxd.it/', ''),
                'review': row['Review'],
                'date_watched': parse_date(row['Watched Date'])
            })

    # Process combined data
    reviews_added = 0
    movies_not_found = 0

    for (title, year), data in combined_data.items():
        # Sort ratings by letterboxd_id (as proxy for recency)
        ratings = sorted(data['ratings'], key=lambda x: x['letterboxd_id'], reverse=True) if data['ratings'] else []
        # Sort reviews by date_watched descending
        reviews = sorted(data['reviews'], key=lambda x: x['date_watched'], reverse=True) if data['reviews'] else []

        # Use the most recent rating
        my_rating = ratings[0]['my_rating'] if ratings else None
        date_watched = reviews[0]['date_watched'] if reviews else None

        # Prioritize letterboxd_id from ratings
        letterboxd_id = ratings[0]['letterboxd_id'] if ratings else (reviews[0]['letterboxd_id'] if reviews else None)

        # Format reviews (combine multiple reviews with dates)
        if len(reviews) > 1:
            sorted_reviews = sorted(reviews, key=lambda x: x['date_watched'], reverse=True)
            my_review = "\n\n".join([
                f"{review['date_watched'].strftime('%m/%d/%Y')}\n{review['review']}"
                for review in sorted_reviews
            ])
        elif reviews:
            my_review = reviews[0]['review']
        else:
            my_review = None

        # Check if movie exists in database
        existing_movie = Movies.query.filter_by(letterboxd_id=letterboxd_id).first()
        if existing_movie:
            # Update existing movie - only if fields are empty
            if not existing_movie.my_rating and my_rating:
                existing_movie.my_rating = my_rating
            if not existing_movie.my_review and my_review:
                existing_movie.my_review = my_review
            if not existing_movie.date_watched and date_watched:
                existing_movie.date_watched = date_watched.strftime('%Y-%m-%d')

            db.session.add(existing_movie)

            # Update the Reviews table
            if date_watched and (my_rating or my_review):
                # Check if review already exists
                existing_review = Reviews.query.filter_by(
                    item_type='Movie',
                    item_id=existing_movie.tmdb_id,
                    date_reviewed=date_watched.strftime('%Y-%m-%d')
                ).first()

                if existing_review:
                    # Only update if fields are empty
                    if not existing_review.rating and my_rating:
                        existing_review.rating = int(float(my_rating)) if my_rating else None
                    if not existing_review.review_text and my_review:
                        existing_review.review_text = my_review
                else:
                    # Create new review
                    review = Reviews(
                        item_type='Movie',
                        item_id=existing_movie.tmdb_id,
                        rating=int(float(my_rating)) if my_rating else None,
                        review_text=my_review,
                        date_reviewed=date_watched.strftime('%Y-%m-%d')
                    )
                    db.session.add(review)
                    reviews_added += 1
        else:
            # Movie not found in database
            print(f"Movie not found in database: {title} ({year})")
            movies_not_found += 1

    db.session.commit()
    print(f"Letterboxd data loaded: {reviews_added} reviews added")
    if movies_not_found > 0:
        print(f"Note: {movies_not_found} movies not found in database (need to import Boredom Killer first)")

    # Move processed files
    if not LOADED_FOLDER.exists():
        LOADED_FOLDER.mkdir(parents=True)
    current_date = datetime.now().strftime('%Y-%m-%d')
    new_folder_name = f"{current_date}_{LETTERBOXD_FOLDER.name}"
    shutil.move(str(LETTERBOXD_FOLDER), str(LOADED_FOLDER / new_folder_name))


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("Movies ETL Script")
        print("=" * 50)

        # Load Boredom Killer movies
        print("\n1. Loading Boredom Killer movies...")
        load_boredom_killer_movies()

        # Load Letterboxd export
        print("\n2. Loading Letterboxd export...")
        print("(Requires letterboxd folder with ratings.csv and reviews.csv)")
        load_letterboxd_export()

        print("\n" + "=" * 50)
        print("Movies ETL Complete!")
