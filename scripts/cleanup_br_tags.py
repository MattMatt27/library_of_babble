"""
Clean up <br> tags in existing database records

This script removes HTML <br> tags from:
- reviews.review_text
- books.my_review
- books.private_notes

Replaces all variants (<br>, <br/>, <br />) with newline characters.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from app.extensions import db
from app.books.models import Books
from app.movies.models import Movies
from app.shows.models import TVShows
from app.common.models import Reviews


def clean_br_tags(text):
    """Remove <br> tags and replace with newlines"""
    if not text:
        return text
    return text.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')


def cleanup_reviews():
    """Clean up <br> tags in reviews table"""
    print("\n1. Cleaning reviews table...")

    reviews_with_br = Reviews.query.filter(
        Reviews.review_text.ilike('%<br%')
    ).all()

    updated_count = 0
    for review in reviews_with_br:
        original = review.review_text
        cleaned = clean_br_tags(original)
        if original != cleaned:
            review.review_text = cleaned
            db.session.add(review)
            updated_count += 1

    db.session.commit()
    print(f"  ✓ Updated {updated_count} reviews")
    return updated_count


def cleanup_books():
    """Clean up <br> tags in books table"""
    print("\n2. Cleaning books table...")

    # Clean my_review column
    books_with_br_review = Books.query.filter(
        Books.my_review.ilike('%<br%')
    ).all()

    review_count = 0
    for book in books_with_br_review:
        original = book.my_review
        cleaned = clean_br_tags(original)
        if original != cleaned:
            book.my_review = cleaned
            db.session.add(book)
            review_count += 1

    # Clean private_notes column
    books_with_br_notes = Books.query.filter(
        Books.private_notes.ilike('%<br%')
    ).all()

    notes_count = 0
    for book in books_with_br_notes:
        original = book.private_notes
        cleaned = clean_br_tags(original)
        if original != cleaned:
            book.private_notes = cleaned
            db.session.add(book)
            notes_count += 1

    db.session.commit()
    print(f"  ✓ Updated {review_count} book reviews")
    print(f"  ✓ Updated {notes_count} book notes")
    return review_count + notes_count


def cleanup_movies():
    """Clean up <br> tags in movies table"""
    print("\n3. Cleaning movies table...")

    # Clean my_review column
    movies_with_br = Movies.query.filter(
        Movies.my_review.ilike('%<br%')
    ).all()

    updated_count = 0
    for movie in movies_with_br:
        original = movie.my_review
        cleaned = clean_br_tags(original)
        if original != cleaned:
            movie.my_review = cleaned
            db.session.add(movie)
            updated_count += 1

    db.session.commit()
    print(f"  ✓ Updated {updated_count} movie reviews")
    return updated_count


def cleanup_shows():
    """Clean up <br> tags in TV shows table"""
    print("\n4. Cleaning TV shows table...")

    # Clean my_review column
    shows_with_br = TVShows.query.filter(
        TVShows.my_review.ilike('%<br%')
    ).all()

    updated_count = 0
    for show in shows_with_br:
        original = show.my_review
        cleaned = clean_br_tags(original)
        if original != cleaned:
            show.my_review = cleaned
            db.session.add(show)
            updated_count += 1

    db.session.commit()
    print(f"  ✓ Updated {updated_count} TV show reviews")
    return updated_count


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("Clean up <br> tags from database")
        print("=" * 60)

        try:
            # Clean up reviews
            reviews_updated = cleanup_reviews()

            # Clean up books
            books_updated = cleanup_books()

            # Clean up movies
            movies_updated = cleanup_movies()

            # Clean up TV shows
            shows_updated = cleanup_shows()

            total_updated = reviews_updated + books_updated + movies_updated + shows_updated

            print("\n" + "=" * 60)
            print(f"✓ Cleanup complete!")
            print(f"  Total records updated: {total_updated}")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ Error during cleanup: {e}")
            db.session.rollback()
            sys.exit(1)
