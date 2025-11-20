# Library of Babble

**A living portfolio showcasing data engineering and full-stack development skills through a personal content aggregation platform.**

---

## About This Project

As a data engineer by training and archaeologist by education, I've always been passionate about classification, curation, and making data work for me. Rather than maintaining a static portfolio of development projects, I wanted to create something more dynamic for my home page on the internet. That is why I decided to create a living platform that demonstrates my technical skills while serving a real purpose in my daily life.

**Library of Babble** is the result: a custom-built Flask web application that aggregates my content consumption across multiple services (Goodreads, Letterboxd, Spotify, and more) into a single, unified interface. It's where I:

- **Track** what I'm reading, watching, listening to, and collecting
- **Curate** my reviews, ratings, quotes, and playlists
- **Showcase** my data engineering skills through ETL pipelines, database design, and API integrations
- **Experiment** with new technologies and development patterns in a production environment

This is designed to be a living project that I will update and improve continuously as my career develops. 

## Why This Approach?

Traditional portfolios show *what* you've built. This project demonstrates:

- **How I architect solutions** - Full-stack design patterns, database schemas, API integrations
- **How I engineer data pipelines** - ETL scripts with conflict resolution, data validation, and incremental imports
- **How I prioritize security** - CSRF protection, XSS prevention, SQL injection safeguards, Content Security Policies
- **How I think about user experience** - Responsive design, smooth interactions, intuitive navigation
- **How I maintain code quality** - Comprehensive documentation, security standards, testing practices

## Tech Stack

**Backend:**
- Python 3.x
- Flask (Web Framework)
- SQLAlchemy (ORM)
- PostgreSQL (Production) / SQLite (Development)
- Flask-Login (Authentication)
- Flask-WTF (CSRF Protection)

**Frontend:**
- Jinja2 Templates
- JavaScript (ES6+)
- jQuery & jQuery UI
- Custom CSS with responsive design

**Integrations:**
- Spotify Web API (via Spotipy)
- The Movie Database (TMDB) API
- Goodreads CSV Exports
- Letterboxd CSV Exports

## What I'm Up To

The content on this site reflects what I'm currently engaged with. Reach out, adn I will create an account for you so that you can browse and see what I'm:

- **Reading** - Books I've finished, quotes that stuck with me, recommendations and reviews
- **Watching** - Movies and shows I've seen, recommendations and reviews
- **Listening** - Curated playlists, monthly music archives since 2019
- **Writing** - Publications and written work
- **Creating** - Visual art projects 
- **Collecting** - Personal collections (pins, bottle labels, etc.)
- **Pondering** - Art pieces and artists I find meaningful

**Want to discuss any of this?** I'm always happy to chat about books, movies, music, or any of the technical decisions behind this platform. Feel free to reach out!

---

## Setting Up Your Own Instance

Want to run your own version of Library of Babble? Here's how to get started.

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12+ (recommended for production) or SQLite (for development)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/library_of_babble.git
   cd library_of_babble
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Copy `.env.example` to `.env` and configure the following:

   ```bash
   cp .env.example .env
   ```

   **Required Configuration:**

   | Variable | Description | How to Obtain |
   |----------|-------------|---------------|
   | `FLASK_SECRET_KEY` | Secret key for session encryption | Generate with `python -c 'import secrets; print(secrets.token_hex(32))'` |
   | `DATABASE_URL` | PostgreSQL connection string | Format: `postgresql://username:password@localhost/dbname` |
   | `FLASK_DEBUG` | Enable debug mode (development only) | Set to `true` for development, `false` for production |
   | `SPOTIPY_CLIENT_ID` | Spotify API client ID | Create app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications) |
   | `SPOTIPY_CLIENT_SECRET` | Spotify API client secret | From same Spotify app |
   | `SPOTIPY_USERNAME` | Your Spotify username | Find at [Spotify Account Overview](https://www.spotify.com/account/overview/) |
   | `TMDB_API_BEARER_TOKEN` | TMDB API bearer token | Create account and get API key at [TMDB API Settings](https://www.themoviedb.org/settings/api) |

   **Optional Configuration:**

   | Variable | Description | Default |
   |----------|-------------|---------|
   | `FLASK_HOST` | Development server host | `127.0.0.1` |
   | `FLASK_PORT` | Development server port | `5000` |
   | `FLASK_ENV` | Environment (development/production) | `development` |

5. **Initialize the database**
   ```bash
   flask db upgrade
   ```

6. **Create an admin user**
   ```bash
   python scripts/create_user.py
   ```

7. **Run the application**
   ```bash
   python run.py
   ```

   The app will be available at `http://127.0.0.1:5000`

### Importing Your Data

The application supports importing data from various sources through the Account page (requires admin access).

#### Goodreads (Books)

**Export Process:**
1. Log into Goodreads
2. Go to "My Books"
3. Click "Import and export" under Tools
4. Click "Export Library"
5. Download the CSV file (named `goodreads_library_export.csv`)

**Import:**
- Navigate to Account → Data Management → Import Data → Goodreads
- Upload the CSV file
- The system will automatically:
  - Add new books
  - Update unread books to read status if they've been marked as read
  - Report conflicts for books already marked as read (database is source of truth)

**Expected Columns:**
`Book Id`, `Title`, `Author`, `Additional Authors`, `ISBN`, `ISBN13`, `My Rating`, `Average Rating`, `Publisher`, `Number of Pages`, `Original Publication Year`, `Date Read`, `Date Added`, `Bookshelves`, `Exclusive Shelf`, `My Review`, `Private Notes`, `Read Count`, `Owned Copies`

#### Letterboxd (Movies)

**Export Process:**
1. Log into Letterboxd
2. Go to Settings → Import & Export
3. Click "Export Your Data"
4. Download and extract the ZIP file
5. Use the files: `reviews.csv`, `ratings.csv`, and `watched.csv`

**Import:**
- Navigate to Account → Data Management → Import Data → Letterboxd
- Upload one or more CSV files from your export
- The system handles:
  - Reviews with ratings and text
  - Ratings without reviews
  - Watch dates and tracking

**Expected Files:**
- `reviews.csv` - Contains: `Date`, `Name`, `Year`, `Letterboxd URI`, `Rating`, `Review`
- `ratings.csv` - Contains: `Date`, `Name`, `Year`, `Letterboxd URI`, `Rating`
- `watched.csv` - Contains: `Date`, `Name`, `Year`, `Letterboxd URI`

#### Boredom Killer (Movies & TV Shows)

**What is Boredom Killer?**
Boredom Killer is a custom Google Sheets template for tracking movies and TV shows with additional metadata like online database ids and collections.

**File Format:**
Export your Google Sheet as CSV. The file should contain these columns:

**For Movies (`Boredom Killer - Movies.csv`):**
`Movie`, `Year`, `Status`, `Source`, `IMDB ID`, `TMDB ID`, `Letterboxd ID`, `Collections`, `Tags`, `Posters`, `Language`, `Director(s)`, `Image`

**For TV Shows (`Boredom Killer - TV.csv`):**
`TV Show`, `Year`, `Status`, `TVDB ID`, `IMDB ID`, `Collections`, `Tags`, `Poster Image`

**For Documentaries (`Boredom Killer - Documentaries.csv`):**
Same format as Movies

**For Docuseries (`Boredom Killer - Docuseries.csv`):**
Same format as TV Shows

**Import:**
- Navigate to Account → Data Management → Import Data → Boredom Killer
- Select the type (Movies, TV Shows, or Docuseries)
- Upload the CSV file
- The system automatically fetches additional metadata from TMDB/TVDB

**Note:** The Boredom Killer format is custom-designed for my workflow. If you want to use this feature, you'll need to create a similar spreadsheet structure or adapt the ETL scripts to your format.

#### Book Quotes

**File Format:**
Create a CSV file named `book_quotes.csv` with these columns:

`Goodreads ID`, `Title`, `Quote`, `Page Number`

**Import:**
- Place the file in `data/staging/`
- Run: `python scripts/etl/books_etl.py`

**Note:** This is a manual process for now. Web-based quote import may be added in the future.

#### Artwork Collections

**Individual Upload:**
- Navigate to Account → Artwork Management
- Enter artist name and upload image
- Files are organized by artist in `static/images/artists/`

**CSV Import:**
Create a CSV with columns: `artist`, `image_filename`

Place images in a folder and reference them in the CSV, then use the CSV import feature.

**Allowed File Types:** `.png`, `.jpg`, `.jpeg`, `.gif`

### Running ETL Scripts Manually

For advanced users, ETL scripts can be run directly:

```bash
# Books
python scripts/etl/books_etl.py path/to/goodreads_export.csv --use-transaction

# Movies
python scripts/etl/movies_etl.py --bk-movies path/to/boredom_killer_movies.csv

# TV Shows
python scripts/etl/shows_etl.py --bk-tv path/to/boredom_killer_tv.csv
```

**Transaction Mode:**
Use `--use-transaction` flag to automatically rollback on errors.

### Deployment

This application is designed to be deployed on platforms like Fly.io, Heroku, or similar PaaS providers.

**Important Deployment Considerations:**
- Set `FLASK_DEBUG=false` in production
- Use PostgreSQL (not SQLite) for production
- Configure proper secret keys
- Enable HTTPS (security headers include HSTS)
- Set up regular database backups

**Need help deploying your instance?** Feel free to reach out! I'm happy to provide guidance or assistance with deployment configuration.

---

## Project Structure

```
library_of_babble/
├── app/                          # Main application package
│   ├── account/                  # Account management & admin tools
│   ├── artworks/                 # Art collection features
│   ├── auth/                     # Authentication (login/register)
│   ├── books/                    # Book tracking & reviews
│   ├── collecting/               # Personal collections (pins, labels, etc.)
│   ├── common/                   # Shared models (reviews, collections)
│   ├── main/                     # Home page & navigation
│   ├── movies/                   # Movie tracking & reviews
│   ├── music/                    # Spotify playlist curation
│   ├── shows/                    # TV show tracking (placeholder)
│   ├── watching/                 # Combined movies/shows view
│   ├── writing/                  # Publications & written work
│   ├── templates/                # Jinja2 HTML templates
│   ├── utils/                    # Utility functions (security, helpers)
│   ├── extensions.py             # Flask extensions (db, login, etc.)
│   └── __init__.py               # Application factory
├── data/                         # Data files
│   ├── archive/                  # Processed import files
│   ├── backups/                  # Database backups
│   ├── loaded/                   # Successfully imported files
│   ├── reports/                  # Import conflict reports
│   └── staging/                  # Files ready for import
├── docs/                         # Documentation
│   ├── ignore/                   # Security implementation docs
│   ├── Secure Development Lifecycle (SDL) Guide.md
│   └── Style and Design Guidelines.md
├── migrations/                   # Database migrations (Flask-Migrate)
├── scripts/                      # Utility scripts
│   ├── etl/                      # ETL pipeline scripts
│   └── create_user.py            # User creation utility
├── static/                       # Static assets
│   ├── css/                      # Stylesheets
│   ├── images/                   # Images and uploads
│   └── js/                       # JavaScript files
├── .env.example                  # Environment variable template
├── config.py                     # Application configuration
├── requirements.txt              # Python dependencies
└── run.py                        # Application entry point
```

## Documentation

- **Security Development Guide:** `docs/Secure Development Lifecycle (SDL) Guide.md` - Comprehensive security standards and best practices
- **Style Guidelines:** `docs/Style and Design Guidelines.md` - Code style and design conventions

## Contributing

This is a personal project and portfolio piece, but I'm open to suggestions and discussions about implementation approaches. If you find a security issue, please report it responsibly by contacting me directly.

## License

This project is personal portfolio work. If you'd like to use portions of the code, please reach out to discuss.

## Contact

Interested in discussing this project, the technical decisions behind it, or anything I'm reading/watching/listening to?

**Let's connect!**

- Check out what I'm up to at [mattflathers.com]
- Or email me at [mattflathers27@gmail.com]

---

**Built with ☕ and 🎵 by Matt Flathers and Claude Code**

*A living demonstration that the best portfolio projects are the ones you actually use.*
