"""
Books ETL Script
Loads book data from Goodreads CSV exports and book quotes

INCREMENTAL IMPORT STRATEGY:
- Database is source of truth
- Read books (read=1) are locked - only report conflicts if data differs
- Unread books can be updated (progression to read status)
- New books are added
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
from app.books.models import Books, BookQuote
from app.common.models import Reviews, Collections

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


def parse_date(date_str):
    """Parse date from various formats"""
    for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Date format for '{date_str}' is not recognized")


def load_book_quotes_from_csv(csv_file='book_quotes.csv'):
    """
    Load book quotes from CSV file

    Expected CSV columns:
    - Goodreads ID
    - Title
    - Quote
    - Page Number
    """
    csv_path = CSV_FOLDER / csv_file

    if not csv_path.exists():
        print(f"CSV file {csv_file} not found in {CSV_FOLDER}")
        return

    # Track existing quotes to avoid duplicates
    existing_quotes = {}
    for quote in BookQuote.query.all():
        quote_key = (quote.book_id, quote.quote_text)
        existing_quotes[quote_key] = quote

    quotes_added = 0
    quotes_updated = 0

    # Try different encodings
    encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'windows-1252']

    for encoding in encodings_to_try:
        try:
            with open(csv_path, 'r', newline='', encoding=encoding) as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        book_id = row['Goodreads ID'].strip()
                        quote_text = row['Quote'].strip()

                        # Skip empty quotes or missing book IDs
                        if not book_id or not quote_text:
                            continue

                        # Try to convert page number to integer
                        try:
                            page_number = int(row['Page Number']) if row['Page Number'].strip() else None
                        except ValueError:
                            page_number = None

                        # Check if this quote already exists
                        quote_key = (book_id, quote_text)
                        if quote_key in existing_quotes:
                            # Update existing quote if page number has changed
                            existing_quote = existing_quotes[quote_key]
                            if existing_quote.page_number != page_number and page_number is not None:
                                existing_quote.page_number = page_number
                                db.session.add(existing_quote)
                                quotes_updated += 1
                        else:
                            # Create new quote
                            new_quote = BookQuote(
                                book_id=book_id,
                                quote_text=quote_text,
                                page_number=page_number
                            )
                            db.session.add(new_quote)
                            quotes_added += 1

                    except Exception as e:
                        print(f"Error processing quote: {e}")
                        continue

                db.session.commit()
                print(f"Book quotes loaded using {encoding} encoding: {quotes_added} added, {quotes_updated} updated")
                break

        except UnicodeDecodeError:
            print(f"Failed to open with {encoding} encoding, trying next...")
            continue
        except Exception as e:
            print(f"Unexpected error opening file with {encoding} encoding: {e}")
            continue
    else:
        print("Could not read the file with any of the attempted encodings")
        return

    # Move the processed file
    if not LOADED_FOLDER.exists():
        LOADED_FOLDER.mkdir(parents=True)

    current_date = datetime.now().strftime('%Y-%m-%d')
    new_file_name = f"{current_date}_{csv_file}"
    shutil.move(str(csv_path), str(LOADED_FOLDER / new_file_name))


def reset_sequence(table_name, id_column='id'):
    """Reset PostgreSQL sequence to match the current max ID"""
    # Whitelist allowed table names to prevent SQL injection
    ALLOWED_TABLES = {'books', 'reviews', 'collections', 'book_quotes'}
    ALLOWED_COLUMNS = {'id'}

    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Table {table_name} not in whitelist")
    if id_column not in ALLOWED_COLUMNS:
        raise ValueError(f"Column {id_column} not in whitelist")

    try:
        # Safe to use f-string now that table_name is validated against whitelist
        # Note: PostgreSQL doesn't support parameters for table/column names in this context
        db.session.execute(db.text(
            f"SELECT setval(pg_get_serial_sequence('{table_name}', '{id_column}'), "
            f"COALESCE((SELECT MAX({id_column}) FROM {table_name}), 1), true);"
        ))
        db.session.commit()
        print(f"  ✓ Reset {table_name} sequence")
    except Exception as e:
        print(f"  ⚠️  Could not reset {table_name} sequence: {e}")
        db.session.rollback()


def load_goodreads_export(csv_file):
    """
    Load books from Goodreads CSV export (INCREMENTAL)

    Strategy:
    - Read books (read=1) are locked: compare and report conflicts if different
    - Unread books can be updated (progression to read)
    - New books are added
    """
    csv_path = CSV_FOLDER / csv_file

    # Reset sequences to prevent ID conflicts
    print("\nResetting database sequences...")
    reset_sequence('reviews')
    reset_sequence('collections')

    conflicts = []
    books_added = 0
    books_updated = 0
    books_skipped = 0
    reviews_added = 0
    collections_added = 0

    batch_size = 100  # Commit every 100 books
    row_count = 0

    # Use no_autoflush to prevent premature flushes that cause constraint violations
    with db.session.no_autoflush:
        with open(csv_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row_num, row in enumerate(reader, start=2):
                row_count += 1
                book_id = int(row['Book Id'])
                existing_book = Books.query.filter_by(id=book_id).first()

                # Parse integer fields
                try:
                    number_of_pages = int(row['Number of Pages']) if row['Number of Pages'].strip() else None
                except ValueError:
                    number_of_pages = None

                try:
                    my_rating = int(row['My Rating']) if row['My Rating'].strip() else None
                except ValueError:
                    my_rating = None

                try:
                    original_publication_year = int(row['Original Publication Year']) if row['Original Publication Year'].strip() else None
                except ValueError:
                    original_publication_year = None

                csv_read_status = 1 if row['Exclusive Shelf'].lower() == 'read' else 0

                # Clean review text - remove <br> tags
                clean_review = row['My Review'].replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
                clean_notes = row['Private Notes'].replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')

                data = {
                    'id': book_id,
                    'title': row['Title'],
                    'author': row['Author'],
                    'additional_authors': row['Additional Authors'],
                    'isbn': row['ISBN'],
                    'isbn13': row['ISBN13'],
                    'my_rating': my_rating,
                    'average_rating': float(row['Average Rating']),
                    'publisher': row['Publisher'],
                    'number_of_pages': number_of_pages,
                    'original_publication_year': original_publication_year,
                    'date_read': row['Date Read'],
                    'date_added': row['Date Added'],
                    'bookshelves': row['Bookshelves'],
                    'read': csv_read_status,
                    'my_review': clean_review,
                    'private_notes': clean_notes,
                    'read_count': int(row['Read Count']),
                    'owned_copies': int(row['Owned Copies']),
                    'cover_image_url': ''
                }

                if existing_book:
                    if existing_book.read == 1:
                        # Book is marked as read in database - it's locked
                        # Check if CSV data differs from database
                        has_conflict = False
                        conflict_fields = {}

                        for key, csv_value in data.items():
                            if key == 'id':
                                continue
                            db_value = getattr(existing_book, key)

                            # Normalize for comparison
                            if csv_value != db_value:
                                has_conflict = True
                                conflict_fields[key] = {
                                    'db_value': db_value,
                                    'csv_value': csv_value
                                }

                        if has_conflict:
                            # Report conflict
                            conflicts.append({
                                'row': row_num,
                                'book_id': book_id,
                                'title': row['Title'],
                                'author': row['Author'],
                                'issue': 'Read book data differs from database',
                                'conflicting_fields': conflict_fields
                            })

                        books_skipped += 1
                    else:
                        # Book is not read yet - allow update (progression)
                        for key, value in data.items():
                            setattr(existing_book, key, value)
                        db.session.add(existing_book)
                        books_updated += 1
                else:
                    # New book - add it
                    record = Books(**data)
                    db.session.add(record)
                    books_added += 1

                # Handle review data (incremental)
                if (row['My Rating'].strip() or row['My Review'].strip()) and row['Date Read'].strip():
                    # Clean review text - remove <br> tags
                    review_text = row['My Review'].replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')

                    # Check if review already exists (by item and date)
                    existing_review = Reviews.query.filter_by(
                        item_type='Book',
                        item_id=str(book_id),
                        date_reviewed=row['Date Read']
                    ).first()

                    if not existing_review:
                        review = Reviews(
                            item_type='Book',
                            item_id=str(book_id),
                            rating=my_rating,
                            review_text=review_text,
                            date_reviewed=row['Date Read']
                        )
                        db.session.add(review)
                        reviews_added += 1
                    else:
                        # Update existing review if rating or text changed
                        if existing_review.rating != my_rating or existing_review.review_text != review_text:
                            existing_review.rating = my_rating
                            existing_review.review_text = review_text
                            db.session.add(existing_review)

                # Handle bookshelves as collections (incremental)
                if row['Bookshelves'].strip():
                    bookshelves = [shelf.strip() for shelf in row['Bookshelves'].split(',')]
                    for shelf in bookshelves:
                        if not shelf:  # Skip empty shelf names
                            continue

                        existing_collection = Collections.query.filter_by(
                            collection_name=shelf,
                            item_type='Book',
                            item_id=str(book_id)
                        ).first()

                        if not existing_collection:
                            collection = Collections(
                                collection_name=shelf,
                                item_type='Book',
                                item_id=str(book_id)
                            )
                            db.session.add(collection)
                            collections_added += 1

                # Commit in batches to avoid autoflush issues
                if row_count % batch_size == 0:
                    db.session.commit()

    # Final commit for remaining records
    db.session.commit()

    print(f"\n📚 Goodreads Import Summary:")
    print(f"  Books added: {books_added}")
    print(f"  Books updated: {books_updated}")
    print(f"  Books skipped (read, unchanged): {books_skipped - len(conflicts)}")
    print(f"  Conflicts detected: {len(conflicts)}")
    print(f"  Reviews added: {reviews_added}")
    print(f"  Collections added: {collections_added}")

    # Generate conflict report if needed
    if conflicts:
        generate_conflict_report(csv_file, 'goodreads', conflicts)

    return {'added': books_added, 'updated': books_updated, 'conflicts': len(conflicts)}


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Import books from Goodreads CSV export')
    parser.add_argument('csv_file', nargs='?', help='Path to Goodreads CSV file')
    parser.add_argument('--use-transaction', action='store_true',
                       help='Use database transaction (rollback on failure)')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        print("Books ETL Script")
        print("=" * 50)

        try:
            # If using transaction mode, we'll rollback on any error
            if args.use_transaction:
                print("Running in transaction mode (all-or-nothing)")

            # Load Goodreads export
            if args.csv_file:
                print(f"\nLoading Goodreads export from: {args.csv_file}")

                # Handle both absolute paths and filenames
                csv_path = Path(args.csv_file)
                if csv_path.is_absolute():
                    # It's an absolute path (from temp file)
                    # We need to temporarily move it to staging folder
                    import shutil
                    temp_csv = CSV_FOLDER / f"temp_{csv_path.name}"
                    shutil.copy(csv_path, temp_csv)
                    result = load_goodreads_export(temp_csv.name)
                    # Clean up temp file
                    temp_csv.unlink(missing_ok=True)
                else:
                    # It's just a filename in staging folder
                    result = load_goodreads_export(args.csv_file)

                print(f"\nBooks added: {result['added']}")
                print(f"Books updated: {result['updated']}")
                print(f"Conflicts reported: {result['conflicts']}")
            else:
                # Interactive mode
                print("\n1. Loading book quotes...")
                load_book_quotes_from_csv()

                print("\n2. Load Goodreads export")
                csv_file = input("Enter Goodreads CSV filename (or press Enter to skip): ").strip()
                if csv_file:
                    load_goodreads_export(csv_file)

            print("\n" + "=" * 50)
            print("Books ETL Complete!")
            sys.exit(0)

        except Exception as e:
            print(f"\n❌ Error during import: {str(e)}", file=sys.stderr)
            if args.use_transaction:
                print("Rolling back database changes...", file=sys.stderr)
                db.session.rollback()
                print("Database rolled back to previous state.", file=sys.stderr)
            sys.exit(1)
