"""
One-time script to extract blockquotes from movie reviews into MovieQuote records.

Merges adjacent blockquotes into a single quote, removes them from the review text,
and creates MovieQuote records.

Usage: python scripts/extract_movie_quotes.py [--dry-run]
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.movies.models import Movies, MovieQuote
from app.extensions import db


def extract_and_clean(review_html):
    """
    Extract blockquotes from review HTML.
    Returns (merged_quote_text, cleaned_review).
    Merges all adjacent blockquotes into one quote, strips empty ones.
    """
    # Find all blockquote contents
    blockquotes = re.findall(r'<blockquote>(.*?)</blockquote>', review_html, re.DOTALL)

    # Filter out empty/whitespace-only blockquotes
    blockquotes = [bq.strip() for bq in blockquotes if bq.strip()]

    if not blockquotes:
        return None, review_html

    # Merge all blockquotes into one quote text
    merged_quote = '\n'.join(blockquotes)

    # Remove all blockquote tags from the review
    cleaned = re.sub(r'<blockquote>.*?</blockquote>', '', review_html, flags=re.DOTALL)

    # Clean up resulting whitespace/empty lines
    cleaned = cleaned.strip()

    return merged_quote, cleaned


def main():
    dry_run = '--dry-run' in sys.argv

    app = create_app('development')
    with app.app_context():
        movies = Movies.query.filter(Movies.my_review.like('%<blockquote>%')).all()
        print(f'Found {len(movies)} movies with blockquotes\n')

        created = 0
        for movie in movies:
            quote_text, cleaned_review = extract_and_clean(movie.my_review)

            if not quote_text:
                print(f'  SKIP {movie.title} — no non-empty blockquotes')
                continue

            preview = quote_text[:80].replace('\n', ' ')
            print(f'  {movie.title} ({movie.year})')
            print(f'    Quote: "{preview}..."' if len(quote_text) > 80 else f'    Quote: "{preview}"')
            print(f'    Review cleaned: {len(movie.my_review)} -> {len(cleaned_review)} chars')

            if not dry_run:
                # Check if quote already exists for this movie
                existing = MovieQuote.query.filter_by(
                    movie_id=movie.tmdb_id
                ).first()
                if existing:
                    print(f'    SKIP — quote already exists (id={existing.id})')
                    continue

                quote = MovieQuote(
                    movie_id=movie.tmdb_id,
                    quote_text=quote_text,
                )
                db.session.add(quote)

                # Update the review to remove blockquotes
                movie.my_review = cleaned_review

                created += 1

            print()

        if not dry_run:
            db.session.commit()
            print(f'Done. Created {created} MovieQuote records.')
        else:
            print(f'DRY RUN complete. Would create {len(movies)} MovieQuote records.')


if __name__ == '__main__':
    main()
