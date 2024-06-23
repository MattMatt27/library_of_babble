import csv
from datetime import datetime
from urllib.parse import quote
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

# Function to get the five most recently watched movies
def get_recently_watched_movies():
    movies = watched_movies_from_csv()
    # Convert date strings to datetime objects
    for movie in movies:
        if movie['date_watched']:  # Check if date_watched is not empty
            movie['date_watched'] = datetime.strptime(movie['date_watched'], '%m/%d/%Y')
        #movie['title'] = truncate_title(movie['title'])
    # Sort the movies by date watched in descending order
    sorted_movies = sorted(movies, key=lambda x: x.get('date_watched', datetime.min), reverse=True)
    return sorted_movies[:7]