#!/usr/bin/env python3
"""
Count publications per author
Analyzes authorship patterns in the publications database
"""

from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment or use default
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost/library_of_babble')

def count_coauthors():
    """Count how many publications each author has"""

    # Create database engine
    engine = create_engine(DATABASE_URL, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Query: Count publications per author
        query = text("""
            SELECT
                a.name,
                a.is_you,
                COUNT(pa.publication_id) as pub_count
            FROM authors a
            JOIN publication_authors pa ON a.id = pa.author_id
            GROUP BY a.id, a.name, a.is_you
            ORDER BY COUNT(pa.publication_id) DESC
        """)

        authors = session.execute(query).fetchall()

        if not authors:
            print("No authors found in the database.")
            return

        print("\n" + "="*70)
        print("PUBLICATION COUNT BY AUTHOR")
        print("="*70)
        print(f"{'Author Name':<40} {'Publications':>15} {'You':>10}")
        print("-"*70)

        for author_name, is_you, pub_count in authors:
            you_marker = "✓" if is_you else ""
            print(f"{author_name:<40} {pub_count:>15} {you_marker:>10}")

        print("="*70)
        print(f"Total unique authors: {len(authors)}")

        # Count co-authors (excluding yourself)
        coauthors = [(name, count) for name, is_you, count in authors if not is_you]
        if coauthors:
            print(f"Total co-authors: {len(coauthors)}")

            # Show top 5 co-authors
            print("\nTop 5 most frequent co-authors:")
            for i, (name, count) in enumerate(coauthors[:5], 1):
                print(f"  {i}. {name} ({count} publication{'s' if count > 1 else ''})")

        # Show collaborative publications
        collab_query = text("""
            SELECT
                p.title,
                COUNT(pa.author_id) as author_count
            FROM publications p
            JOIN publication_authors pa ON p.id = pa.publication_id
            WHERE p.id IN (
                SELECT publication_id
                FROM publication_authors pa2
                JOIN authors a ON pa2.author_id = a.id
                WHERE a.is_you = true
            )
            GROUP BY p.id, p.title
            HAVING COUNT(pa.author_id) > 1
            ORDER BY COUNT(pa.author_id) DESC
        """)

        collab_pubs = session.execute(collab_query).fetchall()

        if collab_pubs:
            print(f"\nYour collaborative publications: {len(collab_pubs)}")
            print("\nPublications with co-authors:")
            for title, author_count in collab_pubs:
                print(f"  • {title} ({author_count} authors)")

        print()

    finally:
        session.close()

if __name__ == '__main__':
    count_coauthors()
