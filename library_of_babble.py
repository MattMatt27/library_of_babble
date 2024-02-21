from flask import Flask, render_template
from datetime import datetime
import csv
import re

app = Flask(__name__)

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

# Function to read data from the CSV file
def read_books_from_csv_new():
    books = {}
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
                    'reviews': []  # Initialize an empty list for reviews
                }
                # Add review details to the book's list of reviews
                review = {
                    'date_read': row['Date Read'],
                    'my_rating': row['My Rating'],
                    'my_review': row['My Review']
                }
                book['reviews'].append(review)
                # Add the book to the dictionary using the book ID as the key
                if book['id'] in books:
                    books[book['id']]['reviews'].append(review)
                else:
                    books[book['id']] = book
    return list(books.values())  # Return a list of books from the dictionary


def truncate_title(title):
    # Truncate title at the first colon
    index = title.find(':')
    return title[:index] if index != -1 else title

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
    # Take the first five books
    return sorted_books[:5]



# Movie CSV Parsing
def watched_movies_from_csv():
    movies = []
    with open('movie_reviews.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Name'] and row['Watched Date']:
                image = row['Movie Poster'] if row['Movie Poster'] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg'
                movie = {
                    'title': row['Name'],
                    'director': row['Director'],
                    'year': row['Year'],
                    'cover_image_url': image,
                    'date_watched': row['Watched Date'],
                    'my_rating': row['Rating'],
                    'my_review': row['Review']
                }
                movies.append(movie)
    return movies

# Function to get the five most recently watched movies
def get_recently_watched_movies():
    movies = watched_movies_from_csv()
    # Convert date strings to datetime objects
    for movie in movies:
        if movie['date_watched']:  # Check if date_watched is not empty
            movie['date_watched'] = datetime.strptime(movie['date_watched'], '%m/%d/%Y')
        movie['title'] = truncate_title(movie['title'])
    # Sort the movies by date watched in descending order
    sorted_movies = sorted(movies, key=lambda x: x.get('date_watched', datetime.min), reverse=True)
    return sorted_movies[:5]



# Display
@app.route('/')
def home():
    recently_read_books = get_recently_read_books()
    recently_watched_movies = get_recently_watched_movies()
    return render_template('index.html', recently_read_books=recently_read_books, recently_watched_movies=recently_watched_movies)

@app.route('/books')
def books():
    books_data = read_books_from_csv()
    return render_template('books.html', books=books_data)

@app.route('/book/<int:book_id>')
def book(book_id):
    # ToDo: Add handling to grab multiple reviews if they appear in the data
    books = read_books_from_csv()
    book_details = None
    reviews = []

    for book in books:
        if book['id'] == str(book_id):
            book_details = book
            book['title'] = truncate_title(book['title'])
            reviews.append({'date_read': book['date_read'], 'my_rating': book['my_rating'], 'my_review': book['my_review']})
    
    quotes = []
    with open('book_quotes.csv', 'r', encoding='iso-8859-1') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Goodreads ID'] == str(book_id):
                quotes.append({'text': row['Quote'], 'page_number': row['Page Number']})

    return render_template('book.html', book=book_details, reviews=reviews, quotes=quotes)


@app.route('/movies')
def movies():
    movies_data = watched_movies_from_csv()
    return render_template('movies.html', movies=movies_data)

if __name__ == '__main__':
    app.run(debug=True)