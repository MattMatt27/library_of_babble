import sqlite3
import os

DB_PATH = "instance/portfolio_prd.db"
IMAGE_BASE_PATH = "static/images/artists"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Pull the relevant data from Artworks
cursor.execute("SELECT id, artist, file_name FROM Artworks")
rows = cursor.fetchall()

missing_images = []

for artwork_id, artist, filename in rows:
    # Construct the folder path for this artist
    artist_folder = os.path.join(IMAGE_BASE_PATH, artist)

    # Check if the artist folder exists
    if not os.path.isdir(artist_folder):
        missing_images.append((artwork_id, artist, filename))
        continue

    # Construct the file path and check if it exists
    file_path = os.path.join(artist_folder, filename)
    if not os.path.isfile(file_path):
        missing_images.append((artwork_id, artist, filename))

conn.close()

# Display results
if missing_images:
    print("The following Artworks rows do not have an associated image:")
    for row in missing_images:
        print(row)
else:
    print("All Artworks appear to have associated images.")