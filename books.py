import csv
import re
import sqlite3
from datetime import datetime

# Clean book titles by dropping text after the first colon (usually a subtitle)
def truncate_title(title):
    index = title.find(':')
    return title[:index] if index != -1 else title

# Book CSV Parsing
def read_books_from_csv():
    books = []
    with open('data/book_reviews.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Title'] and row['Author']:
                year = row['Original Publication Year'] if row['Original Publication Year'] else row['Year Published']
                title = re.sub(r'\s*[\[({][^\[\](){}]*[\])}]', '', row['Title'])
                image = row['Cover Image URL'] if row['Cover Image URL'] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg'
                book = {
                    'id': row['Book Id'],
                    'title': title,
                    'author': row['Author'],
                    'publication_year': year,
                    'cover_image_url': image,
                    'date_read': row['Date Read'],
                    'my_rating': row['My Rating'],
                    'my_review': row['My Review']
                }
                books.append(book)
    return books

def read_books_from_db():
    books = []
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()

    # Execute a SELECT query to fetch all books
    cursor.execute('SELECT id, title, author, original_publication_year, cover_image_url, date_read, my_rating, my_review FROM books WHERE my_rating > 0 AND date_read != ""')
    rows = cursor.fetchall()

    for row in rows:

        book = {
            'id': row[0], 
            'title': re.sub(r'\s*[\[({][^\[\](){}]*[\])}]|:.*', '', row[1]),
            'author': row[2], 
            'publication_year': row[3], 
            'cover_image_url': row[4] if row[4] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_read': row[5], 
            'my_rating': str(row[6]), 
            'my_review': row[7] 
        }
        books.append(book)

    books.sort(key=lambda x: x['date_read'], reverse=True)

    conn.close() 

    return books

# Function to get the five most recently read books
def get_recently_read_books():
    books = read_books_from_db()
    # Sort the books by date read in descending order
    sorted_books = sorted(books, key=lambda x: x.get('date_read', datetime.min), reverse=True)
    return sorted_books[:10]

def get_books_from_bookshelf(bookshelf):
    bookshelf_books = []
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()

    # Fetch books where 'matts-recommended-fiction' is in bookshelves
    query = """
        SELECT id, title, author, original_publication_year, cover_image_url, date_read, my_rating, my_review 
        FROM books
        WHERE bookshelves LIKE ?
    """

    # Execute the query with the parameter
    cursor.execute(query, (f'%{bookshelf}%',))

    rows = cursor.fetchall()

    for row in rows:

        book = {
            'id': row[0], 
            'title': re.sub(r'\s*[\[({][^\[\](){}]*[\])}]|:.*', '', row[1]),
            'author': row[2], 
            'publication_year': row[3], 
            'cover_image_url': row[4] if row[4] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_read': row[5], 
            'my_rating': str(row[6]), 
            'my_review': row[7] 
        }
        bookshelf_books.append(book)

    sorted_books = sorted(bookshelf_books, key=lambda x: x.get('publication_year', datetime.min), reverse=False)

    # Close connection
    conn.close()

    return sorted_books