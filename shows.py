import csv
from datetime import datetime
from urllib.parse import quote
import sqlite3
import pandas as pd
import requests as tmdb


def read_shows_from_db():
    shows = []
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()

    # Execute a SELECT query to fetch all books
    cursor.execute('SELECT tvdb_id, title, year, my_rating, date_finished, last_watched, my_review, cover_image_url FROM tv_shows WHERE last_watched IS NOT NULL')
    rows = cursor.fetchall()

    for row in rows:

        show = {
            'id': row[0], 
            'title': row[1],
            'year': row[2], 
            'cover_image_url': row[7] if row[7] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_finished': row[4], 
            'last_watched': row[5],
            'my_rating': str(row[3]), 
            'my_review': row[6] 
        }
        shows.append(show)

    shows.sort(key=lambda x: x['last_watched'], reverse=True)

    conn.close() 

    return shows

# Function to get the five most recently watched shows
def get_recently_watched_shows():
    shows = read_shows_from_db()
    # Convert date strings to datetime objects
    for show in shows:
        if show['last_watched']:  # Check if last_watched is not empty
            show['last_watched'] = datetime.strptime(show['last_watched'], '%m/%d/%Y')
        #show['title'] = truncate_title(show['title'])
    # Sort the movies by date watched in descending order
    sorted_shows = sorted(shows, key=lambda x: x.get('last_watched', datetime.min), reverse=True)
    return sorted_shows[:10]


def get_shows_from_collection(collection):
    collection_shows = []
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()

    # Fetch books where 'matts-recommended-fiction' is in bookshelves
    query = """
        SELECT tvdb_id, title, year, my_rating, date_finished, my_review, cover_image_url 
        FROM tv_shows
        WHERE collections LIKE ?
    """

    # Execute the query with the parameter
    cursor.execute(query, (f'%{collection}%',))

    rows = cursor.fetchall()

    for row in rows:

        show = {
            'id': row[0], 
            'title': row[1],
            'year': row[2], 
            'cover_image_url': row[6] if row[6] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_finished': row[4], 
            'my_rating': str(row[3]), 
            'my_review': row[5] 
        }
        collection_shows.append(show)

    # Close connection
    conn.close()

    return collection_shows