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

    # Join Books with Reviews to get the latest review data
    query = """
    SELECT b.id, b.title, b.author, b.original_publication_year, b.cover_image_url, 
           r.date_reviewed, r.rating, r.review_text
    FROM books b
    JOIN reviews r ON r.item_id = CAST(b.id AS TEXT) AND r.item_type = 'Book'
    WHERE r.rating > 0 AND r.date_reviewed != ""
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()

    for row in rows:
        book = {
            'id': row[0], 
            'title': re.sub(r'\s*[\[({][^\[\](){}]*[\])}]|:.*', '', row[1]),
            'author': row[2], 
            'publication_year': row[3], 
            'cover_image_url': row[4] if row[4] else 'https://theprairiesbookreview.com/wp-content/uploads/2023/11/cover-not-availble-image.jpg',
            'date_read': row[5], 
            'my_rating': str(row[6]), 
            'my_review': row[7] 
        }
        books.append(book)

    books.sort(key=lambda x: x['date_read'], reverse=True)
    conn.close() 
    return books

def get_recently_read_books():
    """Get recently read books using the Reviews table"""
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()
    
    query = """
    SELECT b.id, b.title, b.author, b.original_publication_year, b.cover_image_url, 
           r.date_reviewed, r.rating, r.review_text
    FROM books b
    JOIN reviews r ON r.item_id = CAST(b.id AS TEXT) AND r.item_type = 'Book'
    WHERE r.rating > 0
    ORDER BY r.date_reviewed DESC
    LIMIT 10
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    books = []
    for row in rows:
        book = {
            'id': row[0], 
            'title': re.sub(r'\s*[\[({][^\[\](){}]*[\])}]|:.*', '', row[1]),
            'author': row[2], 
            'publication_year': row[3], 
            'cover_image_url': row[4] if row[4] else 'https://theprairiesbookreview.com/wp-content/uploads/2023/11/cover-not-availble-image.jpg',
            'date_read': row[5], 
            'my_rating': str(row[6]), 
            'my_review': row[7] 
        }
        books.append(book)
    
    conn.close()
    return books

def get_books_from_bookshelf(bookshelf):
    """Get books from a specific bookshelf using the Collections table"""
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()
    
    query = """
    SELECT b.id, b.title, b.author, b.original_publication_year, b.cover_image_url, 
           r.date_reviewed, r.rating, r.review_text
    FROM books b
    JOIN collections c ON c.item_id = CAST(b.id AS TEXT) AND c.item_type = 'Book'
    LEFT JOIN reviews r ON r.item_id = CAST(b.id AS TEXT) AND r.item_type = 'Book'
    WHERE c.collection_name = ?
    """
    
    cursor.execute(query, (bookshelf,))
    rows = cursor.fetchall()
    
    books = []
    for row in rows:
        book = {
            'id': row[0], 
            'title': re.sub(r'\s*[\[({][^\[\](){}]*[\])}]|:.*', '', row[1]),
            'author': row[2], 
            'publication_year': row[3], 
            'cover_image_url': row[4] if row[4] else 'https://theprairiesbookreview.com/wp-content/uploads/2023/11/cover-not-availble-image.jpg',
            'date_read': row[5], 
            'my_rating': str(row[6]) if row[6] else '0', 
            'my_review': row[7] 
        }
        books.append(book)
    
    # Sort by publication year
    sorted_books = sorted(books, key=lambda x: x.get('publication_year', 0), reverse=False)
    conn.close()
    return sorted_books