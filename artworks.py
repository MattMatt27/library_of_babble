import csv
import re
import sqlite3
from datetime import datetime
from urllib.parse import unquote

def get_approved_artworks_from_db():
    artworks = []
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()

    # Execute a SELECT query to fetch all books
    cursor.execute('SELECT id, title, artist, year, file_name, series, series_id, medium, location FROM artworks WHERE site_approved = 1')
    rows = cursor.fetchall()

    for row in rows:

        artwork = {
            'id': row[0], 
            'title': f"{row[1]} ({row[3]})" if row[1] else f"From the {row[5]} series ({row[3]})",
            'artist': unquote(row[2]), 
            'year': row[3], 
            'file_name': unquote(row[4]) if row[4] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg',
            'series': row[5], 
            'series_id': row[6], 
            'medium': row[7],
            'location': row[8] 
        }
        artworks.append(artwork)

    conn.close() 

    return artworks