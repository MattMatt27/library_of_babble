from flask import Flask, render_template
from books import get_recently_read_books, read_books_from_csv
from movies import get_recently_watched_movies, watched_movies_from_csv
from database import movie_analytics

import pandas as pd
from urllib.parse import quote
from datetime import datetime
import csv
import re

app = Flask(__name__)

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

@app.route('/matt-ranking')
def matt_ranking():
    #current_database = movie_analytics()
    # Sort the DataFrame by 'Matt' column in descending order
    #sorted_df = current_database.sort_values(by=['Matt', 'TMDB ID'], ascending=False)
    # Convert the sorted DataFrame to HTML table
    #table_html = sorted_df.to_html(index=False)

    average_ratings = movie_analytics()

    # Sort the DataFrame by mean rating in descending order
    sorted_ratings = average_ratings.sort_values(by='mean', ascending=False)

    return render_template('matt_ranking.html', ratings=sorted_ratings)

if __name__ == '__main__':
    app.run(debug=True)