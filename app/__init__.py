"""
Application Factory

Creates and configures the Flask application using the factory pattern.
This allows for multiple instances with different configurations (dev, test, prod).
"""
import os
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from config import config
from app.extensions import db, login_manager, migrate

csrf = CSRFProtect()


def create_app(config_name=None):
    """
    Create and configure the Flask application

    Args:
        config_name: Configuration to use (development, production, testing)
                    If None, uses FLASK_ENV environment variable or 'default'

    Returns:
        Configured Flask application instance
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    # Get the absolute path to the project root (one level up from app/)
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    app = Flask(
        __name__,
        template_folder='templates',
        static_folder=os.path.join(basedir, 'static')
    )
    app.config.from_object(config[config_name])

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Import all models so Alembic can detect them for migrations
    from app import models  # noqa: F401

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register context processors
    register_context_processors(app)

    # Add security headers
    register_security_headers(app)

    return app


def register_blueprints(app):
    """Register all Flask blueprints"""

    # Import blueprints here to avoid circular imports
    from app.auth import auth_bp
    from app.reading import reading_bp
    from app.books import books_bp
    from app.movies import movies_bp
    from app.watching import watching_bp
    from app.music import music_bp
    from app.artworks import artworks_bp
    from app.collecting import collecting_bp
    from app.account import account_bp
    from app.writing import writing_bp
    from app.main import main_bp

    # Register blueprints
    app.register_blueprint(main_bp)  # No prefix, root routes
    app.register_blueprint(auth_bp)
    app.register_blueprint(reading_bp, url_prefix='/reading')
    app.register_blueprint(books_bp, url_prefix='/books')
    app.register_blueprint(movies_bp, url_prefix='/movies')
    app.register_blueprint(watching_bp, url_prefix='/watching')
    app.register_blueprint(music_bp, url_prefix='/listening')
    app.register_blueprint(artworks_bp, url_prefix='/artworks')
    app.register_blueprint(collecting_bp, url_prefix='/collecting')
    app.register_blueprint(writing_bp, url_prefix='/writing')
    app.register_blueprint(account_bp)


def register_error_handlers(app):
    """Register error handlers"""

    @app.errorhandler(403)
    def forbidden_error(error):
        # Get list of generative art images for background
        lunacy_path = os.path.join(app.static_folder, 'images/creating/lunacy')
        images = []
        if os.path.exists(lunacy_path):
            images = [f for f in os.listdir(lunacy_path)
                     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
                     and not f.startswith('.')]
        return render_template('403.html', images=images), 403

    @app.errorhandler(404)
    def not_found_error(error):
        # Get list of generative art images for background
        lunacy_path = os.path.join(app.static_folder, 'images/creating/lunacy')
        images = []
        if os.path.exists(lunacy_path):
            images = [f for f in os.listdir(lunacy_path)
                     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
                     and not f.startswith('.')]
        return render_template('404.html', images=images), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        # Get list of generative art images for background
        lunacy_path = os.path.join(app.static_folder, 'images/creating/lunacy')
        images = []
        if os.path.exists(lunacy_path):
            images = [f for f in os.listdir(lunacy_path)
                     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
                     and not f.startswith('.')]
        return render_template('500.html', images=images), 500

    # In production, handle all unhandled exceptions
    if not app.debug:
        @app.errorhandler(Exception)
        def handle_exception(error):
            # Log the error
            app.logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
            db.session.rollback()

            # Return generic error page (no debug info)
            lunacy_path = os.path.join(app.static_folder, 'images/creating/lunacy')
            images = []
            if os.path.exists(lunacy_path):
                images = [f for f in os.listdir(lunacy_path)
                         if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
                         and not f.startswith('.')]
            return render_template('500.html', images=images), 500


def register_context_processors(app):
    """Register context processors to inject variables into all templates"""

    @app.context_processor
    def inject_nav_items():
        """Inject navigation items and active page into all templates"""
        from flask import request
        from app.main.services import get_user_nav_items, can_access_page

        # Auto-detect active page based on URL path
        path = request.path
        active_page = None

        if path == '/':
            active_page = 'home'
        elif path.startswith('/writing'):
            active_page = 'writing'
        elif path.startswith('/books'):
            active_page = 'reading'
        elif path.startswith('/watching'):
            active_page = 'watching'
        elif path.startswith('/creating'):
            active_page = 'creating'
        elif path.startswith('/listening'):
            active_page = 'listening'
        elif path.startswith('/collecting'):
            active_page = 'collecting'
        elif path.startswith('/artworks'):
            active_page = 'pondering'

        return {
            'nav_items': get_user_nav_items(),
            'active_page': active_page,
            'can_access_page': can_access_page
        }

    @app.context_processor
    def inject_site_settings():
        """Inject site settings and page headers into all templates"""
        from flask import request
        from app.services.settings import get_setting
        from app.services.page_headers import get_page_header

        # Detect page slug from URL path
        path = request.path
        page_slug = None

        if path == '/':
            page_slug = 'home'
        elif path.startswith('/writing'):
            page_slug = 'writing'
        elif path.startswith('/reading') or path.startswith('/books'):
            page_slug = 'reading'
        elif path.startswith('/watching'):
            page_slug = 'watching'
        elif path.startswith('/creating'):
            page_slug = 'creating'
        elif path.startswith('/listening'):
            page_slug = 'listening'
        elif path.startswith('/collecting'):
            page_slug = 'collecting'
        elif path.startswith('/artworks'):
            page_slug = 'pondering'

        return {
            'site_title': get_setting('site_title', 'Library of Babble'),
            'site_owner': get_setting('site_owner_name', ''),
            'contact_email': get_setting('contact_email', 'contact@example.com'),
            'page_header': get_page_header(page_slug) if page_slug else None,
        }

    @app.context_processor
    def inject_static_url():
        """Inject static_url helper for images that may be on S3 or local"""
        from urllib.parse import quote

        def static_url(path):
            """
            Returns the full URL for a static asset.
            In development: /static/path
            In production: https://bucket.s3.amazonaws.com/path

            Encodes special characters (like #) in path segments to ensure valid URLs.
            """
            # Encode each path segment to handle special chars like #
            # safe='/' preserves directory separators
            encoded_path = quote(path, safe='/')

            base_url = app.config.get('STATIC_STORAGE_URL', '')
            if base_url:
                # Production: serve from S3
                return f"{base_url}/{encoded_path}"
            else:
                # Development: serve from local /static folder
                return f"/static/{encoded_path}"

        return {'static_url': static_url}


def register_security_headers(app):
    """Add security headers to all responses"""

    @app.after_request
    def add_security_headers(response):
        """Add security headers to prevent common attacks"""

        # Prevent clickjacking attacks
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'

        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Enable XSS protection in browsers
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Control referrer information
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Content Security Policy - prevents inline scripts and external resources
        # Note: Adjust this based on your application's needs
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://code.jquery.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://code.jquery.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-src 'self' https://open.spotify.com; "
            "frame-ancestors 'self'; "
        )
        response.headers['Content-Security-Policy'] = csp

        # Permissions Policy - restrict browser features
        response.headers['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=()'
        )

        # HSTS - Force HTTPS (only enable in production with HTTPS)
        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response
