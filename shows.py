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
    
    query = """
    SELECT s.tvdb_id, s.title, s.year, r.rating, s.date_finished, 
           r.date_reviewed, r.review_text, s.cover_image_url
    FROM tv_shows s
    JOIN reviews r ON r.item_id = s.tvdb_id AND r.item_type = 'TVShow'
    WHERE r.date_reviewed IS NOT NULL
    """
    
    cursor.execute(query)
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

def get_recently_watched_shows():
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()
    
    query = """
    SELECT s.tvdb_id, s.title, s.year, r.rating, s.date_finished, 
           r.date_reviewed, r.review_text, s.cover_image_url
    FROM tv_shows s
    JOIN reviews r ON r.item_id = s.tvdb_id AND r.item_type = 'TVShow'
    ORDER BY r.date_reviewed DESC
    LIMIT 10
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    shows = []
    for row in rows:
        try:
            last_watched = datetime.strptime(row[5], '%m/%d/%Y')
        except (ValueError, TypeError):
            last_watched = datetime.min
        
        show = {
            'id': row[0], 
            'title': row[1],
            'year': row[2], 
            'cover_image_url': row[7] if row[7] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_finished': row[4], 
            'last_watched': last_watched,
            'my_rating': str(row[3]), 
            'my_review': row[6] 
        }
        shows.append(show)
    
    conn.close()
    return shows

def get_shows_from_collection(collection):
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()
    
    query = """
    SELECT s.tvdb_id, s.title, s.year, r.rating, s.date_finished, 
           r.date_reviewed, r.review_text, s.cover_image_url
    FROM tv_shows s
    JOIN collections c ON c.item_id = s.tvdb_id AND c.item_type = 'TVShow'
    LEFT JOIN reviews r ON r.item_id = s.tvdb_id AND r.item_type = 'TVShow'
    WHERE c.collection_name = ?
    """
    
    cursor.execute(query, (collection,))
    rows = cursor.fetchall()
    
    shows = []
    for row in rows:
        show = {
            'id': row[0], 
            'title': row[1],
            'year': row[2], 
            'cover_image_url': row[7] if row[7] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'date_finished': row[4], 
            'last_watched': row[5],
            'my_rating': str(row[3]) if row[3] else '0', 
            'my_review': row[6] 
        }
        shows.append(show)
    
    conn.close()
    return shows