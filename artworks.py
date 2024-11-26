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

def normalize_year(year):
    """
    Convert century values to the start of the century (e.g., '20th Century' -> 1900).
    Other values are returned as-is.
    """
    # Check if the year is in "Nth Century" format
    century_match = re.match(r"(\d+)(st|nd|rd|th)\s+Century", str(year), re.IGNORECASE)
    if century_match:
        century = int(century_match.group(1))  # Extract the numeric part
        return (century - 1) * 100  # Return the start of the century

    # If it's not a century, return the year as an integer
    try:
        return int(year)
    except ValueError:
        return None  # Return None if the year is invalid or unknown


def get_approved_artworks_from_db2(page=1, per_page=100, sort_order='asc', start_date=None, end_date=None, artist_filter=None):
    """
    Fetch artworks from the database with pagination, filtering, and sorting.

    Args:
        page (int): The current page number.
        per_page (int): The number of items per page.
        sort_order (str): Sort order for the `year` field ('asc' or 'desc').
        start_date (int, optional): Start year for filtering.
        end_date (int, optional): End year for filtering.
        artist_filter (list, optional): List of artists to include.

    Returns:
        tuple: A tuple of (artworks, total_pages).
    """
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT artist FROM artworks WHERE site_approved = 1")
    all_artists = [row[0] for row in cursor.fetchall()]

    # Base query
    query_old = """
        SELECT 
            id, 
            title, 
            artist, 
            year, 
            file_name, 
            series, 
            series_id, 
            medium, 
            location,
            CASE 
                WHEN year LIKE '%th Century%' THEN 
                    (CAST(SUBSTR(year, 1, INSTR(year, 'th') - 1) AS INTEGER) - 1) * 100
                WHEN year LIKE '%st Century%' THEN 
                    (CAST(SUBSTR(year, 1, INSTR(year, 'st') - 1) AS INTEGER) - 1) * 100
                WHEN year LIKE '%nd Century%' THEN 
                    (CAST(SUBSTR(year, 1, INSTR(year, 'nd') - 1) AS INTEGER) - 1) * 100
                WHEN year LIKE '%rd Century%' THEN 
                    (CAST(SUBSTR(year, 1, INSTR(year, 'rd') - 1) AS INTEGER) - 1) * 100
                ELSE CAST(year AS INTEGER)
            END AS normalized_year
        FROM artworks 
        WHERE site_approved = 1
    """

    query = """
    SELECT 
        id, 
        title, 
        artist, 
        year, 
        file_name, 
        series, 
        series_id, 
        medium, 
        location,
        CASE 
            -- Handle ranges like "1850–1875"
            WHEN instr(year, '–') > 0 AND year NOT LIKE '%BCE%' AND year NOT LIKE '%CE%' THEN 
                CAST(substr(year, instr(year, '–') + 1) AS INTEGER)
            
            -- Handle ranges with BCE/CE like "664–332 BCE"
            WHEN instr(year, '–') > 0 AND year LIKE '%BCE%' THEN 
                -CAST(substr(year, instr(year, '–') + 1, instr(year || ' ', ' BCE') - instr(year, '–') - 1) AS INTEGER)
            WHEN instr(year, '–') > 0 AND year LIKE '%CE%' THEN 
                CAST(substr(year, instr(year, '–') + 1, instr(year || ' ', ' CE') - instr(year, '–') - 1) AS INTEGER)
            
            -- Handle single years with BCE/CE like "500 CE"
            WHEN year LIKE '%BCE' THEN 
                -CAST(replace(year, ' BCE', '') AS INTEGER)
            WHEN year LIKE '%CE' THEN 
                CAST(replace(year, ' CE', '') AS INTEGER)
            
            -- Handle centuries like "19th Century"
            WHEN year LIKE '%th Century' THEN 
                CAST(substr(year, 1, instr(year, 'th') - 1) AS INTEGER) * 100
            
            -- Handle centuries with BCE like "5th Century BCE"
            WHEN year LIKE '%th Century BCE' THEN 
                -CAST(substr(year, 1, instr(year, 'th') - 1) AS INTEGER) * 100
            
            -- Handle multi-century ranges like "15-16th Century"
            WHEN year LIKE '%-%th Century' THEN 
                CAST(substr(year, instr(year, '-') + 1, instr(year || ' ', 'th Century') - instr(year, '-') - 1) AS INTEGER) * 100
            
            -- Handle BCE to CE ranges like "1st Century BCE - 1st Century CE"
            WHEN year LIKE '%BCE - %CE' THEN 
                CAST(substr(year, instr(year, '-') + 2, instr(year || ' ', ' CE') - instr(year, '-') - 2) AS INTEGER) * 100

            -- Handle normal year values like "1875"
            WHEN year GLOB '[0-9]*' THEN 
                CAST(year AS INTEGER)

            -- Default case if no pattern matches
            ELSE NULL
        END AS normalized_year
    FROM artworks 
    WHERE site_approved = 1
    """

    params = []

    # Apply artist filter
    if artist_filter:
        placeholders = ', '.join(['?'] * len(artist_filter))
        query += f' AND artist IN ({placeholders})'
        params.extend(artist_filter)

    # Apply date range filter
    if start_date:
        query += ' AND normalized_year >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND normalized_year <= ?'
        params.append(end_date)

    # Apply sorting
    if sort_order == "asc":
        query += " ORDER BY normalized_year ASC"
    elif sort_order == "desc":
        query += " ORDER BY normalized_year DESC"
    elif sort_order == "random":
        query += " ORDER BY RANDOM()"

    # Count total rows for pagination
    count_query = f'SELECT COUNT(*) FROM ({query})'
    total_items = cursor.execute(count_query, params).fetchone()[0]

    # Calculate total pages
    total_pages = (total_items + per_page - 1) // per_page

    # Apply pagination
    offset = (page - 1) * per_page
    query += ' LIMIT ? OFFSET ?'
    params.extend([per_page, offset])

    # Fetch paginated results
    cursor.execute(query, params)
    rows = cursor.fetchall()

    # Process results
    artworks = []
    for row in rows:
        normalized_year = normalize_year(row[3])
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

    return artworks, total_pages, all_artists