import csv
from pathlib import Path
import shutil
import uuid
import requests
from datetime import datetime
from collections import defaultdict

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

def load_book_quotes_from_csv(db, BookQuote):
    csv_file = 'book_quotes.csv'
    csv_path = csv_folder / csv_file
    
    if not csv_path.exists():
        print(f"CSV file {csv_file} not found in {csv_folder}")
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
                        
                        # Try to convert page number to integer, use None if not possible
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
                
                # If we got here without errors, we've found the right encoding
                break
                
        except UnicodeDecodeError:
            # Try the next encoding
            print(f"Failed to open with {encoding} encoding, trying next...")
            continue
        except Exception as e:
            print(f"Unexpected error opening file with {encoding} encoding: {e}")
            continue
    else:
        # This executes if the loop didn't break - meaning no encoding worked
        print("Could not read the file with any of the attempted encodings")
        return
    
    # Move the processed file
    if not loaded_folder.exists():
        loaded_folder.mkdir(parents=True)
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    new_file_name = f"{current_date}_{csv_file}"
    shutil.move(str(csv_path), str(loaded_folder / new_file_name))

def get_book_cover_image_openlibrary(isbn):
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if f"ISBN:{isbn}" in data:
            book_data = data[f"ISBN:{isbn}"]
            if "cover" in book_data and "large" in book_data["cover"]:
                return book_data["cover"]["large"]
    return None

def load_goodreads_data_into_books(db, Books, Reviews, Collections, csv_file):
    csv_path = csv_folder / csv_file
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            existing_book = Books.query.filter_by(id=int(row['Book Id'])).first()
            
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

            # Check if the cover image URL field exists
            # cover_image_url = get_book_cover_image_openlibrary(row['ISBN13']) if row['ISBN13'] else None

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
                # Preserve my_rating, my_review, and private_notes
                preserved_fields = {
                    'title': existing_book.title,
                    'author': existing_book.author,
                    'original_publication_year': existing_book.original_publication_year,
                    'my_rating': existing_book.my_rating,
                    'my_review': existing_book.my_review,
                    'private_notes': existing_book.private_notes,
                    'bookshelves': existing_book.bookshelves,
                    'cover_image_url': existing_book.cover_image_url
                }
                
                # Update all other fields
                for key, value in data.items():
                    setattr(existing_book, key, value)
                
                # Restore preserved fields
                for key, value in preserved_fields.items():
                    setattr(existing_book, key, value)
                
                db.session.add(existing_book)
            else:
                data['id'] = int(row['Book Id'])
                record = Books(**data)
                db.session.add(record)
            
            # Handle review data if it exists
            book_id = int(row['Book Id'])
            if (row['My Rating'].strip() or row['My Review'].strip()) and row['Date Read'].strip():
                # Check if review already exists with the same date
                existing_review = Reviews.query.filter_by(
                    item_type='Book',
                    item_id=str(book_id),
                    date_reviewed=row['Date Read']
                ).first()
                
                if not existing_review:
                    # Create new review - no existing review with this date
                    review = Reviews(
                        item_type='Book',
                        item_id=str(book_id),
                        rating=my_rating,
                        review_text=row['My Review'],
                        date_reviewed=row['Date Read']
                    )
                    db.session.add(review)
                # else:
                    # Update the existing review with this date
                    # if my_rating is not None:  # Only update if rating is provided
                    #     existing_review.rating = my_rating
                    # if row['My Review'].strip():  # Only update if review text is provided
                    #     existing_review.review_text = row['My Review']
                    
            
            # Handle bookshelves/collections data
            excluded_bookshelves = ['to-read', 'currently-reading', 'books-on-tape']
            if row['Bookshelves'].strip():
                bookshelf_list = row['Bookshelves'].split(',')
                
                # Get existing collections for this book
                existing_collections = set(
                    collection.collection_name for collection in 
                    Collections.query.filter_by(item_type='Book', item_id=str(book_id)).all()
                )
                
                # Add new collections without deleting existing ones
                for bookshelf_name in bookshelf_list:
                    bookshelf_name = bookshelf_name.strip()
                    if bookshelf_name and bookshelf_name not in excluded_bookshelves:
                        # Only add if it doesn't already exist
                        if bookshelf_name not in existing_collections:
                            collection = Collections(
                                collection_name=bookshelf_name,
                                item_type='Book',
                                item_id=str(book_id)
                            )
                            db.session.add(collection)

        db.session.commit()

    if not loaded_folder.exists():
        loaded_folder.mkdir(parents=True)

    current_date = datetime.now().strftime('%Y-%m-%d')
    new_file_name = f"{current_date}_{csv_file}"
    shutil.move(str(csv_path), str(loaded_folder / new_file_name))

def load_boredom_killer_into_tvshows(db, TVShows, Reviews, Collections):
    csv_file = 'Boredom Killer - TV.csv'
    csv_path = csv_folder / csv_file
    
    # Get all existing TV show TVDB IDs
    existing_shows = {tvshow.tvdb_id: tvshow for tvshow in TVShows.query.all()}
    
    # Set to store TVDB IDs of shows in the CSV
    csv_shows = {}
    duplicate_count = 0
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row_number, row in enumerate(reader, start=2):  # start=2 because row 1 is headers
            tvdb_id = row['TVDB ID'].strip()
            
            # Skip rows with null or empty TVDB ID
            if not tvdb_id or not row['Year']:
                continue
            
            # Check for duplicates
            if tvdb_id in csv_shows:
                duplicate_count += 1
                print(f"Row {row_number}: Duplicate TVDB ID found: {tvdb_id}. Keeping the latest entry.")
            
            # Prepare data for TV show
            data = {
                'tvdb_id': tvdb_id,
                'imdb_id': row['IMDB ID'].strip() if row['IMDB ID'] else None,
                'title': row['TV Show'].strip(),
                'year': int(row['Year']) if row['Year'].strip().isdigit() else None,
                # 'language': row['Language'].strip() if row['Language'] else None,
                'cover_image_url': row['Poster Image'].strip() if row['Poster Image'] else None,
                'collections': f"{row['Collections']}|{row['Tags']}".strip('|') if row['Collections'] or row['Tags'] else None,
                'status': row['Plex Status'].strip() if row['Plex Status'] else None
            }
            
            # Store the latest data for this TVDB ID
            csv_shows[tvdb_id] = data
    
    # Process the deduplicated data
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
    
    # Move the processed file
    if not loaded_folder.exists():
        loaded_folder.mkdir(parents=True)
    current_date = datetime.now().strftime('%Y-%m-%d')
    new_file_name = f"{current_date}_{csv_file}"
    shutil.move(str(csv_path), str(loaded_folder / new_file_name))

def load_boredom_killer_into_movies(db, Movies, Reviews, Collections):
    csv_file = 'Boredom Killer - Movies.csv'
    csv_path = csv_folder / csv_file
    
    # Get all existing movie TMDb IDs
    existing_movies = {movie.tmdb_id: movie for movie in Movies.query.all()}
    
    # Set to store TMDb IDs of movies in the CSV
    csv_movies = {}
    duplicate_count = 0
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row_number, row in enumerate(reader, start=2):  # start=2 because row 1 is headers
            tmdb_id = row['TMDB ID'].strip()
            
            # Skip rows with null or empty TMDB ID
            if not tmdb_id or not row['Year']:
                continue
            
            # Check for duplicates
            if tmdb_id in csv_movies:
                duplicate_count += 1
                print(f"Row {row_number}: Duplicate TMDB ID found: {tmdb_id}. Keeping the latest entry.")
            
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
    
    # Process the deduplicated data
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
    
    # Move the processed file
    if not loaded_folder.exists():
        loaded_folder.mkdir(parents=True)
    current_date = datetime.now().strftime('%Y-%m-%d')
    new_file_name = f"{current_date}_{csv_file}"
    shutil.move(str(csv_path), str(loaded_folder / new_file_name))

def load_letterboxd_data_into_movies(db, Movies, Reviews):
    ratings_path = letterboxd_folder / 'ratings.csv'
    reviews_path = letterboxd_folder / 'reviews.csv'
    
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
    for (title, year), data in combined_data.items():
        # Sort ratings by letterboxd_id (as a proxy for recency, since we don't have dates)
        ratings = sorted(data['ratings'], key=lambda x: x['letterboxd_id'], reverse=True) if data['ratings'] else []
        # Sort reviews by date_watched in descending order
        reviews = sorted(data['reviews'], key=lambda x: x['date_watched'], reverse=True) if data['reviews'] else []
        
        # Use the most recent rating
        my_rating = ratings[0]['my_rating'] if ratings else None
        date_watched = reviews[0]['date_watched'] if reviews else None
        
        # Prioritize letterboxd_id from ratings
        letterboxd_id = ratings[0]['letterboxd_id'] if ratings else (reviews[0]['letterboxd_id'] if reviews else None)
        
        # Format reviews
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
            
            # Update the Reviews table if review doesn't already exist
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
        else:
            # Print out the name and year of the movie not found in the database
            print(f"Movie not found in database: {title} ({year})")
    
    db.session.commit()
    
    # Move processed files
    if not loaded_folder.exists():
        loaded_folder.mkdir(parents=True)
    current_date = datetime.now().strftime('%Y-%m-%d')
    new_folder_name = f"{current_date}_{letterboxd_folder.name}"
    shutil.move(str(letterboxd_folder), str(loaded_folder / new_folder_name))

# def load_letterboxd_data_into_movies(db, model_class):
#     ratings_path = letterboxd_folder / 'ratings.csv'
#     reviews_path = letterboxd_folder / 'reviews.csv'
#     with open(ratings_path, 'r', newline='', encoding='utf-8') as file:
#         reader = csv.DictReader(file)
#         for row in reader:
#             letterboxd_id = row['Letterboxd URI'].replace('https://boxd.it/', '')
#             existing_movie = model_class.query.filter_by(id=letterboxd_id).first()
#             if existing_movie:
#                 continue

#             data = {
#                 'id': letterboxd_id,
#                 'title': row['Name'],
#                 'year': row['Year'],
#                 'my_rating': row['Rating']
#                 # Leave all other columns Null
#             }

#             record = model_class(**data)
#             db.session.add(record)
#         db.session.commit()

#     with open(reviews_path, 'r', newline='', encoding='utf-8') as file:
#         reader = csv.DictReader(file)
#         for row in reader:
#             existing_movie = model_class.query.filter_by(title=row['Name'], year=row['Year']).first()
#             if existing_movie:
#                 # Update the existing movie record
#                 existing_movie.my_review = row['Review']
#                 # existing_movie.collections = row['Tags']
#                 try:
#                     existing_movie.date_watched = parse_date(row['Watched Date'])
#                 except ValueError as e:
#                     print(e)
#                 db.session.add(existing_movie)
#             else:
#                 # Print out the name, year pair if the movie does not exist
#                 print(f"Movie not found in database: {row['Name']}, {row['Year']}")
#         db.session.commit()

#     if not loaded_folder.exists():
#         loaded_folder.mkdir(parents=True)
#     current_date = datetime.now().strftime('%Y-%m-%d')
#     new_folder_name = f"{current_date}_{letterboxd_folder.name}"
#     shutil.move(str(letterboxd_folder), str(loaded_folder / new_folder_name))

def load_artworks_data(db, model_class):
    csv_file = 'artworks.csv'
    csv_path = csv_folder / csv_file
    
    # Get all existing artwork IDs
    existing_artwork_ids = set(artwork.id for artwork in model_class.query.all())
    
    # Set to store IDs of artworks in the CSV
    csv_artwork_ids = set()
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Check if artwork already exists
            existing_artwork = model_class.query.filter_by(
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
            else:
                # Create new artwork record
                data['id'] = str(uuid.uuid4())  # Generate a new random ID
                new_artwork = model_class(**data)
                db.session.add(new_artwork)
                csv_artwork_ids.add(data['id'])
    
    # Remove artworks not in the CSV
    artworks_to_remove = existing_artwork_ids - csv_artwork_ids
    for artwork_id in artworks_to_remove:
        artwork_to_remove = model_class.query.get(artwork_id)
        if artwork_to_remove:
            db.session.delete(artwork_to_remove)
    
    # Commit all changes
    db.session.commit()
    
    # Move the processed file
    if not loaded_folder.exists():
        loaded_folder.mkdir(parents=True)
    current_date = datetime.now().strftime('%Y-%m-%d')
    new_file_name = f"{current_date}_{csv_file}"
    shutil.move(str(csv_path), str(loaded_folder / new_file_name))

def load_generated_images_data(db, model_class):
    csv_file = 'generated_images.csv'
    csv_folder = Path('data/staging')
    loaded_folder = Path('data/loaded')
    csv_path = csv_folder / csv_file

    # Get all existing generated image IDs
    existing_image_ids = set(image.id for image in model_class.query.all())

    # Set to store IDs of generated images in the CSV
    csv_image_ids = set()

    with open(csv_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Check if generated image already exists
            existing_image = model_class.query.filter_by(
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
            else:
                # Create new generated image record
                data['id'] = str(uuid.uuid4())  # Generate a UUID for the id
                new_image = model_class(**data)
                db.session.add(new_image)
                csv_image_ids.add(data['id'])

    # Remove generated images not in the CSV
    images_to_remove = existing_image_ids - csv_image_ids
    for image_id in images_to_remove:
        image_to_remove = model_class.query.get(image_id)
        if image_to_remove:
            db.session.delete(image_to_remove)

    # Commit all changes
    db.session.commit()
    
    # Move the processed file
    if not loaded_folder.exists():
        loaded_folder.mkdir(parents=True)
    current_date = datetime.now().strftime('%Y-%m-%d')
    new_file_name = f"{current_date}_{csv_file}"
    shutil.move(str(csv_path), str(loaded_folder / new_file_name))