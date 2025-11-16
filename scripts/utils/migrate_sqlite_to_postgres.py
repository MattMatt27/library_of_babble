"""
Migrate data from SQLite to PostgreSQL

Usage: python scripts/utils/migrate_sqlite_to_postgres.py

This script will:
1. Connect to the old SQLite database
2. Connect to the new PostgreSQL database (via Flask app)
3. Migrate all data from each table
4. Preserve IDs and relationships
"""
import sqlite3
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app
from app.extensions import db
from app.models import (
    User, Books, BookQuote, Movies, TVShows, Reviews, Collections,
    Playlists, Artworks, LikedArtworks, GeneratedImages
)


def migrate_table(cursor, model, table_name, column_mapping=None):
    """
    Generic function to migrate a table from SQLite to PostgreSQL

    Args:
        cursor: SQLite cursor
        model: SQLAlchemy model class
        table_name: Name of the table in SQLite
        column_mapping: Optional dict to map SQLite columns to model attributes
    """
    print(f"Migrating {table_name}...")

    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        count = 0
        for row in rows:
            row_dict = dict(zip(columns, row))

            # Apply column mapping if provided
            if column_mapping:
                row_dict = {column_mapping.get(k, k): v for k, v in row_dict.items()}

            # Create model instance
            instance = model(**row_dict)
            db.session.add(instance)
            count += 1

            # Commit in batches of 100
            if count % 100 == 0:
                db.session.commit()
                print(f"  Migrated {count} rows...")

        # Final commit
        db.session.commit()
        print(f"  ✓ Migrated {count} rows from {table_name}")

    except Exception as e:
        print(f"  ✗ Error migrating {table_name}: {e}")
        db.session.rollback()
        raise


def migrate_data():
    """Main migration function"""
    print("=" * 60)
    print("SQLite to PostgreSQL Migration")
    print("=" * 60)

    # Create Flask app
    app = create_app('development')

    with app.app_context():
        # Connect to old SQLite database
        sqlite_db_path = 'instance/portfolio_prd.db'
        if not os.path.exists(sqlite_db_path):
            print(f"Error: SQLite database not found at {sqlite_db_path}")
            return

        conn = sqlite3.connect(sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print("\nConnected to SQLite database")
        print(f"Connected to PostgreSQL: {app.config['SQLALCHEMY_DATABASE_URI']}\n")

        # Migrate each table
        try:
            migrate_table(cursor, User, 'user')
            migrate_table(cursor, Books, 'books')
            migrate_table(cursor, BookQuote, 'book_quote')
            migrate_table(cursor, Movies, 'movies')
            migrate_table(cursor, TVShows, 'tv_shows')
            migrate_table(cursor, Reviews, 'reviews')
            migrate_table(cursor, Collections, 'collections')
            migrate_table(cursor, Playlists, 'playlists')
            migrate_table(cursor, Artworks, 'artworks')
            migrate_table(cursor, LikedArtworks, 'liked_artworks')
            migrate_table(cursor, GeneratedImages, 'generated_images')

            print("\n" + "=" * 60)
            print("Migration Complete!")
            print("=" * 60)

        except Exception as e:
            print(f"\n✗ Migration failed: {e}")
            return

        finally:
            conn.close()


if __name__ == '__main__':
    migrate_data()
