import csv
import re
from datetime import datetime

# Clean book titles by dropping text after the first colon (usually a subtitle)
def truncate_title(title):
    index = title.find(':')
    return title[:index] if index != -1 else title

# Book CSV Parsing
def read_books_from_csv():
    books = []
    with open('book_reviews.csv', 'r', encoding='utf-8') as file:
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

# Function to get the five most recently read books
def get_recently_read_books():
    books = read_books_from_csv()
    # Convert date strings to datetime objects
    for book in books:
        if book['date_read']:  # Check if date_read is not empty
            book['date_read'] = datetime.strptime(book['date_read'], '%m/%d/%Y')
        book['title'] = truncate_title(book['title'])
    # Sort the books by date read in descending order
    sorted_books = sorted(books, key=lambda x: x.get('date_read', datetime.min), reverse=True)
    return sorted_books[:5]