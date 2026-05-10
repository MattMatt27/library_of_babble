"""
Security utilities for input validation, sanitization, and protection against common attacks.
"""
import re
import shlex
import subprocess
import imghdr
import json
from pathlib import Path
from typing import List, Union, Tuple
from urllib.parse import urlparse, urljoin
from flask import request, abort, jsonify
from flask_login import current_user, login_required
from functools import wraps
from markupsafe import Markup
import bleach


# ==============================================================================
# Authorization Decorators
# ==============================================================================

def admin_required(f):
    """
    Decorator to require admin access for a route.
    Use for admin-only API endpoints (user management, data imports, etc.)

    Note: For page-level access control based on the 4-tier role hierarchy
    (public -> viewer -> user -> admin), use can_access_page() instead.

    Usage:
        @app.route('/admin-only')
        @admin_required
        def admin_page():
            ...
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


def user_required(f):
    """Require user role or higher (user or admin). Viewers are excluded."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role not in ('user', 'admin'):
            return jsonify({'error': 'User access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


# ==============================================================================
# HTML Sanitization (XSS Protection)
# ==============================================================================

# Define allowed HTML tags and attributes for user content
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'i', 'b',
    'ul', 'ol', 'li', 'a', 'blockquote'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
}


def sanitize_html(content: str) -> Markup:
    """
    Sanitize HTML content to prevent XSS.
    Allows safe formatting tags but strips dangerous content.

    Args:
        content: HTML string to sanitize

    Returns:
        Markup object with sanitized HTML
    """
    if not content:
        return Markup('')

    cleaned = bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

    return Markup(cleaned)


# ==============================================================================
# URL Validation (Open Redirect Protection)
# ==============================================================================

def is_safe_url(target: str) -> bool:
    """
    Check if redirect URL is safe (same origin).
    Prevents open redirect vulnerabilities.

    Args:
        target: URL to validate

    Returns:
        True if URL is safe to redirect to
    """
    if not target:
        return False

    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))

    return (
        test_url.scheme in ('http', 'https') and
        ref_url.netloc == test_url.netloc
    )


# ==============================================================================
# Path Traversal Protection
# ==============================================================================

def sanitize_directory_name(name: str) -> str:
    """
    Sanitize directory/file names to prevent path traversal.
    Removes path separators and dangerous characters.

    Args:
        name: Directory or filename to sanitize

    Returns:
        Sanitized name safe for filesystem operations
    """
    if not name:
        return ''

    # Remove path separators and parent directory references
    name = name.replace('/', '').replace('\\', '').replace('..', '')

    # Only allow alphanumeric, spaces, hyphens, underscores, periods
    name = re.sub(r'[^a-zA-Z0-9 _.-]', '', name)

    # Remove leading/trailing whitespace and dots
    name = name.strip().strip('.')

    return name


def sanitize_artist_name(name: str) -> str:
    """
    Sanitize artist name for safe filesystem and database use.
    Preserves Unicode characters but removes path traversal risks.

    Args:
        name: Artist name to sanitize

    Returns:
        Sanitized name safe for filesystem (with Unicode preserved)
    """
    if not name:
        return ''

    # Remove path separators and parent directory references
    name = name.replace('/', '').replace('\\', '').replace('..', '')

    # Remove leading/trailing whitespace and dots
    name = name.strip().strip('.')

    return name


def sanitize_path(path: Union[str, Path]) -> str:
    """
    Sanitize file paths for subprocess calls.

    Args:
        path: Path to sanitize

    Returns:
        Sanitized absolute path string

    Raises:
        ValueError: If path is outside allowed directories
    """
    path = Path(path).resolve()
    # Ensure path is within expected directories
    import tempfile
    allowed_bases = [
        Path.cwd() / 'static',
        Path.cwd() / 'scripts',
        Path.cwd() / 'data',
        Path('/tmp').resolve(),
        Path(tempfile.gettempdir()).resolve(),  # System temp directory (e.g., /private/var/folders on macOS)
    ]
    if not any(path.is_relative_to(base) for base in allowed_bases):
        raise ValueError(f"Path {path} is outside allowed directories")
    return str(path)


def validate_file_path(base_dir: Path, file_path: Path) -> bool:
    """
    Ensure file path is within base directory.
    Prevents path traversal attacks.

    Args:
        base_dir: Base directory that must contain file_path
        file_path: Path to validate

    Returns:
        True if file_path is within base_dir
    """
    try:
        base_dir = base_dir.resolve()
        file_path = file_path.resolve()
        return file_path.is_relative_to(base_dir)
    except (ValueError, OSError):
        return False


# ==============================================================================
# Command Injection Protection
# ==============================================================================

def run_etl_script(script_name: str, file_path: str = None, extra_args: List[str] = None) -> subprocess.CompletedProcess:
    """
    Safely run ETL scripts with validated inputs.

    Args:
        script_name: Name of the ETL script (must be in whitelist)
        file_path: Path to data file (optional for some scripts)
        extra_args: Optional additional arguments (must be in whitelist)

    Returns:
        CompletedProcess instance with command results

    Raises:
        ValueError: If script_name or arguments not in whitelist
        FileNotFoundError: If script doesn't exist
    """
    # Whitelist allowed scripts (both ETL and refresh scripts)
    ALLOWED_SCRIPTS = {
        'etl/books_etl.py',
        'etl/movies_etl.py',
        'etl/shows_etl.py',
        'etl/letterboxd_etl.py',
        'etl/spotify_etl.py',
    }

    if script_name not in ALLOWED_SCRIPTS:
        raise ValueError(f"Script {script_name} not allowed")

    script_path = Path('scripts') / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script {script_path} not found")

    # Build command with validated inputs
    cmd = ['python', str(script_path)]

    # Add file path if provided
    if file_path:
        # Sanitize file path
        safe_file_path = sanitize_path(file_path)
        cmd.append(safe_file_path)

    if extra_args:
        # Validate extra args against whitelist
        ALLOWED_FLAGS = {
            '--use-transaction', '--reset-data', '--reset-letterboxd',
            '--letterboxd-ratings', '--letterboxd-reviews',
            '--bk-movies', '--bk-docs', '--bk-tv', '--bk-docuseries'
        }
        for arg in extra_args:
            if arg not in ALLOWED_FLAGS:
                raise ValueError(f"Argument {arg} not allowed")
        cmd.extend(extra_args)

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
        check=False  # Don't raise on non-zero exit
    )


def run_pg_dump(db_uri: str, output_path: str) -> subprocess.CompletedProcess:
    """
    Safely run pg_dump with validated inputs.

    Args:
        db_uri: PostgreSQL database URI
        output_path: Path where dump should be saved

    Returns:
        CompletedProcess instance with command results

    Raises:
        ValueError: If database URI is invalid
    """
    # Parse and validate database URI
    parsed = urlparse(db_uri)
    if parsed.scheme not in ('postgresql', 'postgres'):
        raise ValueError("Invalid database scheme")

    output_path = sanitize_path(output_path)

    # Use environment variable for password instead of URI
    import os
    import getpass
    env = os.environ.copy()
    if parsed.password:
        env['PGPASSWORD'] = parsed.password

    # Build safe command
    # If no username in URI, use current system user (PostgreSQL default behavior)
    username = parsed.username if parsed.username else getpass.getuser()

    cmd = [
        'pg_dump',
        '-Fc',
        '-h', parsed.hostname or 'localhost',
        '-p', str(parsed.port or 5432),
        '-U', username,
        '-d', parsed.path.lstrip('/'),
        '-f', output_path
    ]

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
        check=False
    )


# ==============================================================================
# File Upload Validation
# ==============================================================================

MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB


def validate_image_file(file_stream, filename: str) -> Tuple[bool, str]:
    """
    Validate image file by checking content, not just extension.

    Args:
        file_stream: File stream object
        filename: Original filename

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    file_stream.seek(0, 2)  # Seek to end
    file_size = file_stream.tell()
    file_stream.seek(0)  # Reset to beginning

    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB"

    if file_size == 0:
        return False, "File is empty"

    # Check actual file type by reading header
    header = file_stream.read(512)
    file_stream.seek(0)

    format = imghdr.what(None, header)
    allowed_formats = ['jpeg', 'png', 'gif', 'webp', 'bmp']

    if format not in allowed_formats:
        return False, f"Invalid image format. Allowed: {', '.join(allowed_formats)}"

    # Check file extension matches content
    file_ext = filename.lower().split('.')[-1]
    ext_to_format = {
        'jpg': 'jpeg',
        'jpeg': 'jpeg',
        'png': 'png',
        'gif': 'gif',
        'webp': 'webp',
        'bmp': 'bmp'
    }

    expected_format = ext_to_format.get(file_ext)
    if expected_format and expected_format != format:
        return False, f"File extension .{file_ext} doesn't match content type {format}"

    return True, "Valid image"


def validate_csv_file(file_stream) -> Tuple[bool, str]:
    """
    Validate CSV file.

    Args:
        file_stream: File stream object

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    file_stream.seek(0, 2)
    file_size = file_stream.tell()
    file_stream.seek(0)

    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB"

    if file_size == 0:
        return False, "File is empty"

    # Try to read as CSV
    try:
        import csv
        file_stream.seek(0)
        sample = file_stream.read(1024).decode('utf-8')
        file_stream.seek(0)

        csv.Sniffer().sniff(sample)
        return True, "Valid CSV"
    except Exception as e:
        return False, f"Invalid CSV file: {str(e)}"


# ==============================================================================
# Password Validation
# ==============================================================================

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password meets security requirements.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"

    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
        return False, "Password must contain at least one special character"

    # Check for common passwords
    if check_password_common(password):
        return False, "Password is too common. Please choose a more unique password"

    return True, "Valid password"


def check_password_common(password: str) -> bool:
    """
    Check if password is in common passwords list.

    Args:
        password: Password to check

    Returns:
        True if password is common
    """
    common_passwords = {
        'password', 'password123', '123456', '12345678',
        'qwerty', 'abc123', 'monkey', '1234567',
        'letmein', 'trustno1', 'dragon', 'baseball',
        'password1', 'Password123', 'Welcome123'
    }
    return password.lower() in common_passwords


# ==============================================================================
# Page Permission Enforcement
# ==============================================================================

def page_visible(page_name):
    """
    Decorator to enforce page visibility permissions based on config.
    Returns 403 if user doesn't have permission to view the page.

    Usage:
        @page_visible('watching')
        def watching_index():
            ...

    Args:
        page_name: Name of the page in page_permissions.json
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Load permissions from config
            config_path = Path('config/page_permissions.json')
            try:
                with open(config_path, 'r') as file:
                    permissions = json.load(file)
            except FileNotFoundError:
                # If config doesn't exist, only allow admins
                if not current_user.is_authenticated or not current_user.is_admin:
                    abort(403)
                return f(*args, **kwargs)

            # Find the page in permissions
            page_config = None
            for page in permissions.get('pages', []):
                if page['page_name'] == page_name:
                    page_config = page
                    break

            # If page not in config, default to admin-only
            if not page_config:
                if not current_user.is_authenticated or not current_user.is_admin:
                    abort(403)
                return f(*args, **kwargs)

            # Check visibility based on user role
            user_role = current_user.role if current_user.is_authenticated else None

            if user_role == 'admin':
                allowed = page_config.get('admin', True)
            elif user_role == 'user':
                allowed = page_config.get('user', False)
            elif user_role == 'viewer':
                allowed = page_config.get('viewer', False)
            else:
                # Public (not logged in)
                allowed = page_config.get('public', False)

            if not allowed:
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator
