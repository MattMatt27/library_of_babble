"""
Watching Routes
Aggregates movies and TV shows for the watching page
"""
import random
import time
from flask import render_template, request, jsonify, session
from flask_login import current_user, login_required
from sqlalchemy import func
from app.watching import watching_bp
from app.movies.models import Movies, MovieQuote, LikedMovieQuotes
from app.shows.models import TVShows
from app.shows.services import get_shows_from_collection
from app.movies.services import get_recently_watched_movies, get_movies_from_collection
from app.common.models import Collection, CollectionItem
from app.common.services import get_pairings_for_page
from app.utils.security import page_visible
from app.extensions import db


@watching_bp.route('/')
@page_visible('watching')
def index():
    """Watching page - recently watched movies and TV shows"""
    # Get movie data
    recently_watched_movies = get_recently_watched_movies(limit=20)

    # Get pairings where at least one side is a Movie or TVShow
    content_pairings = get_pairings_for_page(['Movie', 'TVShow'])

    # Get a random short movie quote for the quote card
    short_quotes = MovieQuote.query.filter(
        func.length(MovieQuote.quote_text) <= 300
    ).all()

    random_quote = None
    if short_quotes:
        quote = random.choice(short_quotes)
        movie = Movies.query.get(quote.movie_id)
        if movie:
            random_quote = {
                'id': quote.id,
                'text': quote.quote_text,
                'movie_title': movie.title,
                'movie_director': movie.director,
                'movie_id': movie.tmdb_id,
            }

    # Build shelves from approved Movie/TVShow collections
    movie_collections = Collection.query.filter(
        Collection.collection_type.in_(['Movie', 'TVShow']),
        Collection.site_approved == True
    ).order_by(Collection.sort_order.asc().nullslast(), Collection.collection_name).all()

    movie_shelves = []
    tv_shelves = []
    for collection in movie_collections:
        if collection.collection_type == 'Movie':
            items = get_movies_from_collection(collection.collection_name)
            target = movie_shelves
        else:
            items = get_shows_from_collection(collection.collection_name)
            target = tv_shelves
        if items:
            target.append({
                'id': collection.id,
                'name': collection.collection_name,
                'display_name': collection.description or collection.collection_name.replace('-', ' ').title(),
                'items': items,
                'type': collection.collection_type,
            })

    return render_template(
        'watching/index.html',
        recently_watched_movies=recently_watched_movies,
        movie_shelves=movie_shelves,
        tv_shelves=tv_shelves,
        content_pairings=content_pairings,
        random_quote=random_quote,
        current_user=current_user
    )


@watching_bp.route('/quotes')
@page_visible('watching')
def quotes():
    """Movie quotes exploration page with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 100
    sort_order = request.args.get('sort', 'random')
    movie_filter = request.args.get('movie', None, type=str)
    liked_only = request.args.get('liked', 'false') == 'true'

    # Random seed for consistent pagination
    filter_key = f"{movie_filter}_{liked_only}"
    if sort_order == 'random':
        previous_sort = session.get('movie_quotes_previous_sort')
        if ('movie_quotes_random_seed' not in session or
            session.get('movie_quotes_filter_key') != filter_key or
            previous_sort != 'random'):
            session['movie_quotes_random_seed'] = int(time.time() * 1000000) % 2147483647
            session['movie_quotes_filter_key'] = filter_key
        random_seed = session['movie_quotes_random_seed']
    else:
        random_seed = None
    session['movie_quotes_previous_sort'] = sort_order

    # Get user's liked quotes
    liked_quote_ids = set()
    if current_user.is_authenticated:
        liked = LikedMovieQuotes.query.filter_by(user_id=current_user.id).all()
        liked_quote_ids = {like.quote_id for like in liked}

    # Build query
    query = MovieQuote.query
    if movie_filter:
        query = query.filter(MovieQuote.movie_id == movie_filter)

    all_quotes = query.all()

    # Build quotes data with movie info
    quotes_data = []
    for quote in all_quotes:
        movie = Movies.query.get(quote.movie_id)
        if movie:
            is_liked = quote.id in liked_quote_ids
            if liked_only and not is_liked:
                continue
            quotes_data.append({
                'id': quote.id,
                'text': quote.quote_text,
                'movie_id': movie.tmdb_id,
                'movie_title': movie.title,
                'movie_director': movie.director,
                'movie_cover': movie.cover_image_url,
                'movie_year': movie.year,
                'character': quote.character,
                'scene_timestamp': quote.scene_timestamp,
                'is_liked': is_liked,
            })

    # Sort
    if sort_order == 'random' and random_seed:
        random.seed(random_seed)
        random.shuffle(quotes_data)
    elif sort_order == 'movie-title':
        quotes_data.sort(key=lambda q: q['movie_title'].lower())
    elif sort_order == 'movie-year-asc':
        quotes_data.sort(key=lambda q: q['movie_year'] or 0)
    elif sort_order == 'movie-year-desc':
        quotes_data.sort(key=lambda q: q['movie_year'] or 0, reverse=True)

    # Pagination
    total_quotes = len(quotes_data)
    total_pages = max(1, (total_quotes + per_page - 1) // per_page)
    page = min(page, total_pages)
    start_idx = (page - 1) * per_page
    paginated_quotes = quotes_data[start_idx:start_idx + per_page]

    # Get unique movies for filter dropdown
    all_movie_ids = [q.movie_id for q in MovieQuote.query.all()]
    movies_with_quotes = Movies.query.filter(
        Movies.tmdb_id.in_(all_movie_ids)
    ).order_by(Movies.title).all()

    return render_template(
        'watching/quotes.html',
        quotes=paginated_quotes,
        movies_with_quotes=movies_with_quotes,
        current_page=page,
        total_pages=total_pages,
        total_quotes=total_quotes,
        sort_order=sort_order,
        movie_filter=movie_filter,
        liked_only=liked_only,
        current_user=current_user
    )
