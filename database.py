import csv
import pandas as pd
import requests as tmdb
import json

headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIwNzFiYjA1MjIxZTdjYTgzZDE0NzJlOGY2YmYwODJhMSIsInN1YiI6IjVjYTY4ZTUzYzNhMzY4M2IxZGFhNWZhMCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.POFEGXZ3PU_3WjxTxJZ7bVpqqHutbVwTtnD5fF1cUsM"
}

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
    movie_ratings = pd.read_csv('movie_ratings.csv')

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

# Save data from csvs to a website specific csv that serves as the database.
def save_movie_data():
    boredom_killer = pd.read_csv('Boredom Killer - Movies.csv')
    boredom_killer.dropna(subset=['TMDB ID'], inplace=True)
    boredom_killer['TMDB ID'] = boredom_killer['TMDB ID'].apply(pd.to_numeric, errors='coerce').astype('float64')
    boredom_killer.drop(columns=['Source'], inplace=True)

    # Commented out to avoid timeout errors
    #for index, row in boredom_killer.iterrows():
    #    boredom_killer['Image'] = get_tmdb_poster(boredom_killer['TMDB ID'])

    movie_ratings = update_movie_ratings()

    try:
        current_database = pd.read_csv('Boredest Killer.csv')
    except FileNotFoundError:
        current_database = pd.DataFrame({'TMDB ID': []})

    boredom_killer.set_index('TMDB ID', inplace=True)
    movie_ratings.set_index('TMDB ID', inplace=True)
    current_database.set_index('TMDB ID', inplace=True)

    # Don't think this works the way I want it to
    new_database = boredom_killer.combine_first(movie_ratings)
    new_database = new_database.combine_first(current_database)

    # Reset the index of the current database dataframe
    current_database.reset_index(inplace=True)

    final_column_order = ['TMDB ID', 'IMDB ID', 'Movie', 'Year', 'Plex Status', 'Collections', 'Tags', 'Posters', 
                          'Matt', 'Andrew', 'Griffin', 'Gabe', 'Ice', 'Dan']
    current_database = current_database[final_column_order]

    # Save the updated current database dataframe back to the file
    current_database.to_csv('Boredest Killer.csv', index=False)

    return current_database


def movie_analytics():
    current_database = pd.read_csv('Boredest Killer.csv')

    analysis_df = current_database.copy()

    analysis_df['Collections'] = analysis_df['Collections'].str.split('|')
    analysis_df = analysis_df.explode('Collections')

    # Group by 'Collections' and calculate mean, count, and standard deviation for 'Matt'
    analytics = analysis_df.groupby('Collections')['Matt'].agg(['mean', 'count', 'std'])

    return analytics
