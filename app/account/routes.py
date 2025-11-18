"""
Account Routes
User account pages and admin tools
"""
from flask import render_template, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from functools import wraps
from app.account import account_bp
from app.extensions import db
from app.artworks.models import Artworks, LikedArtworks
from app.auth.models import User
from app.utils.security import run_etl_script, run_pg_dump, sanitize_path, sanitize_directory_name, validate_file_path
import json
import csv
import tempfile
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


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
                return False, f"pg_dump failed: {result.stderr}"

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
    # Get user's liked artworks if they have permission
    liked_artworks = []
    liked_count = 0

    if current_user.can_view_artworks:
        # Get liked artwork IDs
        liked_ids = [like.artwork_id for like in
                     LikedArtworks.query.filter_by(user_id=current_user.id).all()]

        # Get artwork details (limit to 24 for preview)
        if liked_ids:
            liked_artworks = Artworks.query.filter(Artworks.id.in_(liked_ids)).limit(24).all()
            liked_count = len(liked_ids)

    # Get database statistics for admins
    stats = {}
    all_users = []
    if current_user.is_admin:
        from app.books.models import Books
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
            error_msg = (result.stderr or 'Unknown error occurred').strip()
            return jsonify({
                'success': False,
                'error': f'Import failed and was rolled back. Error: {error_msg}',
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
            error_msg = (result.stderr or 'Unknown error occurred').strip()
            return jsonify({
                'success': False,
                'error': f'Import failed and was rolled back. Error: {error_msg}',
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
                raise Exception(f"Movies import failed: {result.stderr}")

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
                raise Exception(f"Documentaries import failed: {result.stderr}")

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
                raise Exception(f"TV shows import failed: {result.stderr}")

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
                raise Exception(f"Docuseries import failed: {result.stderr}")

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
            return jsonify({
                'success': False,
                'error': f'Import failed: {result.stderr}'
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
        # Run the Spotify refresh script using secure function
        result = run_etl_script(
            'refresh_spotify.py'
        )

        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': f'Refresh failed: {result.stderr}'
            }), 500

        # Parse output for statistics
        output = result.stdout
        playlists_updated = 0

        for line in output.split('\n'):
            if 'Playlists updated:' in line or 'playlists updated' in line.lower():
                try:
                    playlists_updated = int(''.join(filter(str.isdigit, line)))
                except:
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
    """Upload a new artwork with metadata"""
    import uuid
    from werkzeug.utils import secure_filename

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

        # Sanitize artist name to prevent path traversal
        safe_artist = sanitize_directory_name(artist)
        if not safe_artist:
            return jsonify({
                'success': False,
                'error': 'Invalid artist name'
            }), 400

        # Create filename using format: "Title (Year).ext"
        # Only include characters that are safe for filenames
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_', ',')).strip()
        new_filename = f"{safe_title} ({year}){file_ext}"

        # Create artist directory if it doesn't exist (with sanitized name)
        base_dir = Path('static/images/artists')
        artist_dir = base_dir / safe_artist
        artist_dir.mkdir(parents=True, exist_ok=True)

        # Save the file
        file_path = artist_dir / new_filename

        # Validate that final path is within allowed directory (defense in depth)
        if not validate_file_path(base_dir, file_path):
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            }), 400

        # Check if file already exists
        if file_path.exists():
            # Add timestamp to make filename unique
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title_for_timestamp = safe_title.replace(' ', '_')
            new_filename = f"{safe_title_for_timestamp}_{timestamp}{file_ext}"
            file_path = artist_dir / new_filename

        file.save(str(file_path))

        # Create artwork database entry (use sanitized artist name)
        artwork = Artworks(
            id=artwork_id,
            title=title,
            artist=safe_artist,  # Use sanitized artist name
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
            'path': str(file_path),
            'message': 'Artwork uploaded successfully'
        })

    except Exception as e:
        db.session.rollback()
        # Clean up file if it was saved
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
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

                    # Sanitize artist name to prevent path traversal
                    safe_artist = sanitize_directory_name(artist)
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

                    # Check if artwork already exists (by artist + title, using sanitized artist)
                    existing = Artworks.query.filter_by(artist=safe_artist, title=title).first()
                    if existing:
                        errors.append(f'Row {row_num}: Artwork "{title}" by {safe_artist} already exists')
                        skipped += 1
                        continue

                    # Create new artwork (use sanitized artist name)
                    import uuid
                    artwork = Artworks(
                        id=str(uuid.uuid4()),
                        artist=safe_artist,  # Use sanitized artist name
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
