# ETL Scripts

Data import scripts for loading content from various sources into the Library of Babble database.

## Available Scripts

### 📚 books_etl.py
Loads book data from Goodreads CSV exports and book quotes.

**Functions:**
- `load_book_quotes_from_csv()` - Import book quotes
- `load_goodreads_export()` - Import Goodreads library export

**Data Sources:**
- Goodreads library export (`goodreads_library_export.csv`)
- Book quotes (`book_quotes.csv`)

**Usage:**
```bash
python scripts/etl/books_etl.py
```

**CSV Format - Goodreads Export:**
Export from Goodreads → My Books → Tools → Import/Export

Required columns: Book Id, Title, Author, ISBN, ISBN13, My Rating, Date Read, Bookshelves, etc.

**CSV Format - Book Quotes:**
- Goodreads ID
- Title
- Quote
- Page Number

---

### 🎵 spotify_etl.py
Fetches and loads playlist data from Spotify API.

**Functions:**
- `parse_and_load_playlists()` - Fetch user's playlists from Spotify

**Requirements:**
Set in `.env`:
- `SPOTIPY_CLIENT_ID`
- `SPOTIPY_CLIENT_SECRET`
- `SPOTIPY_USERNAME`

**Usage:**
```bash
python scripts/etl/spotify_etl.py
```

Will prompt for Spotify authorization in browser on first run.

---

### 🎬 movies_etl.py
Loads movie data from Boredom Killer CSV and Letterboxd exports.

**Functions:**
- `load_boredom_killer_movies()` - Import from Boredom Killer CSV
- `load_letterboxd_export()` - Import Letterboxd ratings and reviews

**Data Sources:**
- Boredom Killer - Movies.csv (in `data/`)
- Letterboxd export folder (ratings.csv + reviews.csv in `data/staging/letterboxd/`)

**Usage:**
```bash
python scripts/etl/movies_etl.py
```

**CSV Format - Boredom Killer:**
Required columns: TMDB ID, IMDB ID, Letterboxd ID, Movie, Director(s), Year, Language, Image, Collections, Tags, Plex Status

**Letterboxd Format:**
Export from Letterboxd → Settings → Data → Export Your Data
Place extracted folder as `data/staging/letterboxd/`

---

### 📺 shows_etl.py
Loads TV show data from Boredom Killer CSV.

**Functions:**
- `load_boredom_killer_shows()` - Import TV shows

**Data Sources:**
- Boredom Killer - TV.csv (in `data/staging/`)

**Usage:**
```bash
python scripts/etl/shows_etl.py
```

**CSV Format:**
Required columns: TVDB ID, IMDB ID, TV Show, Year, Poster Image, Collections, Tags, Plex Status

---

### 🎨 artworks_etl.py
Loads artworks and AI-generated images from CSV files.

**Functions:**
- `load_artworks_from_csv()` - Import artwork metadata
- `load_generated_images_from_csv()` - Import AI-generated images

**Data Sources:**
- artworks.csv (in `data/staging/`)
- generated_images.csv (in `data/staging/`)

**Usage:**
```bash
python scripts/etl/artworks_etl.py
```

**CSV Format - Artworks:**
Required columns: Title, Artist, After, Year, Series, Series ID, file_name, site_approved, Location, Description, Medium, Tags

**CSV Format - Generated Images:**
Required columns: Model, Model Version, Prompt, Artist Palette, File Name

**Important Note:** This ETL script syncs with the CSV files - artworks/images not present in the CSV will be removed from the database.

---

## Data Staging Directory

Place CSV files in `data/staging/` before running ETL scripts.

After processing, files are automatically moved to `data/loaded/` with timestamps.

## Running ETL Scripts

### Full Data Load (Fresh Database)

1. **Books:**
   ```bash
   # Place goodreads export and quotes CSV in data/staging/
   python scripts/etl/books_etl.py
   ```

2. **Spotify Playlists:**
   ```bash
   python scripts/etl/spotify_etl.py
   ```

3. **Movies:**
   ```bash
   # Place Boredom Killer - Movies.csv in data/staging/
   # Optional: Place letterboxd folder in data/staging/
   python scripts/etl/movies_etl.py
   ```

4. **TV Shows:**
   ```bash
   # Place Boredom Killer - TV.csv in data/staging/
   python scripts/etl/shows_etl.py
   ```

5. **Artworks (Optional):**
   ```bash
   # Place artworks.csv and generated_images.csv in data/staging/
   python scripts/etl/artworks_etl.py
   ```

### Incremental Updates

ETL scripts detect existing records and update rather than duplicate:
- Books: Updates by Book ID
- Playlists: Updates by Playlist ID
- Quotes: Checks for duplicates before inserting

## Development Notes

### Creating New ETL Scripts

Template structure:
```python
"""
[Content Type] ETL Script
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app import create_app
from app.extensions import db
from app.[blueprint].models import ModelName

def load_data():
    \"\"\"Load data from source\"\"\"
    # ETL logic here
    pass

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        load_data()
```

### Best Practices

1. **Idempotent:** Scripts should be safe to run multiple times
2. **Logging:** Print progress and errors
3. **Error Handling:** Wrap DB operations in try/except
4. **File Movement:** Move processed CSVs to `data/loaded/`
5. **Encoding:** Try multiple encodings for CSV files

## Troubleshooting

**"CSV file not found"**
- Ensure file is in `data/staging/` directory
- Check filename matches what script expects

**Encoding errors:**
- Scripts try multiple encodings automatically
- If still failing, try converting CSV to UTF-8

**Spotify authorization:**
- Ensure `.env` has correct credentials
- May need to authorize in browser on first run
- Check redirect URI matches Spotify app settings

**Database errors:**
- Verify database is running
- Check `DATABASE_URL` in `.env`
- Ensure migrations are up to date: `flask db upgrade`
