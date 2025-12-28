"""
Application Configuration

Provides different configurations for development, production, and testing environments.
"""
import os
from dotenv import load_dotenv

load_dotenv('.env')


class Config:
    """Base configuration with settings common to all environments"""

    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Static Storage / S3 Configuration
    # In development: serves from local /static folder (empty STATIC_STORAGE_URL)
    # In production: serves from CloudFront URL
    STATIC_STORAGE_URL = os.getenv('STATIC_STORAGE_URL', '')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', '')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

    # Spotify API
    SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
    SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
    SPOTIPY_USERNAME = os.getenv('SPOTIPY_USERNAME')

    # TMDB API
    TMDB_API_BEARER_TOKEN = os.getenv('TMDB_API_BEARER_TOKEN')


class DevelopmentConfig(Config):
    """Development environment configuration"""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://localhost/library_of_babble'
    )
    SQLALCHEMY_ECHO = True  # Log SQL queries in development


class ProductionConfig(Config):
    """Production environment configuration"""

    DEBUG = False
    TESTING = False

    # In production, DATABASE_URL must be set
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable must be set in production")


class TestingConfig(Config):
    """Testing environment configuration"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/library_of_babble_test'
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
