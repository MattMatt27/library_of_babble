"""
Account Routes
User account pages and admin tools
"""
from flask import render_template, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from app.account import account_bp
from app.extensions import db
from app.artworks.models import Artworks, LikedArtworks
from app.books.models import LikedQuotes, BookQuote, Books
from app.auth.models import User
from app.utils.security import run_etl_script, run_pg_dump, sanitize_path, sanitize_directory_name, sanitize_artist_name, validate_file_path, admin_required, validate_csv_file, validate_image_file
import json
import csv
import tempfile
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import html


def sanitize_error_message(stderr_output):
    """
    Sanitize error messages from ETL scripts to avoid leaking sensitive info.
    Returns a generic message for users while logging the actual error.
    """
    if not stderr_output:
        return "An unexpected error occurred"

    # Log the actual error for debugging (visible in server logs)
    current_app.logger.error(f"ETL script error: {stderr_output}")

    # Return generic message to user - don't expose internal paths/details
    return "Import failed. Please check the file format and try again."


def load_page_permissions():
    """Load page permissions from config file"""
    config_path = Path('config/page_permissions.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return empty default if file doesn't exist
        return {'pages': []}


def save_page_permissions(permissions_data):
    """Save page permissions to config file"""
    config_path = Path('config/page_permissions.json')
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(permissions_data, f, indent=2)
    return True


def create_database_backup():
    """Create a backup of the database before import operations"""
    try:
        # Get database URI from config
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')

        # Create backups directory if it doesn't exist
        backup_dir = Path('data/backups')
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Handle SQLite databases
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            db_file = Path(db_path)

            if not db_file.exists():
                return False, "Database file not found"

            backup_file = backup_dir / f"library_backup_{timestamp}.db"
            shutil.copy2(db_file, backup_file)

            # Keep only last 10 backups
            backups = sorted(backup_dir.glob('library_backup_*.db'), key=os.path.getmtime, reverse=True)
            for old_backup in backups[10:]:
                old_backup.unlink()

            return True, str(backup_file)

        # Handle PostgreSQL databases
        elif db_uri.startswith('postgresql://') or db_uri.startswith('postgres://'):
            backup_file = backup_dir / f"library_backup_{timestamp}.sql"

            # Use secure pg_dump function to create backup
            result = run_pg_dump(db_uri, str(backup_file))

            if result.returncode != 0:
                current_app.logger.error(f"pg_dump failed: {result.stderr}")
                return False, "Database backup failed"

            # Keep only last 10 backups
            backups = sorted(backup_dir.glob('library_backup_*.sql'), key=os.path.getmtime, reverse=True)
            for old_backup in backups[10:]:
                old_backup.unlink()

            return True, str(backup_file)

        else:
            return False, f"Unsupported database type: {db_uri.split(':')[0]}"

    except subprocess.TimeoutExpired:
        return False, "Backup timed out"
    except Exception as e:
        return False, f"Backup failed: {str(e)}"


@account_bp.route('/account')
@login_required
def index():
    """Main account page"""
    from app.main.services import can_access_page

    # Get user's liked artworks if they have permission
    liked_artworks = []
    liked_count = 0

    if can_access_page('pondering'):
        # Get liked artwork IDs
        liked_ids = [like.artwork_id for like in
                     LikedArtworks.query.filter_by(user_id=current_user.id).all()]

        # Get artwork details (limit to 24 for preview)
        if liked_ids:
            artworks_query = Artworks.query.filter(Artworks.id.in_(liked_ids)).limit(24).all()
            # Convert to dicts with filesystem_artist for image path construction
            liked_artworks = [{
                'id': a.id,
                'title': a.title,
                'artist': a.artist,
                'filesystem_artist': a.artist or '',  # Same as artist for Option A (Unicode preserved)
                'year': a.year,
                'file_name': a.file_name,
                'location': a.location,
                'medium': a.medium,
                'description': a.description
            } for a in artworks_query]
            liked_count = len(liked_ids)

    # Get user's liked quotes if they have permission
    liked_quotes = []
    if can_access_page('book-detail'):
        liked_quotes_query = db.session.query(
            LikedQuotes, BookQuote, Books
        ).join(
            BookQuote, LikedQuotes.quote_id == BookQuote.id
        ).join(
            Books, BookQuote.book_id == Books.id.cast(db.String)
        ).filter(
            LikedQuotes.user_id == current_user.id
        ).order_by(
            LikedQuotes.created_at.desc()
        ).all()

        for like, quote, book in liked_quotes_query:
            # Fix Windows-1252 encoding issues (common in imported data)
            quote_text = quote.quote_text
            # Map common Windows-1252 characters to proper Unicode
            replacements = {
                '\u0092': "'",  # Right single quotation mark
                '\u0093': '"',  # Left double quotation mark
                '\u0094': '"',  # Right double quotation mark
                '\u0096': '—',  # Em dash
                '\u0097': '—',  # Em dash (alternative)
                '\u0091': "'",  # Left single quotation mark
            }
            for old, new in replacements.items():
                quote_text = quote_text.replace(old, new)

            liked_quotes.append({
                'id': quote.id,
                'text': quote_text,
                'page_number': quote.page_number,
                'chapter': quote.chapter,
                'book_title': book.title,
                'book_author': book.author,
                'book_id': book.id
            })

    # Get database statistics for admins
    stats = {}
    all_users = []
    if current_user.is_admin:
        from app.movies.models import Movies
        from app.shows.models import TVShows
        from app.music.models import Playlists

        stats = {
            'books': Books.query.count(),
            'movies': Movies.query.count(),
            'shows': TVShows.query.count(),
            'artworks': Artworks.query.count(),
            'playlists': Playlists.query.count(),
            'users': User.query.count()
        }

        # Get all users for the Manage Users modal
        all_users = User.query.order_by(User.username).all()

    return render_template('account/index.html',
                         liked_artworks=liked_artworks,
                         liked_count=liked_count,
                         liked_quotes=liked_quotes,
                         liked_quotes_count=len(liked_quotes),
                         stats=stats,
                         all_users=all_users)


@account_bp.route('/account/liked-artworks')
@login_required
def liked_artworks_all():
    """Get all liked artworks for current user"""
    if not current_user.can_view_artworks:
        return jsonify({'error': 'Permission denied'}), 403

    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 48, type=int)

    # Get liked artwork IDs
    liked_ids = [like.artwork_id for like in
                 LikedArtworks.query.filter_by(user_id=current_user.id).all()]

    if not liked_ids:
        return jsonify({
            'artworks': [],
            'total': 0,
            'page': page,
            'pages': 0
        })

    # Paginate artworks
    pagination = Artworks.query.filter(Artworks.id.in_(liked_ids)).paginate(
        page=page, per_page=per_page, error_out=False
    )

    artworks = [{
        'id': artwork.id,
        'title': artwork.title,
        'artist': artwork.artist,
        'year': artwork.year,
        'medium': artwork.medium,
        'location': artwork.location,
        'file_name': artwork.file_name,
        'description': artwork.description
    } for artwork in pagination.items]

    return jsonify({
        'artworks': artworks,
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    })


@account_bp.route('/account/export-likes')
@login_required
def export_likes():
    """Export user's liked artworks as CSV"""
    if not current_user.can_view_artworks:
        return jsonify({'error': 'Permission denied'}), 403

    # Get liked artworks with full details
    likes = LikedArtworks.query.filter_by(user_id=current_user.id).all()
    liked_ids = [like.artwork_id for like in likes]
    artworks = Artworks.query.filter(Artworks.id.in_(liked_ids)).all() if liked_ids else []

    # Create temporary CSV file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='', encoding='utf-8')
    writer = csv.writer(temp_file)

    # Write header - include file_name only for admins
    if current_user.is_admin:
        writer.writerow(['Title', 'Artist', 'Year', 'Medium', 'Location', 'File Name', 'Description'])
    else:
        writer.writerow(['Title', 'Artist', 'Year', 'Medium', 'Location', 'Description'])

    # Write artwork data
    for artwork in artworks:
        if current_user.is_admin:
            writer.writerow([
                artwork.title or '',
                artwork.artist or '',
                artwork.year or '',
                artwork.medium or '',
                artwork.location or '',
                artwork.file_name or '',
                artwork.description or ''
            ])
        else:
            writer.writerow([
                artwork.title or '',
                artwork.artist or '',
                artwork.year or '',
                artwork.medium or '',
                artwork.location or '',
                artwork.description or ''
            ])

    temp_file.close()

    filename = f"liked_artworks_{current_user.username}_{datetime.now().strftime('%Y%m%d')}.csv"

    return send_file(
        temp_file.name,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )


@account_bp.route('/account/import/goodreads', methods=['POST'])
@admin_required
def import_goodreads():
    """Import books from Goodreads CSV export"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'error': 'File must be a CSV'}), 400

    is_valid, error_msg = validate_csv_file(file.stream)
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400

    backup_file = None
    temp_file_path = None

    try:
        # Create database backup before import
        backup_success, backup_file = create_database_backup()
        if not backup_success:
            return jsonify({
                'success': False,
                'error': f'Could not create backup: {backup_file}'
            }), 500

        # Save file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        temp_file_path = temp_file.name
        file.save(temp_file_path)
        temp_file.close()

        # Run the Goodreads ETL script with transaction flag using secure function
        result = run_etl_script(
            'etl/books_etl.py',
            temp_file_path,
            ['--use-transaction']
        )

        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

        if result.returncode != 0:
            # Import failed - database was automatically rolled back by the ETL script
            sanitize_error_message(result.stderr)  # Logs the actual error
            return jsonify({
                'success': False,
                'error': 'Import failed and was rolled back. Please check the file format.',
                'rolled_back': True
            }), 500

        # Parse output for statistics
        output = result.stdout
        added = updated = conflicts = 0

        for line in output.split('\n'):
            if 'Books added:' in line:
                added = int(line.split(':')[1].strip())
            elif 'Books updated:' in line:
                updated = int(line.split(':')[1].strip())
            elif 'Conflicts reported:' in line:
                conflicts = int(line.split(':')[1].strip())

        return jsonify({
            'success': True,
            'added': added,
            'updated': updated,
            'conflicts': conflicts,
            'backup_file': backup_file
        })

    except subprocess.TimeoutExpired:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

        return jsonify({
            'success': False,
            'error': 'Import timed out (took longer than 10 minutes). Database changes were rolled back.',
            'rolled_back': True
        }), 500
    except Exception as e:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

        return jsonify({
            'success': False,
            'error': f'Import failed: {str(e)}',
            'rolled_back': True
        }), 500


@account_bp.route('/account/import/letterboxd', methods=['POST'])
@admin_required
def import_letterboxd():
    """Import reviews and ratings from Letterboxd CSV exports"""
    if 'ratings_file' not in request.files or 'reviews_file' not in request.files:
        return jsonify({'success': False, 'error': 'Both ratings and reviews files are required'}), 400

    ratings_file = request.files['ratings_file']
    reviews_file = request.files['reviews_file']
    reset_data = request.form.get('reset_data') == 'true'

    if ratings_file.filename == '' or reviews_file.filename == '':
        return jsonify({'success': False, 'error': 'Both files must be selected'}), 400

    if not ratings_file.filename.endswith('.csv') or not reviews_file.filename.endswith('.csv'):
        return jsonify({'success': False, 'error': 'Both files must be CSV files'}), 400

    for f, label in [(ratings_file, 'Ratings'), (reviews_file, 'Reviews')]:
        is_valid, error_msg = validate_csv_file(f.stream)
        if not is_valid:
            return jsonify({'success': False, 'error': f'{label} file: {error_msg}'}), 400

    ratings_temp_path = None
    reviews_temp_path = None

    try:
        # Create database backup before import
        backup_success, backup_file = create_database_backup()
        if not backup_success:
            return jsonify({
                'success': False,
                'error': f'Could not create backup: {backup_file}'
            }), 500

        # Save both files temporarily
        ratings_temp = tempfile.NamedTemporaryFile(delete=False, suffix='_ratings.csv')
        ratings_temp_path = ratings_temp.name
        ratings_file.save(ratings_temp_path)
        ratings_temp.close()

        reviews_temp = tempfile.NamedTemporaryFile(delete=False, suffix='_reviews.csv')
        reviews_temp_path = reviews_temp.name
        reviews_file.save(reviews_temp_path)
        reviews_temp.close()

        # Run the Letterboxd ETL script with both files using secure function
        extra_args = [
            '--letterboxd-ratings', ratings_temp_path,
            '--letterboxd-reviews', reviews_temp_path,
            '--use-transaction'
        ]

        # Add reset flag if requested
        if reset_data:
            extra_args.append('--reset-letterboxd')

        result = run_etl_script(
            'etl/movies_etl.py',
            None,  # No single file path for this command
            extra_args
        )

        # Clean up temp files
        if ratings_temp_path and os.path.exists(ratings_temp_path):
            os.unlink(ratings_temp_path)
        if reviews_temp_path and os.path.exists(reviews_temp_path):
            os.unlink(reviews_temp_path)

        if result.returncode != 0:
            # Import failed - database was automatically rolled back by the ETL script
            sanitize_error_message(result.stderr)  # Logs the actual error
            return jsonify({
                'success': False,
                'error': 'Import failed and was rolled back. Please check the file format.',
                'rolled_back': True
            }), 500

        # Parse output for statistics
        output = result.stdout
        movies_updated = reviews_added = 0

        for line in output.split('\n'):
            if 'Movies updated:' in line:
                try:
                    movies_updated = int(line.split(':')[1].strip())
                except:
                    pass
            elif 'Reviews added:' in line:
                try:
                    reviews_added = int(line.split(':')[1].strip())
                except:
                    pass

        return jsonify({
            'success': True,
            'ratings_imported': movies_updated,
            'reviews_imported': reviews_added,
            'backup_file': backup_file
        })

    except subprocess.TimeoutExpired:
        # Clean up temp files
        if ratings_temp_path and os.path.exists(ratings_temp_path):
            os.unlink(ratings_temp_path)
        if reviews_temp_path and os.path.exists(reviews_temp_path):
            os.unlink(reviews_temp_path)

        return jsonify({
            'success': False,
            'error': 'Import timed out (took longer than 10 minutes). Database changes were rolled back.',
            'rolled_back': True
        }), 500
    except Exception as e:
        # Clean up temp files
        if ratings_temp_path and os.path.exists(ratings_temp_path):
            os.unlink(ratings_temp_path)
        if reviews_temp_path and os.path.exists(reviews_temp_path):
            os.unlink(reviews_temp_path)

        return jsonify({
            'success': False,
            'error': f'Import failed: {str(e)}',
            'rolled_back': True
        }), 500


@account_bp.route('/account/import/boredom-killer', methods=['POST'])
@admin_required
def import_boredom_killer():
    """Import movies and shows from Boredom Killer CSV exports"""
    # Check if at least one file is provided
    has_movies = 'movies_file' in request.files and request.files['movies_file'].filename != ''
    has_docs = 'docs_file' in request.files and request.files['docs_file'].filename != ''
    has_tv = 'tv_file' in request.files and request.files['tv_file'].filename != ''
    has_docuseries = 'docuseries_file' in request.files and request.files['docuseries_file'].filename != ''

    if not (has_movies or has_docs or has_tv or has_docuseries):
        return jsonify({'success': False, 'error': 'At least one CSV file must be provided'}), 400

    # Validate all provided files are CSVs
    for file_key in ['movies_file', 'docs_file', 'tv_file', 'docuseries_file']:
        if file_key in request.files:
            file = request.files[file_key]
            if file.filename != '' and not file.filename.endswith('.csv'):
                return jsonify({'success': False, 'error': f'{file_key} must be a CSV file'}), 400
            if file.filename != '':
                is_valid, error_msg = validate_csv_file(file.stream)
                if not is_valid:
                    return jsonify({'success': False, 'error': f'{file_key}: {error_msg}'}), 400

    temp_files = {}

    try:
        # Create database backup before import
        backup_success, backup_file = create_database_backup()
        if not backup_success:
            return jsonify({
                'success': False,
                'error': f'Could not create backup: {backup_file}'
            }), 500

        # Save all provided files temporarily
        if has_movies:
            temp = tempfile.NamedTemporaryFile(delete=False, suffix='_bk_movies.csv')
            temp_files['movies'] = temp.name
            request.files['movies_file'].save(temp.name)
            temp.close()

        if has_docs:
            temp = tempfile.NamedTemporaryFile(delete=False, suffix='_bk_docs.csv')
            temp_files['docs'] = temp.name
            request.files['docs_file'].save(temp.name)
            temp.close()

        if has_tv:
            temp = tempfile.NamedTemporaryFile(delete=False, suffix='_bk_tv.csv')
            temp_files['tv'] = temp.name
            request.files['tv_file'].save(temp.name)
            temp.close()

        if has_docuseries:
            temp = tempfile.NamedTemporaryFile(delete=False, suffix='_bk_docuseries.csv')
            temp_files['docuseries'] = temp.name
            request.files['docuseries_file'].save(temp.name)
            temp.close()

        movies_added = docs_added = tv_added = docuseries_added = 0

        # Process Movies file using secure function
        if has_movies:
            result = run_etl_script(
                'etl/movies_etl.py',
                None,
                ['--bk-movies', temp_files['movies'], '--use-transaction']
            )

            if result.returncode != 0:
                sanitize_error_message(result.stderr)
                raise Exception("Movies import failed")

            for line in result.stdout.split('\n'):
                if 'Movies added:' in line or 'added' in line.lower():
                    try:
                        movies_added = int(''.join(filter(str.isdigit, line.split(':')[1])))
                    except:
                        pass

        # Process Documentaries file (goes to movies table) using secure function
        if has_docs:
            result = run_etl_script(
                'etl/movies_etl.py',
                None,
                ['--bk-docs', temp_files['docs'], '--use-transaction']
            )

            if result.returncode != 0:
                sanitize_error_message(result.stderr)
                raise Exception("Documentaries import failed")

            for line in result.stdout.split('\n'):
                if 'Movies added:' in line or 'Documentaries added:' in line or 'added' in line.lower():
                    try:
                        docs_added = int(''.join(filter(str.isdigit, line.split(':')[1])))
                    except:
                        pass

        # Process TV file using secure function
        if has_tv:
            result = run_etl_script(
                'etl/shows_etl.py',
                None,
                ['--bk-tv', temp_files['tv'], '--use-transaction']
            )

            if result.returncode != 0:
                sanitize_error_message(result.stderr)
                raise Exception("TV shows import failed")

            for line in result.stdout.split('\n'):
                if 'Shows added:' in line or 'TV shows added:' in line or 'added' in line.lower():
                    try:
                        tv_added = int(''.join(filter(str.isdigit, line.split(':')[1])))
                    except:
                        pass

        # Process Docuseries file (goes to shows table) using secure function
        if has_docuseries:
            result = run_etl_script(
                'etl/shows_etl.py',
                None,
                ['--bk-docuseries', temp_files['docuseries'], '--use-transaction']
            )

            if result.returncode != 0:
                sanitize_error_message(result.stderr)
                raise Exception("Docuseries import failed")

            for line in result.stdout.split('\n'):
                if 'Shows added:' in line or 'Docuseries added:' in line or 'added' in line.lower():
                    try:
                        docuseries_added = int(''.join(filter(str.isdigit, line.split(':')[1])))
                    except:
                        pass

        # Clean up all temp files
        for temp_path in temp_files.values():
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        return jsonify({
            'success': True,
            'movies_added': movies_added,
            'docs_added': docs_added,
            'tv_added': tv_added,
            'docuseries_added': docuseries_added,
            'backup_file': backup_file
        })

    except subprocess.TimeoutExpired as e:
        # Clean up temp files
        for temp_path in temp_files.values():
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        return jsonify({
            'success': False,
            'error': 'Import timed out (took longer than 10 minutes). Some changes may have been rolled back.',
            'rolled_back': True
        }), 500
    except Exception as e:
        # Clean up temp files
        for temp_path in temp_files.values():
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        return jsonify({
            'success': False,
            'error': f'Import failed: {str(e)}',
            'rolled_back': True
        }), 500


@account_bp.route('/account/import/shows', methods=['POST'])
@admin_required
def import_shows():
    """Import TV shows from CSV export"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'error': 'File must be a CSV'}), 400

    is_valid, error_msg = validate_csv_file(file.stream)
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400

    try:
        # Create database backup before import
        backup_success, backup_info = create_database_backup()
        if not backup_success:
            return jsonify({
                'success': False,
                'error': f'Could not create backup: {backup_info}'
            }), 500

        # Save file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        file.save(temp_file.name)
        temp_file.close()

        # Run the TV Shows ETL script using secure function
        result = run_etl_script(
            'etl/shows_etl.py',
            temp_file.name
        )

        # Clean up temp file
        os.unlink(temp_file.name)

        if result.returncode != 0:
            sanitize_error_message(result.stderr)  # Logs the actual error
            return jsonify({
                'success': False,
                'error': 'Import failed. Please check the file format.'
            }), 500

        # Parse output for statistics
        output = result.stdout
        added = updated = conflicts = 0

        for line in output.split('\n'):
            if 'Shows added:' in line:
                added = int(line.split(':')[1].strip())
            elif 'Shows updated:' in line:
                updated = int(line.split(':')[1].strip())
            elif 'Conflicts reported:' in line:
                conflicts = int(line.split(':')[1].strip())

        return jsonify({
            'success': True,
            'added': added,
            'updated': updated,
            'conflicts': conflicts
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Import timed out'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Import failed: {str(e)}'
        }), 500


@account_bp.route('/account/refresh/spotify', methods=['POST'])
@admin_required
def refresh_spotify():
    """Refresh Spotify playlists"""
    try:
        # Run the Spotify ETL using secure function
        result = run_etl_script(
            'etl/spotify_etl.py'
        )

        if result.returncode != 0:
            sanitize_error_message(result.stderr)  # Logs the actual error
            return jsonify({
                'success': False,
                'error': 'Spotify refresh failed. Please try again.'
            }), 500

        # Parse output for statistics. spotify_etl.py emits a summary line
        # "Total playlists processed: N"; older versions used "Playlists
        # updated: N". Accept either.
        output = result.stdout
        playlists_updated = 0

        for line in output.split('\n'):
            lower = line.lower()
            if ('playlists updated:' in lower
                    or 'playlists processed:' in lower
                    or 'total playlists' in lower):
                try:
                    playlists_updated = int(''.join(filter(str.isdigit, line)))
                    break
                except Exception:
                    playlists_updated = 0

        return jsonify({
            'success': True,
            'playlists_updated': playlists_updated,
            'message': 'Spotify playlists refreshed successfully'
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Refresh timed out'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Refresh failed: {str(e)}'
        }), 500


@account_bp.route('/account/upload_artwork', methods=['POST'])
@admin_required
def upload_artwork():
    """Upload a new artwork with metadata - supports local and S3 storage"""
    import uuid
    from werkzeug.utils import secure_filename
    from app.services.storage import storage

    # Validate required fields
    if 'artwork_file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['artwork_file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    # Validate image file
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        return jsonify({'success': False, 'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'}), 400

    is_valid, error_msg = validate_image_file(file.stream, file.filename)
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400

    # Get form data
    artist = request.form.get('artist', '').strip()
    title = request.form.get('title', '').strip()
    year = request.form.get('year', '').strip()
    medium = request.form.get('medium', '').strip()
    location = request.form.get('location', '').strip()
    series = request.form.get('series', '').strip()
    description = request.form.get('description', '').strip()
    site_approved = request.form.get('site_approved') == 'true'

    # Validate required fields
    if not artist:
        return jsonify({'success': False, 'error': 'Artist name is required'}), 400
    if not title:
        return jsonify({'success': False, 'error': 'Artwork title is required'}), 400
    if not year:
        return jsonify({'success': False, 'error': 'Year is required'}), 400

    try:
        # Generate unique ID for artwork
        artwork_id = str(uuid.uuid4())

        # Get file extension from uploaded file
        original_filename = secure_filename(file.filename)
        file_ext = Path(original_filename).suffix

        # Sanitize artist name for filesystem (preserves Unicode, removes path traversal chars)
        safe_artist = sanitize_artist_name(artist)
        if not safe_artist:
            return jsonify({
                'success': False,
                'error': 'Invalid artist name'
            }), 400

        # Create filename using format: "Title (Year).ext"
        # Only include characters that are safe for filenames
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_', ',')).strip()
        new_filename = f"{safe_title} ({year}){file_ext}"

        # Build relative path for storage (works for both local and S3)
        relative_path = f"images/artists/{safe_artist}/{new_filename}"

        # Check if file already exists
        if storage.file_exists(relative_path):
            # Add timestamp to make filename unique
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title_for_timestamp = safe_title.replace(' ', '_')
            new_filename = f"{safe_title_for_timestamp}_{timestamp}{file_ext}"
            relative_path = f"images/artists/{safe_artist}/{new_filename}"

        # Save file using storage service (handles both local and S3)
        result = storage.save_file(file, relative_path)
        if not result['success']:
            return jsonify({
                'success': False,
                'error': f'Upload failed: {result.get("error", "Unknown error")}'
            }), 500

        # Create artwork database entry (store sanitized artist name - same as folder)
        artwork = Artworks(
            id=artwork_id,
            title=title,
            artist=safe_artist,  # Sanitized name (Unicode preserved, path chars removed)
            year=year,
            medium=medium or None,
            location=location or None,
            series=series or None,
            description=description or None,
            file_name=new_filename,
            site_approved=site_approved
        )

        db.session.add(artwork)
        db.session.commit()

        return jsonify({
            'success': True,
            'artwork_id': artwork_id,
            'artist': artist,
            'title': title,
            'filename': new_filename,
            'path': relative_path,
            'message': 'Artwork uploaded successfully'
        })

    except Exception as e:
        db.session.rollback()
        # Clean up file if it was saved
        if 'relative_path' in locals():
            storage.delete_file(relative_path)
        return jsonify({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }), 500


@account_bp.route('/account/import_artworks_csv', methods=['POST'])
@admin_required
def import_artworks_csv():
    """Import artworks from CSV file"""
    if 'artworks_csv' not in request.files:
        return jsonify({'success': False, 'error': 'No CSV file provided'}), 400

    file = request.files['artworks_csv']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'error': 'File must be a CSV'}), 400

    is_valid, error_msg = validate_csv_file(file.stream)
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400

    temp_file_path = None

    try:
        # Create database backup before import
        backup_success, backup_file = create_database_backup()
        if not backup_success:
            return jsonify({
                'success': False,
                'error': f'Could not create backup: {backup_file}'
            }), 500

        # Save file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        temp_file_path = temp_file.name
        file.save(temp_file_path)
        temp_file.close()

        # Read and process CSV
        imported = 0
        skipped = 0
        errors = []

        with open(temp_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            # Validate CSV has required columns
            required_columns = {'artist', 'title', 'year'}
            if not required_columns.issubset(set(reader.fieldnames or [])):
                return jsonify({
                    'success': False,
                    'error': f'CSV must include columns: {", ".join(required_columns)}'
                }), 400

            for row_num, row in enumerate(reader, start=2):
                try:
                    # Validate required fields
                    artist = row.get('artist', '').strip()
                    title = row.get('title', '').strip()
                    year = row.get('year', '').strip()

                    if not artist or not title or not year:
                        errors.append(f'Row {row_num}: Missing required field (artist, title, or year)')
                        skipped += 1
                        continue

                    # Sanitize artist name (preserves Unicode, removes path traversal chars)
                    safe_artist = sanitize_artist_name(artist)
                    if not safe_artist:
                        errors.append(f'Row {row_num}: Invalid artist name "{artist}"')
                        skipped += 1
                        continue

                    # Optional fields
                    medium = row.get('medium', '').strip() or None
                    location = row.get('location', '').strip() or None
                    series = row.get('series', '').strip() or None
                    description = row.get('description', '').strip() or None
                    file_name = row.get('file_name', '').strip() or None
                    site_approved_str = row.get('site_approved', '').strip().lower()
                    site_approved = site_approved_str in ('true', '1', 'yes', 'y')

                    # Check if artwork already exists (by artist + title)
                    existing = Artworks.query.filter_by(artist=artist, title=title).first()
                    if existing:
                        errors.append(f'Row {row_num}: Artwork "{title}" by {artist} already exists')
                        skipped += 1
                        continue

                    # Create new artwork (store sanitized artist name - same as folder)
                    import uuid
                    artwork = Artworks(
                        id=str(uuid.uuid4()),
                        artist=safe_artist,  # Sanitized name (Unicode preserved, path chars removed)
                        title=title,
                        year=year,
                        medium=medium,
                        location=location,
                        series=series,
                        description=description,
                        file_name=file_name,
                        site_approved=site_approved
                    )

                    db.session.add(artwork)
                    imported += 1

                except Exception as e:
                    errors.append(f'Row {row_num}: {str(e)}')
                    skipped += 1
                    continue

        # Commit all changes
        db.session.commit()

        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

        response_data = {
            'success': True,
            'imported': imported,
            'skipped': skipped,
            'backup_file': backup_file
        }

        if errors:
            response_data['errors'] = errors[:10]  # Limit to first 10 errors

        return jsonify(response_data)

    except Exception as e:
        db.session.rollback()

        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

        return jsonify({
            'success': False,
            'error': f'Import failed: {str(e)}'
        }), 500


# =============================================================================
# Playlist and Collection Management Routes
# =============================================================================

@account_bp.route('/account/playlists', methods=['GET'])
@admin_required
def get_playlists():
    """Get all playlists with their collection assignments"""
    from app.music.models import Playlists
    from app.common.models import Collection, CollectionItem
    import os

    try:
        # Check for mine_only filter
        mine_only = request.args.get('mine_only', 'false').lower() == 'true'

        # Get playlists (optionally filtered by owner)
        query = Playlists.query
        if mine_only:
            spotify_username = os.environ.get('SPOTIPY_USERNAME', '')
            if spotify_username:
                # Filter by playlist_owner (display name) or user_id (username)
                # Try both since they might differ
                query = query.filter(
                    db.or_(
                        Playlists.user_id == spotify_username,
                        Playlists.playlist_owner == spotify_username
                    )
                )

        playlists = query.order_by(Playlists.name).all()

        # Get music collections (containing playlists OR marked as Playlist type)
        playlist_collection_ids = db.session.query(CollectionItem.collection_id).filter_by(
            item_type='Playlist'
        ).distinct().subquery()

        collections = Collection.query.filter(
            db.or_(
                Collection.id.in_(playlist_collection_ids),
                Collection.collection_type == 'Playlist'
            )
        ).order_by(Collection.sort_order, Collection.collection_name).all()

        # Build collection assignment map
        collection_items = CollectionItem.query.filter_by(item_type='Playlist').all()
        playlist_collections = {}
        for item in collection_items:
            playlist_collections[item.item_id] = item.collection_id

        playlists_data = [{
            'id': p.id,
            'name': p.name,
            'album_art': p.album_art,
            'description': p.description,
            'site_approved': p.site_approved,
            'playlist_owner': p.playlist_owner,
            'collection_id': playlist_collections.get(p.id)
        } for p in playlists]

        collections_data = [{
            'id': c.id,
            'name': c.collection_name,
            'description': c.description,
            'site_approved': c.site_approved,
            'sort_order': c.sort_order
        } for c in collections]

        return jsonify({
            'success': True,
            'playlists': playlists_data,
            'collections': collections_data
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@account_bp.route('/account/playlists/<playlist_id>/toggle-approval', methods=['POST'])
@admin_required
def toggle_playlist_approval(playlist_id):
    """Toggle site_approved status for a playlist"""
    from app.music.models import Playlists

    try:
        playlist = Playlists.query.get(playlist_id)
        if not playlist:
            return jsonify({'success': False, 'error': 'Playlist not found'}), 404

        playlist.site_approved = not playlist.site_approved
        db.session.commit()

        return jsonify({
            'success': True,
            'site_approved': playlist.site_approved
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@account_bp.route('/account/playlists/<playlist_id>/collection', methods=['POST'])
@admin_required
def update_playlist_collection(playlist_id):
    """Add or remove a playlist from a collection"""
    from app.music.models import Playlists
    from app.common.models import Collection, CollectionItem

    try:
        data = request.get_json()
        collection_id = data.get('collection_id')  # None means remove from all collections

        playlist = Playlists.query.get(playlist_id)
        if not playlist:
            return jsonify({'success': False, 'error': 'Playlist not found'}), 404

        # Remove from any existing collection
        CollectionItem.query.filter_by(
            item_type='Playlist',
            item_id=playlist_id
        ).delete()

        # Add to new collection if specified
        if collection_id:
            collection = Collection.query.get(collection_id)
            if not collection:
                return jsonify({'success': False, 'error': 'Collection not found'}), 404

            # Get max order in collection
            max_order = db.session.query(db.func.max(CollectionItem.item_order)).filter_by(
                collection_id=collection_id
            ).scalar() or 0

            new_item = CollectionItem(
                collection_id=collection_id,
                item_type='Playlist',
                item_id=playlist_id,
                item_order=max_order + 1
            )
            db.session.add(new_item)

        db.session.commit()

        return jsonify({
            'success': True,
            'collection_id': collection_id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@account_bp.route('/account/collections', methods=['GET'])
@admin_required
def get_collections():
    """Get all collections ordered by sort_order"""
    from app.common.models import Collection, CollectionItem

    try:
        # Check for type filter (e.g., ?type=music for playlist collections only)
        collection_type = request.args.get('type', '')

        if collection_type == 'music':
            # Get collections that contain playlists OR are marked as Playlist type
            playlist_collection_ids = db.session.query(CollectionItem.collection_id).filter_by(
                item_type='Playlist'
            ).distinct().subquery()

            collections = Collection.query.filter(
                db.or_(
                    Collection.id.in_(playlist_collection_ids),
                    Collection.collection_type == 'Playlist'
                )
            ).order_by(Collection.sort_order, Collection.id).all()
        else:
            collections = Collection.query.order_by(Collection.sort_order, Collection.id).all()

        collections_data = []
        for c in collections:
            item_count = CollectionItem.query.filter_by(collection_id=c.id).count()
            collections_data.append({
                'id': c.id,
                'name': c.collection_name,
                'description': c.description,
                'site_approved': c.site_approved,
                'sort_order': c.sort_order,
                'item_count': item_count
            })

        return jsonify({
            'success': True,
            'collections': collections_data
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@account_bp.route('/account/collections', methods=['POST'])
@admin_required
def create_collection():
    """Create a new collection"""
    from app.common.models import Collection

    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip() or None
        collection_type = data.get('type')  # Optional: 'Playlist', 'Book', etc.

        if not name:
            return jsonify({'success': False, 'error': 'Collection name is required'}), 400

        # Check for duplicate name
        existing = Collection.query.filter_by(collection_name=name).first()
        if existing:
            return jsonify({'success': False, 'error': 'Collection with this name already exists'}), 400

        # Get max sort_order
        max_order = db.session.query(db.func.max(Collection.sort_order)).scalar() or 0

        collection = Collection(
            collection_name=name,
            description=description,
            collection_type=collection_type,
            site_approved=True,
            sort_order=max_order + 1
        )
        db.session.add(collection)
        db.session.commit()

        return jsonify({
            'success': True,
            'collection': {
                'id': collection.id,
                'name': collection.collection_name,
                'description': collection.description,
                'site_approved': collection.site_approved,
                'sort_order': collection.sort_order
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@account_bp.route('/account/collections/<int:collection_id>', methods=['DELETE'])
@admin_required
def delete_collection(collection_id):
    """Delete a collection (items are removed but not deleted)"""
    from app.common.models import Collection

    try:
        collection = Collection.query.get(collection_id)
        if not collection:
            return jsonify({'success': False, 'error': 'Collection not found'}), 404

        db.session.delete(collection)  # Cascade will delete CollectionItems
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@account_bp.route('/account/collections/<int:collection_id>', methods=['PUT'])
@admin_required
def update_collection(collection_id):
    """Update a collection's name and description"""
    from app.common.models import Collection

    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip() or None

        if not name:
            return jsonify({'success': False, 'error': 'Collection name is required'}), 400

        collection = Collection.query.get(collection_id)
        if not collection:
            return jsonify({'success': False, 'error': 'Collection not found'}), 404

        # Check for duplicate name (excluding current collection)
        existing = Collection.query.filter(
            Collection.collection_name == name,
            Collection.id != collection_id
        ).first()
        if existing:
            return jsonify({'success': False, 'error': 'Another collection with this name already exists'}), 400

        collection.collection_name = name
        collection.description = description
        db.session.commit()

        return jsonify({
            'success': True,
            'collection': {
                'id': collection.id,
                'name': collection.collection_name,
                'description': collection.description
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@account_bp.route('/account/collections/<int:collection_id>/toggle-approval', methods=['POST'])
@admin_required
def toggle_collection_approval(collection_id):
    """Toggle site_approved status for a collection"""
    from app.common.models import Collection

    try:
        collection = Collection.query.get(collection_id)
        if not collection:
            return jsonify({'success': False, 'error': 'Collection not found'}), 404

        collection.site_approved = not collection.site_approved
        db.session.commit()

        return jsonify({
            'success': True,
            'site_approved': collection.site_approved
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@account_bp.route('/account/collections/reorder', methods=['POST'])
@admin_required
def reorder_collections():
    """Reorder collections by updating sort_order"""
    from app.common.models import Collection

    try:
        data = request.get_json()
        order = data.get('order', [])  # List of collection IDs in new order

        if not order:
            return jsonify({'success': False, 'error': 'Order list is required'}), 400

        for index, collection_id in enumerate(order):
            collection = Collection.query.get(collection_id)
            if collection:
                collection.sort_order = index

        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@account_bp.route('/account/page-permissions', methods=['GET'])
@admin_required
def get_page_permissions():
    """Get current page permissions configuration"""
    try:
        permissions = load_page_permissions()
        return jsonify({'success': True, 'permissions': permissions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@account_bp.route('/account/page-permissions', methods=['POST'])
@admin_required
def update_page_permissions():
    """Update page permissions configuration"""
    try:
        data = request.get_json()

        if not data or 'pages' not in data:
            return jsonify({'success': False, 'error': 'Invalid data format'}), 400

        # Validate that all required fields are present
        for page in data['pages']:
            required_fields = ['page_name', 'display_name', 'route_name', 'public', 'viewer', 'user', 'admin']
            if not all(field in page for field in required_fields):
                return jsonify({'success': False, 'error': f'Missing required fields for page: {page.get("page_name", "unknown")}'}), 400

        # Save the configuration
        save_page_permissions(data)

        return jsonify({'success': True, 'message': 'Page permissions updated successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
