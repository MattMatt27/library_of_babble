import csv
import pandas as pd
import requests as tmdb
from urllib.parse import quote
import json
import psycopg2

headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIwNzFiYjA1MjIxZTdjYTgzZDE0NzJlOGY2YmYwODJhMSIsInN1YiI6IjVjYTY4ZTUzYzNhMzY4M2IxZGFhNWZhMCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.POFEGXZ3PU_3WjxTxJZ7bVpqqHutbVwTtnD5fF1cUsM"
}

def connect_to_database():
    conn = psycopg2.connect(
        dbname='library_of_babble',  # Updated to use the correct database name
        user='postgres',              # Your PostgreSQL username
        password='postgres',          # Your PostgreSQL password
        host='localhost'
    )
    cursor = conn.cursor()
    return conn, cursor

def query_postgres_movies():
    cursor.execute("SELECT * FROM Movies_Ref")
    movies = cursor.fetchall()

# TMDB API Calls
def query_tmdb_for_id(raw_title, year):
    encoded_title = quote(raw_title)
    url = "https://api.themoviedb.org/3/search/movie?query=" + encoded_title
    response = tmdb.get(url, headers=headers)
    if response.status_code == 200:
        json_data = response.json()
        first_result_id = json_data['results'][0]['id']
        return first_result_id
    else:
        return ''

def get_tmdb_poster(id):
    url = "https://api.themoviedb.org/3/search/movie/" + str(id)
    response = tmdb.get(url, headers=headers)
    if response.status_code == 200:
        json_data = response.json()
        poster_path = json_data['results'][0]['poster_path']
        image_url = "https://image.tmdb.org/t/p/original/" + poster_path
        return image_url
    else:
        return ''

# Helper to add TMDB IDs (and hopefully eventually images) to the movie_ratings csv import
def update_movie_ratings():
    movie_ratings = pd.read_csv('data/movie_ratings.csv')

    tmdb_ids = []

    # This seems to cause timeout errors-- They likely dont want users scraping images
    for index, row in movie_ratings.iterrows():
        tmdb_id = query_tmdb_for_id(row['Movie'], row['Year'])
        tmdb_ids.append(tmdb_id)

    movie_ratings['TMDB ID'] = tmdb_ids
    movie_ratings.dropna(subset=['TMDB ID'], inplace=True)
    movie_ratings['TMDB ID'] = movie_ratings['TMDB ID'].apply(pd.to_numeric, errors='coerce').astype('float64')
    movie_ratings.drop(columns=['Letterboxd URI', 'Date'], inplace=True)
    movie_ratings['Matt'] *= 2 

    return movie_ratings

def merge_movie_data():
    # Your existing movie_ratings update logic here...
    movie_ratings = update_movie_ratings()

    # Your existing save_movie_data logic here...
    boredom_killer = pd.read_csv('Boredom Killer - Movies.csv')
    boredom_killer.dropna(subset=['TMDB ID'], inplace=True)
    boredom_killer['TMDB ID'] = boredom_killer['TMDB ID'].apply(pd.to_numeric, errors='coerce').astype('float64')
    boredom_killer.drop(columns=['Source', 'Unnamed: 9'], inplace=True)
    boredom_killer.rename(columns={'Plex Status': 'Plex_Status'}, inplace=True)

    # Merge the data frames on TMDB ID
    merged_data = boredom_killer.merge(movie_ratings, on='TMDB ID', how='left', suffixes=('', '_ratings'))

    # Retain non-null values from '_ratings' columns and drop '_ratings' columns
    for column in merged_data.columns:
        if '_ratings' in column:
            orig_column = column.replace('_ratings', '')
            merged_data[orig_column] = merged_data[column].combine_first(merged_data[orig_column])
            merged_data.drop(column, axis=1, inplace=True)

    return merged_data

# Save data from csvs to a website specific csv that serves as the database.
def save_movies_to_database(merged_data, conn, cursor):
    for index, row in merged_data.iterrows():
        try:
            cursor.execute("""
                INSERT INTO Movies_Ref (TMDB_ID, IMDB_ID, Movie, Year, Director, Plex_Status, 
                                        Collections, Tags, Posters, Matt, Andrew, Griffin, 
                                        Gabe, Ice, Dan)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (TMDB_ID) DO UPDATE SET
                IMDB_ID = COALESCE(EXCLUDED.IMDB_ID, Movies_Ref.IMDB_ID),
                Movie = COALESCE(EXCLUDED.Movie, Movies_Ref.Movie),
                Year = COALESCE(EXCLUDED.Year, Movies_Ref.Year),
                Director = COALESCE(EXCLUDED.Director, Movies_Ref.Director),
                Plex Status = COALESCE(EXCLUDED.Plex_Status, Movies_Ref.Plex_Status),
                Collections = COALESCE(EXCLUDED.Collections, Movies_Ref.Collections),
                Tags = COALESCE(EXCLUDED.Tags, Movies_Ref.Tags),
                Posters = COALESCE(EXCLUDED.Posters, Movies_Ref.Posters),
                Matt = COALESCE(EXCLUDED.Matt, Movies_Ref.Matt),
                Andrew = COALESCE(EXCLUDED.Andrew, Movies_Ref.Andrew),
                Griffin = COALESCE(EXCLUDED.Griffin, Movies_Ref.Griffin),
                Gabe = COALESCE(EXCLUDED.Gabe, Movies_Ref.Gabe),
                Ice = COALESCE(EXCLUDED.Ice, Movies_Ref.Ice),
                Dan = COALESCE(EXCLUDED.Dan, Movies_Ref.Dan)
                """, (
                row['TMDB ID'], row['IMDB ID'], row['Movie'], row['Year'], row['Director'], row['Plex Status'],
                row['Collections'], row['Tags'], row['Posters'], row['Matt'], row['Andrew'], row['Griffin'],
                row['Gabe'], row['Ice'], row['Dan']
            ))
            conn.commit() # Commit each insert
        except psycopg2.Error as e:
            print("Error: Could not upsert data into the database", e)
            conn.rollback() # Rollback in case of any error

    try:
        conn, cursor = connect_to_database()
        save_movies_to_database()(merged_data, conn, cursor)
    except psycopg2.Error as e:
        print("Error: Could not connect to the database", e)
    finally:
        cursor.close()
        conn.close()

def movie_analytics():
    current_database = pd.read_csv('Boredest Killer.csv')

    analysis_df = current_database.copy()

    analysis_df['Collections'] = analysis_df['Collections'].str.split('|')
    analysis_df = analysis_df.explode('Collections')

    # Group by 'Collections' and calculate mean, count, and standard deviation for 'Matt'
    analytics = analysis_df.groupby('Collections')['Matt'].agg(['mean', 'count', 'std'])

    return analytics
