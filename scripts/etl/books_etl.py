"""
Books ETL Script
Loads book data from Goodreads CSV exports and book quotes
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
from app.books.models import Books, BookQuote
from app.collections.models import Reviews, Collections

# Configure paths
CSV_FOLDER = Path('data/staging/')
LOADED_FOLDER = Path('data/loaded/')


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


def load_goodreads_export(csv_file):
    """
    Load books from Goodreads CSV export

    This function loads book data and creates review records
    """
    csv_path = CSV_FOLDER / csv_file

    with open(csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            existing_book = Books.query.filter_by(id=int(row['Book Id'])).first()

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

            data = {
                'id': int(row['Book Id']),
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
                'read': 1 if row['Exclusive Shelf'].lower() == 'read' else 0,
                'my_review': row['My Review'],
                'private_notes': row['Private Notes'],
                'read_count': int(row['Read Count']),
                'owned_copies': int(row['Owned Copies']),
                'cover_image_url': ''
            }

            if existing_book:
                # Update book preserving certain fields
                for key, value in data.items():
                    setattr(existing_book, key, value)
                db.session.add(existing_book)
            else:
                record = Books(**data)
                db.session.add(record)

            # Handle review data
            book_id = int(row['Book Id'])
            if (row['My Rating'].strip() or row['My Review'].strip()) and row['Date Read'].strip():
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
                        review_text=row['My Review'],
                        date_reviewed=row['Date Read']
                    )
                    db.session.add(review)

            # Handle bookshelves as collections
            if row['Bookshelves'].strip():
                bookshelves = [shelf.strip() for shelf in row['Bookshelves'].split(',')]
                for shelf in bookshelves:
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

    db.session.commit()
    print(f"Goodreads data loaded from {csv_file}")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("Books ETL Script")
        print("=" * 50)

        # Load book quotes
        print("\n1. Loading book quotes...")
        load_book_quotes_from_csv()

        # Load Goodreads export (prompt for filename)
        print("\n2. Load Goodreads export")
        csv_file = input("Enter Goodreads CSV filename (or press Enter to skip): ").strip()
        if csv_file:
            load_goodreads_export(csv_file)

        print("\n" + "=" * 50)
        print("Books ETL Complete!")
