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
    
    query = """
    SELECT m.tmdb_id, m.title, m.director, m.year, m.cover_image_url, 
           r.date_reviewed, r.rating, r.review_text
    FROM movies m
    JOIN reviews r ON r.item_id = m.tmdb_id AND r.item_type = 'Movie'
    WHERE r.date_reviewed IS NOT NULL
    """
    
    cursor.execute(query)
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

    movies.sort(key=lambda x: x['date_watched'], reverse=True)
    conn.close() 
    return movies

def get_recently_watched_movies():
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()
    
    query = """
    SELECT m.tmdb_id, m.title, m.director, m.year, m.cover_image_url, 
           r.date_reviewed, r.rating, r.review_text
    FROM movies m
    JOIN reviews r ON r.item_id = m.tmdb_id AND r.item_type = 'Movie'
    ORDER BY r.date_reviewed DESC
    LIMIT 10
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    movies = []
    for row in rows:
        try:
            date_watched = datetime.strptime(row[5], '%Y-%m-%d')
        except (ValueError, TypeError):
            date_watched = datetime.min
        
        movie = {
            'id': row[0], 
            'title': row[1],
            'director': row[2], 
            'year': row[3], 
            'cover_image_url': row[4] if row[4] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_watched': date_watched, 
            'my_rating': str(row[6]), 
            'my_review': row[7] 
        }
        movies.append(movie)
    
    conn.close()
    return movies

def get_movies_from_collection(collection):
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()
    
    query = """
    SELECT m.tmdb_id, m.title, m.director, m.year, m.cover_image_url, 
           r.date_reviewed, r.rating, r.review_text
    FROM movies m
    JOIN collections c ON c.item_id = m.tmdb_id AND c.item_type = 'Movie'
    LEFT JOIN reviews r ON r.item_id = m.tmdb_id AND r.item_type = 'Movie'
    WHERE c.collection_name = ?
    """
    
    cursor.execute(query, (collection,))
    rows = cursor.fetchall()
    
    movies = []
    for row in rows:
        movie = {
            'id': row[0], 
            'title': row[1],
            'director': row[2], 
            'year': row[3], 
            'cover_image_url': row[4] if row[4] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_watched': row[5], 
            'my_rating': str(row[6]) if row[6] else '0', 
            'my_review': row[7] 
        }
        movies.append(movie)
    
    sorted_movies = sorted(movies, key=lambda x: x.get('year', 0), reverse=False)
    conn.close()
    return sorted_movies