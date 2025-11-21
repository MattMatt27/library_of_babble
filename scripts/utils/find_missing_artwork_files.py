#!/usr/bin/env python3
"""
Script to find artwork database entries that don't have corresponding image files
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.artworks.models import Artworks


def find_missing_artwork_files():
    """Find all artworks in database that don't have corresponding image files"""

    app = create_app()

    with app.app_context():
        print(f"\n{'='*80}")
        print("Finding Artworks with Missing Image Files")
        print(f"{'='*80}\n")

        # Get all artworks from database
        all_artworks = Artworks.query.all()
        print(f"Total artworks in database: {len(all_artworks)}\n")

        # Track missing files
        missing_files = []
        missing_artist_dirs = []
        artworks_without_filename = []
        found_files = 0

        # Check each artwork
        for artwork in all_artworks:
            # Check if artwork has a file_name
            if not artwork.file_name:
                artworks_without_filename.append(artwork)
                continue

            # Build expected file path
            artist_dir = Path('static/images/artists') / artwork.artist
            file_path = artist_dir / artwork.file_name

            # Check if file exists
            if not file_path.exists():
                # Check if it's because the artist directory doesn't exist
                if not artist_dir.exists():
                    missing_artist_dirs.append({
                        'artwork': artwork,
                        'expected_path': str(file_path),
                        'artist_dir': str(artist_dir)
                    })
                else:
                    missing_files.append({
                        'artwork': artwork,
                        'expected_path': str(file_path),
                        'artist_dir': str(artist_dir)
                    })
            else:
                found_files += 1

        # Report results
        print(f"{'='*80}")
        print("Summary")
        print(f"{'='*80}")
        print(f"Artworks with files found: {found_files}")
        print(f"Artworks without file_name: {len(artworks_without_filename)}")
        print(f"Missing artist directories: {len(missing_artist_dirs)}")
        print(f"Missing image files (directory exists): {len(missing_files)}")
        print(f"Total artworks with issues: {len(artworks_without_filename) + len(missing_artist_dirs) + len(missing_files)}")
        print()

        # Detail: Artworks without file_name
        if artworks_without_filename:
            print(f"{'='*80}")
            print(f"Artworks Without file_name Field ({len(artworks_without_filename)})")
            print(f"{'='*80}")
            for artwork in artworks_without_filename:
                print(f"ID: {artwork.id}")
                print(f"  Title: {artwork.title}")
                print(f"  Artist: {artwork.artist}")
                print(f"  Year: {artwork.year}")
                print()

        # Detail: Missing artist directories
        if missing_artist_dirs:
            print(f"{'='*80}")
            print(f"Missing Artist Directories ({len(missing_artist_dirs)})")
            print(f"{'='*80}")
            # Group by artist
            artists_missing = {}
            for entry in missing_artist_dirs:
                artist = entry['artwork'].artist
                if artist not in artists_missing:
                    artists_missing[artist] = []
                artists_missing[artist].append(entry)

            for artist, entries in sorted(artists_missing.items()):
                print(f"\nArtist: {artist} ({len(entries)} artworks)")
                print(f"  Missing directory: {entries[0]['artist_dir']}")
                for entry in entries[:5]:  # Show first 5
                    print(f"    - {entry['artwork'].title} ({entry['artwork'].year})")
                if len(entries) > 5:
                    print(f"    ... and {len(entries) - 5} more")
            print()

        # Detail: Missing image files (where directory exists)
        if missing_files:
            print(f"{'='*80}")
            print(f"Missing Image Files - Directory Exists ({len(missing_files)})")
            print(f"{'='*80}")
            for entry in missing_files:
                artwork = entry['artwork']
                print(f"Artist: {artwork.artist}")
                print(f"  Title: {artwork.title} ({artwork.year})")
                print(f"  Expected file: {entry['expected_path']}")
                print(f"  ID: {artwork.id}")

                # Check if there are any files in the artist directory
                artist_path = Path(entry['artist_dir'])
                if artist_path.exists():
                    files_in_dir = list(artist_path.glob('*'))
                    image_files = [f for f in files_in_dir if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']]
                    print(f"  Files in artist dir: {len(image_files)} images")
                print()

        # Export to CSV if there are issues
        if artworks_without_filename or missing_artist_dirs or missing_files:
            csv_path = Path('data/missing_artwork_files.csv')
            csv_path.parent.mkdir(parents=True, exist_ok=True)

            import csv
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['ID', 'Artist', 'Title', 'Year', 'File Name', 'Expected Path', 'Issue Type'])

                # Write artworks without filename
                for artwork in artworks_without_filename:
                    writer.writerow([
                        artwork.id,
                        artwork.artist,
                        artwork.title,
                        artwork.year,
                        '',
                        '',
                        'No file_name in database'
                    ])

                # Write missing artist directories
                for entry in missing_artist_dirs:
                    artwork = entry['artwork']
                    writer.writerow([
                        artwork.id,
                        artwork.artist,
                        artwork.title,
                        artwork.year,
                        artwork.file_name,
                        entry['expected_path'],
                        'Artist directory missing'
                    ])

                # Write missing files
                for entry in missing_files:
                    artwork = entry['artwork']
                    writer.writerow([
                        artwork.id,
                        artwork.artist,
                        artwork.title,
                        artwork.year,
                        artwork.file_name,
                        entry['expected_path'],
                        'Image file missing'
                    ])

            print(f"{'='*80}")
            print(f"CSV report exported to: {csv_path}")
            print(f"{'='*80}\n")

        return {
            'total': len(all_artworks),
            'found': found_files,
            'no_filename': len(artworks_without_filename),
            'missing_dirs': len(missing_artist_dirs),
            'missing_files': len(missing_files)
        }


if __name__ == '__main__':
    results = find_missing_artwork_files()

    # Exit with error code if there are missing files
    if results['no_filename'] + results['missing_dirs'] + results['missing_files'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
