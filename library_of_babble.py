from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from books import get_recently_read_books, read_books_from_csv, truncate_title
from music import music_test, generate_monthly_playlists_df, select_playlist, get_tracks_artists
from movies import get_recently_watched_movies, watched_movies_from_csv
from pins import get_recently_added_pins, read_pins_from_csv
from alcohol_labels import get_recently_added_labels, read_alc_labels_from_csv
from database import movie_analytics, save_movies_to_database, merge_movie_data, connect_to_database

import pandas as pd
from datetime import datetime
import csv
import re
import os

load_dotenv('ids.env')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)

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

def init_db():
    with app.app_context():
        db.create_all()
        create_user('admin', 'admin_password', 'admin')  # Replace with secure password
        create_user('viewer', 'viewer_password', 'viewer')  # Replace with secure password

@app.route('/users')
@login_required
def show_users():
    if current_user.role != 'admin':
        return "You do not have permission to access this page."
    
    users = User.query.all()
    user_list = [{'username': user.username, 'password': user.password, 'role': user.role} for user in users]
    return jsonify(user_list)

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

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(request.referrer or '/')



@app.route('/')
def home():
    return render_template('home.html')


@app.route('/writing')
def writing():
    return render_template('writing.html')

@app.route('/fyog')
def fyog():
    return render_template('fyog.html')

@app.route('/new-generation-thinking')
def ngt():
    return render_template('new-generation-thinking.html')

@app.route('/watching')
def watching():
    recently_read_books = get_recently_read_books()
    recently_watched_movies = get_recently_watched_movies()
    return render_template('watching.html', recently_read_books=recently_read_books, recently_watched_movies=recently_watched_movies)

@app.route('/books')
def books():
    books_data = read_books_from_csv()
    return render_template('reading.html', books=books_data)

@app.route('/reading')
def reading():
    books_data = read_books_from_csv()
    return render_template('reading.html', books=books_data)

@app.route('/collecting')
def collecting():
    recently_added_pins = get_recently_added_pins()
    recently_added_labels = get_recently_added_labels()
    return render_template('collecting.html', recently_added_pins=recently_added_pins, recently_added_labels=recently_added_labels)

@app.route('/pins')
def pins():
    pins_data = read_pins_from_csv()
    return render_template('pins.html', pins=pins_data)

@app.route('/alcohol-labels')
def alcohol_labels():
    labels_data = read_alc_labels_from_csv()
    return render_template('alcohol_labels.html', labels=labels_data)

@app.route('/listening', methods=['GET', 'POST'])
@login_required
def listening():
    # Currently this is limited to just the date changing functionality. Will need to think of a clever way
    # to allow for multiple sections to cause changes in what is displayed.
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
        return render_template('listening.html')  # Render initial form

@app.route('/playlist')
def playlist():
    # Logic to fetch playlist data or perform any necessary actions before rendering the template
    # Example data for demonstration purposes
    playlist_name = "My Playlist"
    songs = ["Song 1", "Song 2", "Song 3"]

    return render_template('playlist.html', playlist_name=playlist_name, songs=songs)


@app.route('/book/<int:book_id>')
def book(book_id):
    books = read_books_from_csv()
    book_details = None
    reviews = []

    for book in books:
        if book['id'] == str(book_id):
            book_details = book
            book['title'] = truncate_title(book['title'])
            reviews.append({'date_read': book['date_read'], 'my_rating': book['my_rating'], 'my_review': book['my_review']})
    
    quotes = []
    with open('data/book_quotes.csv', 'r', encoding='iso-8859-1') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Goodreads ID'] == str(book_id):
                quotes.append({'text': row['Quote'], 'page_number': row['Page Number']})

    return render_template('book.html', book=book_details, reviews=reviews, quotes=quotes)


@app.route('/movies')
def movies():
    movies_data = watched_movies_from_csv()
    return render_template('movies.html', movies=movies_data)

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

    app.run(debug=True)