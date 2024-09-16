import csv
from datetime import datetime
from urllib.parse import quote
import sqlite3
import pandas as pd
import requests as tmdb

# Movie CSV Parsing
def watched_movies_from_csv():
    movies = []
    with open('data/movie_reviews.csv', 'r', encoding='utf-8') as file:
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

def read_movies_from_db():
    movies = []
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()

    # Execute a SELECT query to fetch all books
    cursor.execute('SELECT tmdb_id, title, director, year, cover_image_url, date_watched, my_rating, my_review FROM movies WHERE date_watched IS NOT NULL')
    rows = cursor.fetchall()

    for row in rows:

        movie = {
            'id': row[0], 
            'title': row[1],
            'director': row[2], 
            'year': row[3], 
            'cover_image_url': row[4] if row[4] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_watched': row[5], 
            'my_rating': str(row[6]), 
            'my_review': row[7] 
        }
        movies.append(movie)

    # Proper date handling should be done eventually
    # for movie in movies:
    #     if movie['date_watched']: 
    #         movie['date_watched_dt'] = datetime.strptime(movie['date_watched'], '%Y-%m-%d')

    movies.sort(key=lambda x: x['date_watched'], reverse=True)

    conn.close() 

    return movies

# Function to get the five most recently watched movies
def get_recently_watched_movies():
    movies = read_movies_from_db()
    # Convert date strings to datetime objects
    for movie in movies:
        if movie['date_watched']:  # Check if date_watched is not empty
            movie['date_watched'] = datetime.strptime(movie['date_watched'], '%Y-%m-%d')
        #movie['title'] = truncate_title(movie['title'])
    # Sort the movies by date watched in descending order
    sorted_movies = sorted(movies, key=lambda x: x.get('date_watched', datetime.min), reverse=True)
    return sorted_movies[:10]


def get_movies_from_collection(collection):
    collection_movies = []
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()

    # Fetch books where 'matts-recommended-fiction' is in bookshelves
    query = """
        SELECT tmdb_id, title, director, year, cover_image_url, date_watched, my_rating, my_review 
        FROM movies
        WHERE collections LIKE ?
    """

    # Execute the query with the parameter
    cursor.execute(query, (f'%{collection}%',))

    rows = cursor.fetchall()

    for row in rows:

        movie = {
            'id': row[0], 
            'title': row[1],
            'director': row[2], 
            'year': row[3], 
            'cover_image_url': row[4] if row[4] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_watched': row[5], 
            'my_rating': str(row[6]), 
            'my_review': row[7] 
        }
        collection_movies.append(movie)

    sorted_movies = sorted(collection_movies, key=lambda x: x.get('year', datetime.min), reverse=False)
    # Close connection
    conn.close()

    return sorted_movies