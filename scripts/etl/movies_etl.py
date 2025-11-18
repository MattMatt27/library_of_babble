"""
Movies ETL Script
Loads movie data from Boredom Killer CSV and Letterboxd exports

INCREMENTAL IMPORT STRATEGY:
- Database is source of truth
- Watched movies (has date_watched or my_rating) are locked - only report conflicts if data differs
- Unwatched movies can be updated (metadata corrections)
- New movies are added
- Never deletes existing data
"""
import csv
import sys
import json
from pathlib import Path
from datetime import datetime
import shutil
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app import create_app
from app.extensions import db
from app.movies.models import Movies
from app.common.models import Reviews, Collections

# Configure paths
CSV_FOLDER = Path('data/staging/')
LETTERBOXD_FOLDER = Path('data/staging/letterboxd/')
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


def parse_date(date_str):
    """Parse date from various formats"""
    for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Date format for '{date_str}' is not recognized")


def load_boredom_killer_movies(csv_file='Boredom Killer - Movies.csv', csv_folder=None):
    """
    Load movies from Boredom Killer CSV (INCREMENTAL)

    Strategy:
    - Watched movies (has date_watched or my_rating) are locked: compare and report conflicts if different
    - Unwatched movies can be updated (metadata corrections)
    - New movies are added
    """
    folder = Path(csv_folder) if csv_folder else CSV_FOLDER
    csv_path = folder / csv_file

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
            # Handle both 'Movie' (for movies) and 'Documentary' (for documentaries) columns
            title = row.get('Movie') or row.get('Documentary', '')

            data = {
                'tmdb_id': tmdb_id,
                'imdb_id': row['IMDB ID'].strip() if row['IMDB ID'] else None,
                'letterboxd_id': row['Letterboxd ID'].strip() if row['Letterboxd ID'] else None,
                'title': title.strip(),
                'director': row['Director(s)'].strip() if row['Director(s)'] else None,
                'year': int(row['Year']) if row['Year'].strip().isdigit() else None,
                'language': row['Language'].strip() if row['Language'] else None,
                'cover_image_url': row['Image'].strip() if row['Image'] else None,
                'collections': f"{row['Collections']}|{row['Tags']}".strip('|') if row['Collections'] or row['Tags'] else None,
                'status': row['Plex Status'].strip() if row['Plex Status'] else None
            }

            # Store the latest data for this TMDB ID, along with row number
            csv_movies[tmdb_id] = {'data': data, 'row': row_number}

    if duplicate_count > 0:
        print(f"Found {duplicate_count} duplicates - kept latest entries")

    # Process the deduplicated data
    conflicts = []
    movies_added = 0
    movies_updated = 0
    movies_skipped = 0
    collections_added = 0

    for tmdb_id, entry in csv_movies.items():
        data = entry['data']
        row_num = entry['row']

        if tmdb_id in existing_movies:
            existing_movie = existing_movies[tmdb_id]

            # Check if movie is watched (locked)
            is_watched = existing_movie.date_watched or existing_movie.my_rating

            if is_watched:
                # Movie is watched - it's locked
                # Only compare metadata fields (not user-specific fields)
                has_conflict = False
                conflict_fields = {}

                metadata_fields = ['title', 'director', 'year', 'language', 'cover_image_url',
                                   'imdb_id', 'letterboxd_id', 'status']

                for key in metadata_fields:
                    if key in data:
                        csv_value = data[key]
                        db_value = getattr(existing_movie, key)

                        if csv_value != db_value:
                            has_conflict = True
                            conflict_fields[key] = {
                                'db_value': db_value,
                                'csv_value': csv_value
                            }

                if has_conflict:
                    conflicts.append({
                        'row': row_num,
                        'tmdb_id': tmdb_id,
                        'title': data['title'],
                        'director': data['director'],
                        'year': data['year'],
                        'issue': 'Watched movie metadata differs from database',
                        'conflicting_fields': conflict_fields
                    })

                movies_skipped += 1
            else:
                # Movie is not watched - allow metadata update
                for key, value in data.items():
                    if key != 'collections' and value is not None:
                        setattr(existing_movie, key, value)
                db.session.add(existing_movie)
                movies_updated += 1

            # Update collections (always incremental, even for watched movies)
            if data.get('collections'):
                existing_collections = set(
                    collection.collection_name for collection in
                    Collections.query.filter_by(item_type='Movie', item_id=tmdb_id).all()
                )

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
                        collections_added += 1
        else:
            # Create new movie record
            new_movie = Movies(**data)
            db.session.add(new_movie)
            movies_added += 1

            # Add collections if available
            if data.get('collections'):
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
                        collections_added += 1

    # Commit all changes
    db.session.commit()

    print(f"\n🎬 Boredom Killer Movies Import Summary:")
    print(f"  Movies added: {movies_added}")
    print(f"  Movies updated: {movies_updated}")
    print(f"  Movies skipped (watched, unchanged): {movies_skipped - len(conflicts)}")
    print(f"  Conflicts detected: {len(conflicts)}")
    print(f"  Collections added: {collections_added}")

    # Generate conflict report if needed
    if conflicts:
        generate_conflict_report(csv_file, 'boredom_killer_movies', conflicts)

    # Move the processed file (only in interactive mode, not for web uploads)
    if csv_folder is None:
        if not LOADED_FOLDER.exists():
            LOADED_FOLDER.mkdir(parents=True)
        current_date = datetime.now().strftime('%Y-%m-%d')
        new_file_name = f"{current_date}_{csv_file}"
        shutil.move(str(csv_path), str(LOADED_FOLDER / new_file_name))

    return {'added': movies_added, 'updated': movies_updated, 'conflicts': len(conflicts)}


def load_letterboxd_export(letterboxd_folder=None):
    """
    Load movie ratings and reviews from Letterboxd export (INCREMENTAL)

    Strategy:
    - Only updates empty fields in database (database is source of truth)
    - Adds new reviews incrementally
    - Reports movies not found in database
    """
    folder = Path(letterboxd_folder) if letterboxd_folder else LETTERBOXD_FOLDER
    ratings_path = folder / 'ratings.csv'
    reviews_path = folder / 'reviews.csv'

    if not ratings_path.exists() or not reviews_path.exists():
        print(f"Letterboxd export files not found in {folder}")
        print("Expected: ratings.csv and reviews.csv")
        return

    # Combine ratings and reviews
    combined_data = defaultdict(lambda: {'ratings': [], 'reviews': []})

    # Process ratings
    with open(ratings_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            key = (row['Name'], row['Year'])
            # Convert Letterboxd rating to float (0-5 scale)
            rating = None
            if row['Rating']:
                try:
                    rating = float(row['Rating'])
                except (ValueError, TypeError):
                    rating = None

            combined_data[key]['ratings'].append({
                'letterboxd_id': row['Letterboxd URI'].replace('https://boxd.it/', ''),
                'my_rating': rating
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
    movies_updated = 0
    reviews_added = 0
    movies_not_found = []

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
        # Also clean <br> tags from review text
        def clean_br_tags(text):
            """Remove <br> tags and replace with newlines"""
            if not text:
                return text
            return text.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')

        if len(reviews) > 1:
            sorted_reviews = sorted(reviews, key=lambda x: x['date_watched'], reverse=True)
            my_review = "\n\n".join([
                f"{review['date_watched'].strftime('%m/%d/%Y')}\n{clean_br_tags(review['review'])}"
                for review in sorted_reviews
            ])
        elif reviews:
            my_review = clean_br_tags(reviews[0]['review'])
        else:
            my_review = None

        # Check if movie exists in database
        existing_movie = Movies.query.filter_by(letterboxd_id=letterboxd_id).first()
        if existing_movie:
            # Update existing movie - only fill empty fields (database is source of truth)
            updated = False
            if not existing_movie.my_rating and my_rating:
                existing_movie.my_rating = my_rating
                updated = True
            if not existing_movie.my_review and my_review:
                existing_movie.my_review = my_review
                updated = True
            if not existing_movie.date_watched and date_watched:
                existing_movie.date_watched = date_watched.strftime('%Y-%m-%d')
                updated = True

            if updated:
                db.session.add(existing_movie)
                movies_updated += 1

            # Add reviews (incremental)
            if date_watched and (my_rating or my_review):
                existing_review = Reviews.query.filter_by(
                    item_type='Movie',
                    item_id=existing_movie.tmdb_id,
                    date_reviewed=date_watched.strftime('%Y-%m-%d')
                ).first()

                if existing_review:
                    # Only update empty fields
                    if not existing_review.rating and my_rating:
                        existing_review.rating = float(my_rating) if my_rating else None
                    if not existing_review.review_text and my_review:
                        existing_review.review_text = my_review
                else:
                    # Create new review
                    review = Reviews(
                        item_type='Movie',
                        item_id=existing_movie.tmdb_id,
                        rating=float(my_rating) if my_rating else None,
                        review_text=my_review,
                        date_reviewed=date_watched.strftime('%Y-%m-%d')
                    )
                    db.session.add(review)
                    reviews_added += 1
        else:
            # Movie not found in database
            movies_not_found.append({
                'title': title,
                'year': year,
                'letterboxd_id': letterboxd_id
            })

    db.session.commit()

    print(f"\n📽️  Letterboxd Import Summary:")
    print(f"  Movies updated: {movies_updated}")
    print(f"  Reviews added: {reviews_added}")
    print(f"  Movies not found: {len(movies_not_found)}")

    if movies_not_found:
        print(f"\n⚠️  {len(movies_not_found)} movies from Letterboxd not found in database")
        print("   (Import Boredom Killer CSV first to add these movies)")

    # Move processed files (only in interactive mode, not for web uploads)
    if letterboxd_folder is None:
        if not LOADED_FOLDER.exists():
            LOADED_FOLDER.mkdir(parents=True)
        current_date = datetime.now().strftime('%Y-%m-%d')
        new_folder_name = f"{current_date}_{LETTERBOXD_FOLDER.name}"
        shutil.move(str(LETTERBOXD_FOLDER), str(LOADED_FOLDER / new_folder_name))

    return {'updated': movies_updated, 'reviews_added': reviews_added, 'not_found': len(movies_not_found)}


def reset_sequence(table_name):
    """Reset the auto-increment sequence for a table to avoid conflicts"""
    try:
        # For PostgreSQL
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

    parser = argparse.ArgumentParser(description='Movies ETL Script')
    parser.add_argument('file_path', nargs='?', help='Path to CSV file')
    parser.add_argument('--bk-movies', action='store_true', help='Import Boredom Killer Movies CSV')
    parser.add_argument('--bk-docs', action='store_true', help='Import Boredom Killer Documentaries CSV (goes to movies table)')
    parser.add_argument('--letterboxd-ratings', help='Path to Letterboxd ratings.csv')
    parser.add_argument('--letterboxd-reviews', help='Path to Letterboxd reviews.csv')
    parser.add_argument('--reset-letterboxd', action='store_true', help='Reset all existing ratings and reviews before import')
    parser.add_argument('--use-transaction', action='store_true', help='Run in transaction mode with automatic rollback on error')

    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        try:
            # Reset sequences to prevent ID conflicts
            reset_sequence('reviews')
            reset_sequence('collections')

            # Interactive mode (no arguments)
            if not any([args.bk_movies, args.bk_docs, args.letterboxd_ratings]):
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
                sys.exit(0)

            # CLI mode
            if args.use_transaction:
                print("Running in transaction mode - all changes will be rolled back on error")

            # Boredom Killer Movies
            if args.bk_movies:
                if not args.file_path:
                    print("Error: file_path required for --bk-movies")
                    sys.exit(1)

                print(f"Importing Boredom Killer Movies from: {args.file_path}")
                file_path = Path(args.file_path)
                result = load_boredom_killer_movies(file_path.name, csv_folder=str(file_path.parent))

                if result:
                    print(f"Movies added: {result.get('added', 0)}")
                    print(f"Movies updated: {result.get('updated', 0)}")
                    print(f"Conflicts reported: {result.get('conflicts', 0)}")

            # Boredom Killer Documentaries (goes to movies table)
            if args.bk_docs:
                if not args.file_path:
                    print("Error: file_path required for --bk-docs")
                    sys.exit(1)

                print(f"Importing Boredom Killer Documentaries from: {args.file_path}")
                file_path = Path(args.file_path)
                result = load_boredom_killer_movies(file_path.name, csv_folder=str(file_path.parent))

                if result:
                    print(f"Documentaries added: {result.get('added', 0)}")
                    print(f"Documentaries updated: {result.get('updated', 0)}")
                    print(f"Conflicts reported: {result.get('conflicts', 0)}")

            # Letterboxd
            if args.letterboxd_ratings and args.letterboxd_reviews:
                print(f"Importing Letterboxd ratings from: {args.letterboxd_ratings}")
                print(f"Importing Letterboxd reviews from: {args.letterboxd_reviews}")

                # Reset existing ratings and reviews if requested
                if args.reset_letterboxd:
                    print("\n⚠️  Resetting all existing ratings and reviews...")
                    # Clear all ratings, reviews, and date_watched from movies
                    Movies.query.update({
                        Movies.my_rating: None,
                        Movies.my_review: None,
                        Movies.date_watched: None
                    })
                    # Delete all movie reviews
                    Reviews.query.filter_by(item_type='Movie').delete()
                    db.session.commit()
                    print("  ✓ All ratings and reviews cleared")

                # Create temporary letterboxd folder with the files
                import tempfile
                temp_dir = Path(tempfile.mkdtemp())
                letterboxd_temp = temp_dir / 'letterboxd'
                letterboxd_temp.mkdir()

                # Copy files to temp directory
                shutil.copy(args.letterboxd_ratings, letterboxd_temp / 'ratings.csv')
                shutil.copy(args.letterboxd_reviews, letterboxd_temp / 'reviews.csv')

                # Pass the temp folder to the function
                result = load_letterboxd_export(letterboxd_folder=str(letterboxd_temp))

                # Cleanup temp directory
                shutil.rmtree(temp_dir)

                if result:
                    print(f"Movies with ratings added: {result.get('updated', 0)}")
                    print(f"Reviews added: {result.get('reviews_added', 0)}")

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
