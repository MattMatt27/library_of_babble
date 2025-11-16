"""
Migrate ratings from Integer to Float format
Converts the my_rating column in movies, tv_shows, and books tables from Integer to Float
Integer scale 0-10 → Float scale 0-5 (divide by 2)
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from app.extensions import db

def migrate_ratings():
    """Migrate ratings from integer (0-10) to float (0-5) format"""
    app = create_app()
    with app.app_context():
        print("Migrating rating columns from Integer to Float...")
        print("=" * 50)
        print("Converting scale: Integer 0-10 → Float 0-5")

        try:
            # Migrate movies table
            print("\n1. Migrating movies.my_rating...")
            db.session.execute(db.text("""
                ALTER TABLE movies
                ALTER COLUMN my_rating TYPE FLOAT
                USING CASE
                    WHEN my_rating IS NULL THEN NULL
                    ELSE my_rating::FLOAT / 2
                END;
            """))
            db.session.commit()
            print("  ✓ movies.my_rating migrated successfully")

            # Migrate tv_shows table
            print("\n2. Migrating tv_shows.my_rating...")
            db.session.execute(db.text("""
                ALTER TABLE tv_shows
                ALTER COLUMN my_rating TYPE FLOAT
                USING CASE
                    WHEN my_rating IS NULL THEN NULL
                    ELSE my_rating::FLOAT / 2
                END;
            """))
            db.session.commit()
            print("  ✓ tv_shows.my_rating migrated successfully")

            # Migrate books table
            print("\n3. Migrating books.my_rating...")
            db.session.execute(db.text("""
                ALTER TABLE books
                ALTER COLUMN my_rating TYPE FLOAT
                USING CASE
                    WHEN my_rating IS NULL THEN NULL
                    ELSE my_rating::FLOAT / 2
                END;
            """))
            db.session.commit()
            print("  ✓ books.my_rating migrated successfully")

            # Show sample converted values
            print("\n4. Verifying conversion...")
            result = db.session.execute(db.text("""
                SELECT my_rating, COUNT(*) as count
                FROM movies
                WHERE my_rating IS NOT NULL
                GROUP BY my_rating
                ORDER BY my_rating
                LIMIT 10;
            """))

            print("\n  Sample converted ratings in movies table:")
            for row in result:
                print(f"    {row[0]} stars ({row[1]} movies)")

            print("\n" + "=" * 50)
            print("✓ Migration complete!")
            print("\nNext steps:")
            print("  1. Update model files:")
            print("     - app/movies/models.py: my_rating = db.Column(db.Float)")
            print("     - app/shows/models.py: my_rating = db.Column(db.Float)")
            print("     - app/books/models.py: my_rating = db.Column(db.Float)")
            print("  2. Update templates to format float as string for image filenames")
            print("  3. Re-import Letterboxd data with corrected ratings")

        except Exception as e:
            print(f"\n✗ Migration failed: {str(e)}")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    migrate_ratings()
