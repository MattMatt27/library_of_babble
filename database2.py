import csv
from pathlib import Path
import shutil
from datetime import datetime

csv_folder = Path('data/staging/')
letterboxd_folder = Path('data/staging/letterboxd/')
loaded_folder = Path('data/loaded/')

def parse_date(date_str):
    for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Date format for '{date_str}' is not recognized")

def load_goodreads_data_into_books(db, model_class, csv_file):
    csv_path = csv_folder / csv_file
    with open(csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            existing_book = model_class.query.filter_by(id=int(row['Book Id']), read=True).first()
            if existing_book:
                continue
            try:
                number_of_pages = int(row['Number of Pages']) if row['Number of Pages'].strip() else None
            except ValueError:
                number_of_pages = None  # Handle non-numeric or empty strings
            
            try:
                my_rating = int(row['My Rating']) if row['My Rating'].strip() else None
            except ValueError:
                my_rating = None  # Handle non-numeric or empty strings
            
            try:
                original_publication_year = int(row['Original Publication Year']) if row['Original Publication Year'].strip() else None
            except ValueError:
                original_publication_year = None  # Handle non-numeric or empty strings

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
            record = model_class(**data)
            db.session.add(record)
        db.session.commit()

    if not loaded_folder.exists():
        loaded_folder.mkdir(parents=True)
    shutil.move(str(csv_path), str(loaded_folder / csv_file))



def load_letterboxd_data_into_movies(db, model_class):
    ratings_path = letterboxd_folder / 'ratings.csv'
    reviews_path = letterboxd_folder / 'reviews.csv'
    with open(ratings_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            letterboxd_id = row['Letterboxd URI'].replace('https://boxd.it/', '')
            existing_movie = model_class.query.filter_by(id=letterboxd_id).first()
            if existing_movie:
                continue

            data = {
                'id': letterboxd_id,
                'title': row['Name'],
                'year': row['Year'],
                'my_rating': row['Rating']
                # Leave all other columns Null
            }

            record = model_class(**data)
            db.session.add(record)
        db.session.commit()

    with open(reviews_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            existing_movie = model_class.query.filter_by(title=row['Name'], year=row['Year']).first()
            if existing_movie:
                # Update the existing movie record
                existing_movie.my_review = row['Review']
                existing_movie.collections = row['Tags']
                try:
                    existing_movie.date_watched = parse_date(row['Watched Date'])
                except ValueError as e:
                    print(e)
                db.session.add(existing_movie)
            else:
                # Print out the name, year pair if the movie does not exist
                print(f"Movie not found in database: {row['Name']}, {row['Year']}")
        db.session.commit()

    if not loaded_folder.exists():
        loaded_folder.mkdir(parents=True)
    shutil.move(str(letterboxd_folder), str(loaded_folder / letterboxd_folder.name))