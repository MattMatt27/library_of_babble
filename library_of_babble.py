from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from books import get_recently_read_books, read_books_from_csv, truncate_title, read_books_from_db, get_books_from_bookshelf
from music import music_test, generate_monthly_playlists_df, select_playlist, get_tracks_artists, get_site_approved_playlists
from movies import get_recently_watched_movies, read_movies_from_db, get_movies_from_collection
from shows import get_recently_watched_shows, read_shows_from_db, get_shows_from_collection
from pins import get_recently_added_pins, read_pins_from_csv
from alcohol_labels import get_recently_added_labels, read_alc_labels_from_csv
from database import movie_analytics, save_movies_to_database, merge_movie_data, connect_to_database
from database2 import load_goodreads_data_into_books, load_boredom_killer_into_movies, load_boredom_killer_into_tvshows, load_letterboxd_data_into_movies, load_artworks_data, load_generated_images_data
from playlist_parse import parse_and_load_playlists
from artworks import get_approved_artworks_from_db

import pandas as pd
from datetime import datetime, timedelta
import csv
from pathlib import Path
import sqlite3
import re
import os
import random

load_dotenv('ids.env')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio_prd.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)

class Books(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    additional_authors = db.Column(db.String(255))
    isbn = db.Column(db.String(20))
    isbn13 = db.Column(db.String(20))
    my_rating = db.Column(db.Integer)
    average_rating = db.Column(db.Float)
    publisher = db.Column(db.String(100))
    number_of_pages = db.Column(db.Integer)
    original_publication_year = db.Column(db.Integer)
    date_read = db.Column(db.String(20))
    date_added = db.Column(db.String(20))
    bookshelves = db.Column(db.String(255))
    read = db.Column(db.Boolean)
    my_review = db.Column(db.Text)
    private_notes = db.Column(db.Text)
    read_count = db.Column(db.Integer)
    owned_copies = db.Column(db.Integer)
    cover_image_url = db.Column(db.String(255))

class Movies(db.Model):
    tmdb_id = db.Column(db.String, primary_key=True)
    imdb_id = db.Column(db.String)
    letterboxd_id = db.Column(db.String)
    title = db.Column(db.String(255), nullable=False)
    director = db.Column(db.String(100))
    year = db.Column(db.Integer, nullable=False)
    my_rating = db.Column(db.Integer)
    date_watched = db.Column(db.String(20))
    my_review = db.Column(db.Text)
    language = db.Column(db.String(20))
    cover_image_url = db.Column(db.String(255))
    collections = db.Column(db.String(255))
    status = db.Column(db.String(20))

class TVShows(db.Model):
    tvdb_id = db.Column(db.String, primary_key=True)
    imdb_id = db.Column(db.String)
    title = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    my_rating = db.Column(db.Integer)
    date_finished = db.Column(db.String(20))
    last_watched = db.Column(db.String(20))
    my_review = db.Column(db.Text)
    language = db.Column(db.String(20))
    cover_image_url = db.Column(db.String(255))
    collections = db.Column(db.String(255))
    status = db.Column(db.String(20))

class Playlists(db.Model):
    user_id = db.Column(db.String, nullable=False)
    playlist_owner = db.Column(db.String, nullable=False)
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    album_art = db.Column(db.String)
    track_count = db.Column(db.Integer)
    is_collab = db.Column(db.Boolean)
    is_public = db.Column(db.Boolean)
    site_approved = db.Column(db.Boolean, default=0, nullable=False)

class LastRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    function_name = db.Column(db.String, nullable=False, unique=True)
    last_run = db.Column(db.DateTime, nullable=False)

class Artworks(db.Model):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255))
    after = db.Column(db.String(100))
    year = db.Column(db.String(100), nullable=False)
    series = db.Column(db.String(255))
    series_id = db.Column(db.Integer)
    file_name = db.Column(db.String(255))
    location = db.Column(db.String(255))
    description = db.Column(db.String(255))
    medium = db.Column(db.String(255))
    collections = db.Column(db.String(255))
    site_approved = db.Column(db.Boolean, default=0, nullable=False)

class GeneratedImages(db.Model):
    id = db.Column(db.String, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    artist_palette = db.Column(db.String(1000), nullable=False)
    model = db.Column(db.String(255))
    model_version = db.Column(db.Integer)
    prompt = db.Column(db.String(1000))

def should_run_function(function_name, interval_days=7):
    last_run_entry = LastRun.query.filter_by(function_name=function_name).first()
    now = datetime.utcnow()
    if last_run_entry:
        if now - last_run_entry.last_run > timedelta(days=interval_days):
            return True
        else:
            return False
    return True

def update_last_run(function_name):
    last_run_entry = LastRun.query.filter_by(function_name=function_name).first()
    now = datetime.utcnow()
    if last_run_entry:
        last_run_entry.last_run = now
    else:
        new_run_entry = LastRun(function_name=function_name, last_run=now)
        db.session.add(new_run_entry)
    db.session.commit()

def check_and_load_books():
    with app.app_context():
        if should_run_function('check_and_load_books', 1):
            csv_file = 'goodreads_library_export.csv'
            csv_path = Path('data/staging') / csv_file
            if csv_path.exists():
                try:
                    load_goodreads_data_into_books(db, Books, csv_file)
                    print(f"Books loaded from {csv_file} successfully!")
                    update_last_run('check_and_load_books')
                except Exception as e:
                    print(f"Error loading books: {e}")
            else:
                print(f"CSV file {csv_file} not found in data/staging.")
        else:
            print(f"Books have been updated within the past day.")

def check_and_load_shows():
    with app.app_context():
        if should_run_function('check_and_load_shows', 1):
            csv_file = 'Boredom Killer - TV.csv'
            csv_path = Path('data/staging') / csv_file
            if csv_path.exists():
                try:
                    load_boredom_killer_into_tvshows(db, TVShows)
                    print(f"TV Shows loaded from Boredom Killer successfully!")
                except Exception as e:
                    print(f"Error loading TV shows: {e}")
            else:
                print(f"Boredom Killer TV show data not found in data/staging.")
        else:
            print(f"TV Shows have been updated within the past day.")

def check_and_load_movies():
    with app.app_context():
        if should_run_function('check_and_load_movies', 1):
            csv_file = 'Boredom Killer - Movies.csv'
            csv_path = Path('data/staging') / csv_file
            if csv_path.exists():
                try:
                    load_boredom_killer_into_movies(db, Movies)
                    print(f"Movies loaded from Boredom Killer successfully!")
                except Exception as e:
                    print(f"Error loading movies: {e}")
            else:
                print(f"Boredom Killer movie data not found in data/staging.")

            letterboxd_path = Path('data/staging/letterboxd') 
            if letterboxd_path.exists():
                try:
                    load_letterboxd_data_into_movies(db, Movies)
                    print(f"Movies loaded from Letterboxd successfully!")
                    update_last_run('check_and_load_movies')
                except Exception as e:
                    print(f"Error loading movies: {e}")
            else:
                print(f"Letterboxd data not found in data/staging.")
        else:
            print(f"Movies have been updated within the past day.")

def check_and_load_playlists():
    with app.app_context():
        if should_run_function('check_and_load_playlists'):
            response = input("It has been over a week since you updated playlist data. Would you like to update it now? (y/n): ").strip().lower()
            if response == 'y':
                try:
                    parse_and_load_playlists(db, Playlists)
                    print("Playlists updated successfully!")
                    update_last_run('check_and_load_playlists')
                except Exception as e:
                    print(f"Error updating playlists: {e}")
            else:
                print("Playlist update skipped.")
        else:
            print("Playlists have been updated within the past week.")

def check_and_load_artworks():
    with app.app_context():
        if should_run_function('check_and_load_artworks', 1):
            csv_file = 'artworks.csv'
            csv_path = Path('data/staging') / csv_file
            if csv_path.exists():
                try:
                    load_artworks_data(db, Artworks)
                    print("Artworks updated successfully!")
                    update_last_run('check_and_load_artworks')
                except Exception as e:
                    print(f"Error updating artworks: {e}")
            else:
                print("Artworks data not found in data/staging.")
        else:
            print("Artworks have been updated within the past day.")

def check_and_load_generative_art():
    with app.app_context():
        if should_run_function('check_and_load_generative_art', 1):
            csv_file = 'generated_images.csv'
            csv_path = Path('data/staging') / csv_file
            if csv_path.exists():
                try:
                    load_generated_images_data(db, GeneratedImages)
                    print("Generative Art updated successfully!")
                    update_last_run('check_and_load_generative_art')
                except Exception as e:
                    print(f"Error updating generative art: {e}")
            else:
                print("Generative Art data not found in data/staging.")
        else:
            print("Generative Art has been updated within the past day.")



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized_callback():
    session['unauth_login'] = 1
    session['next_url'] = request.url
    return redirect(url_for('login'))

def create_user(username, password, role):
    hashed_password = generate_password_hash(password)
    user = User.query.filter_by(username=username).first()

    if user:
        user.password = hashed_password
        user.role = role
    else:
        user = User(username=username, password=hashed_password, role=role)

    db.session.add(user)
    db.session.commit()



# Only uncomment for debugging
# @app.route('/users')
# @login_required
# def show_users():
#     if current_user.role != 'admin':
#         return "You do not have permission to access this page."
    
#     users = User.query.all()
#     user_list = [{'username': user.username, 'password': user.password, 'role': user.role} for user in users]
#     return jsonify(user_list)

@app.errorhandler(404)
def page_not_found(e):
    nav_items = get_user_nav_items()
    image_folder = os.path.join(app.static_folder, 'images', 'creating', 'lunacy')
    images = [f for f in os.listdir(image_folder) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    random.shuffle(images)
    return render_template('404.html', nav_items=nav_items, images=images), 404

@app.route('/check_login')
@login_required
def check_login():
    if current_user.role != 'admin':
        return "You do not have permission to access this page."

    if current_user.is_authenticated:
        return f"User {current_user.username} is logged in."
    else:
        return "User is not logged in."

@app.route('/login', methods=['GET', 'POST'])
def login():
    nav_items = get_user_nav_items()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id  # Store user ID in session
            flash('Login Successful', 'success')
            login_user(user)
            next_page = session.get('next_url', '/')
            session.pop('next_url', None)

            return redirect(next_page)
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    else:
        referrer = request.referrer
        if 'unauth_login' in session and session['unauth_login'] == 1:
            session.pop('unauth_login', None)
            output = session['next_url']
        else:
            if 'login' not in request.url:
                session['next_url'] = request.url
                output = request.url
            else:
                session['next_url'] = referrer
                output = referrer

    return render_template('login.html', nav_items=nav_items)

@app.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(request.referrer or '/')

def init_db():
    with app.app_context():
        db.create_all()
        create_user('admin', 'admin_password', 'admin')  # Replace with secure password
        create_user('viewer', 'viewer_password', 'viewer')  # Replace with secure password



def get_user_nav_items():
    nav_items = [
        {'name': 'Home', 'url': url_for('home'), 'active_page': 'home'},
        {'name': 'Writing', 'url': url_for('writing'), 'active_page': 'writing'},
        {'name': 'Reading', 'url': url_for('reading'), 'active_page': 'reading'},
        {'name': 'Watching', 'url': url_for('watching'), 'active_page': 'watching'},
        {'name': 'Creating', 'url': url_for('creating'), 'active_page': 'creating'},
        {'name': 'Listening', 'url': url_for('listening'), 'active_page': 'listening'},
        {'name': 'Collecting', 'url': url_for('collecting'), 'active_page': 'collecting'},
        {'name': 'Pondering', 'url': url_for('pondering'), 'active_page': 'pondering'},
    ]
    
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return nav_items
        elif current_user.role == 'viewer':
            return [item for item in nav_items if item['name'] not in ['Pondering', 'Collecting']]
    else:
        return [item for item in nav_items if item['name'] in ['Home', 'Reading', 'Writing', 'Creating']]

@app.route('/')
def home():
    nav_items = get_user_nav_items()
    return render_template('home.html', nav_items=nav_items)

@app.route('/writing')
def writing():
    nav_items = get_user_nav_items()
    return render_template('writing.html', nav_items=nav_items)

@app.route('/fyog')
def fyog():
    nav_items = get_user_nav_items()
    return render_template('fyog.html', nav_items=nav_items)

@app.route('/new-generation-thinking')
def ngt():
    nav_items = get_user_nav_items()
    return render_template('new-generation-thinking.html', nav_items=nav_items)

@app.route('/creating')
def creating():
    nav_items = get_user_nav_items()
    artists = Artworks.query.with_entities(Artworks.artist, Artworks.file_name).distinct().all()
    artist_data = []
    for artist in artists:
        if artist.artist and artist.file_name:
            # Use the artist name as the subfolder name
            relative_path = f'images/artists/{artist.artist}/{artist.file_name}'
            
            # Use os.path.join for the full system path
            full_path = os.path.join(app.static_folder, 'images', 'artists', artist.artist, artist.file_name)
            
            if os.path.exists(full_path):
                artist_data.append({
                    'name': artist.artist,
                    'image': url_for('static', filename=relative_path)
                })
            else:
                print(f"Warning: File not found for artist {artist.artist}: {full_path}")

    generated_images = db.session.query(GeneratedImages).all()
    generated_image_data = [{
        'file_name': image.file_name,
        'artist_palette': image.artist_palette.split('|'),
        'model': image.model,
        'model_version': image.model_version,
        'prompt': image.prompt
    } for image in generated_images]

    return render_template('creating.html', 
                           artists=artist_data, 
                           generated_images=generated_image_data, nav_items=nav_items)

@app.route('/pondering')
@login_required
def pondering():
    nav_items = get_user_nav_items()

    # Get pagination and filter parameters from the request
    page = request.args.get('page', 1, type=int)
    per_page = 100
    sort_order = request.args.get('sort_order', 'random')
    start_date = request.args.get('start_date', None, type=int)
    end_date = request.args.get('end_date', None, type=int)
    artist_filter = request.args.getlist('artist')
    selected_artists = request.args.getlist('artist')

    # Fetch paginated and filtered artworks
    approved_artworks, total_pages, all_artists = get_approved_artworks_from_db(
        page=page,
        per_page=per_page,
        sort_order=sort_order,
        start_date=start_date,
        end_date=end_date,
        artist_filter=artist_filter
    )

    return render_template(
        'pondering.html',
        approved_artworks=approved_artworks,
        nav_items=nav_items,
        current_page=page,
        total_pages=total_pages,
        all_artists=all_artists,
        selected_artists=selected_artists
    )

@app.route('/watching')
@login_required
def watching():
    nav_items = get_user_nav_items()
    recently_watched_movies = get_recently_watched_movies()
    recommended_movies = get_movies_from_collection('matts-recommended')
    recently_watched_shows = get_recently_watched_shows()
    recommended_shows = get_shows_from_collection('matts-recommended')
    return render_template('watching.html', nav_items=nav_items,
                            recently_watched_movies=recently_watched_movies, recommended_movies=recommended_movies,
                            recently_watched_shows=recently_watched_shows, recommended_shows=recommended_shows)

@app.route('/movies')
@login_required
def movies():
    nav_items = get_user_nav_items()
    movies_data = read_movies_from_db()
    return render_template('movies.html', movies=movies_data, nav_items=nav_items)

@app.route('/books')
def books():
    nav_items = get_user_nav_items()
    books_data = read_books_from_db()
    return render_template('books.html', books=books_data, nav_items=nav_items)

@app.route('/reading')
def reading():
    nav_items = get_user_nav_items()
    recently_read_books = get_recently_read_books()
    recommended_fiction_books = get_books_from_bookshelf('matts-recommended-fiction')
    recommended_nonfiction_books = get_books_from_bookshelf('matts-recommended-nonfiction')
    return render_template('reading.html', recently_read_books=recently_read_books, 
                                           recommended_fiction_books= recommended_fiction_books, 
                                           recommended_nonfiction_books = recommended_nonfiction_books,
                                           current_user=current_user, nav_items=nav_items)

@app.route('/update_review/<int:book_id>', methods=['POST'])
@login_required
def update_review(book_id):
    nav_items = get_user_nav_items()
    if current_user.role != 'admin':
        return "You do not have permission to update reviews."

    book = Books.query.get_or_404(book_id)
    new_review = request.form.get('my_review')

    # Update the book's review
    book.my_review = new_review
    db.session.commit()

    return redirect(url_for('books'))

@app.route('/collecting')
def collecting():
    nav_items = get_user_nav_items()
    recently_added_pins = get_recently_added_pins()
    recently_added_labels = get_recently_added_labels()
    return render_template('collecting.html', nav_items=nav_items, 
                            recently_added_pins=recently_added_pins, recently_added_labels=recently_added_labels)

@app.route('/pins')
def pins():
    nav_items = get_user_nav_items()
    pins_data = read_pins_from_csv()
    return render_template('pins.html', nav_items=nav_items,
                            pins=pins_data)

@app.route('/alcohol-labels')
def alcohol_labels():
    nav_items = get_user_nav_items()
    labels_data = read_alc_labels_from_csv()
    return render_template('alcohol_labels.html', nav_items=nav_items,
                            labels=labels_data)

@app.route('/listening', methods=['GET', 'POST'])
@login_required
def listening():
    # Currently this is limited to just the date changing functionality. Will need to think of a clever way
    # to allow for multiple sections to cause changes in what is displayed.
    nav_items = get_user_nav_items()
    approved_playlists = get_site_approved_playlists()
    if request.method == 'POST':
        selected_month = request.json['month']
        selected_year = request.json['year']
        search_term = request.json['playlist_code']
        print(search_term)
    
        monthly_playlists_df = generate_monthly_playlists_df()
        playlist_id, playlist_art, playlist_name = select_playlist(monthly_playlists_df, search_term)


        if playlist_id is not None:
            playlist_data = {
                'playlist_id': playlist_id,
                'playlist_art': playlist_art,
                'playlist_name': playlist_name,
            }
            
            print(playlist_data)
            return jsonify(playlist_data)  # Return JSON response with playlist data
        else:
            return jsonify({'error': 'Playlist not found for the selected month and year.'}), 404
    else:
        return render_template('listening.html', nav_items=nav_items,
                                approved_playlists=approved_playlists)



# Reimplement book specific pages once multi-reviews and quotes are handled
# @app.route('/book/<int:book_id>')
# def book(book_id):
#     nav_items = get_user_nav_items()
#     books = read_books_from_csv()
#     book_details = None
#     reviews = []

#     for book in books:
#         if book['id'] == str(book_id):
#             book_details = book
#             book['title'] = truncate_title(book['title'])
#             reviews.append({'date_read': book['date_read'], 'my_rating': book['my_rating'], 'my_review': book['my_review']})
    
#     quotes = []
#     with open('data/book_quotes.csv', 'r', encoding='iso-8859-1') as file:
#         reader = csv.DictReader(file)
#         for row in reader:
#             if row['Goodreads ID'] == str(book_id):
#                 quotes.append({'text': row['Quote'], 'page_number': row['Page Number']})

#     return render_template('book.html', nav_items=nav_items,
#                             book=book_details, reviews=reviews, quotes=quotes)

# DEPRECATED
# @app.route('/playlist')
# @login_required
# def playlist():
#     # Logic to fetch playlist data or perform any necessary actions before rendering the template
#     # Example data for demonstration purposes
#     nav_items = get_user_nav_items()
#     playlist_name = "My Playlist"
#     songs = ["Song 1", "Song 2", "Song 3"]

#     return render_template('playlist.html', nav_items=nav_items, 
#                             playlist_name=playlist_name, songs=songs)

# DEPRECATED
# @app.route('/book-db')
# def display_books():
#     conn = sqlite3.connect('instance/portfolio_prd.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM books')
#     rows = cursor.fetchall()
#     conn.close()
#     return render_template('book-db.html', books_test=rows)

# DEPRECATED
# @app.route('/matt-ranking')
# def matt_ranking():

#     #average_ratings = movie_analytics()

#     # Sort the DataFrame by mean rating in descending order
#     #sorted_ratings = average_ratings.sort_values(by='mean', ascending=False)

#     # ratings=sorted_ratings
#     return render_template('matt_ranking.html', table_html=table_html)

# DEPRECATED
# @app.route('/music2', methods=['GET', 'POST'])
# def music2():
#     if request.method == 'POST':
#         selected_month = request.form['month']
#         selected_year = request.form['year']
        
#         monthly_playlists_df = generate_monthly_playlists_df()
#         playlist_id, playlist_art, playlist_name = select_playlist(monthly_playlists_df, search_term)

#         track_names, artists, artwork_urls = get_tracks_artists(playlist_id)

#         if playlist_id is not None:
#             return render_template('playlist.html', playlist_id=playlist_id, playlist_art=playlist_art, playlist_name=playlist_name, track_names=track_names, artists=artists, artwork_urls=artwork_urls)
#         else:
#             return "Playlist not found for the selected month and year."
#     else:
#         return render_template('music.html')  # Render initial form

if __name__ == '__main__':
    init_db()
    check_and_load_books()
    check_and_load_movies()
    check_and_load_shows()
    check_and_load_playlists()
    check_and_load_artworks()
    check_and_load_generative_art()
    app.run(debug=True)