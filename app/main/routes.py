"""
Main Application Routes

Root-level pages like home, writing, creating, etc.
"""
import os
from flask import render_template, url_for, current_app
from app.main import main_bp
from app.main.services import get_user_nav_items
from app.artworks.models import Artworks, GeneratedImages
from app.extensions import db


@main_bp.route('/')
def home():
    """Home page"""
    nav_items = get_user_nav_items()
    return render_template('main/home.html', nav_items=nav_items)


@main_bp.route('/writing')
def writing():
    """Writing projects page"""
    nav_items = get_user_nav_items()
    return render_template('main/writing.html', nav_items=nav_items)


@main_bp.route('/fyog')
def fyog():
    """For Your Own Good project page"""
    nav_items = get_user_nav_items()
    return render_template('main/fyog.html', nav_items=nav_items)


@main_bp.route('/new-generation-thinking')
def ngt():
    """New Generation Thinking page"""
    nav_items = get_user_nav_items()
    return render_template('main/new-generation-thinking.html', nav_items=nav_items)


@main_bp.route('/creating')
def creating():
    """Creating/art showcase page"""
    nav_items = get_user_nav_items()

    # Get distinct artists with their file names
    artists = Artworks.query.with_entities(
        Artworks.artist,
        Artworks.file_name
    ).distinct().all()

    artist_data = []
    for artist in artists:
        if artist.artist and artist.file_name:
            # Use the artist name as the subfolder name
            relative_path = f'images/artists/{artist.artist}/{artist.file_name}'

            # Use os.path.join for the full system path
            full_path = os.path.join(
                current_app.static_folder,
                'images',
                'artists',
                artist.artist,
                artist.file_name
            )

            if os.path.exists(full_path):
                artist_data.append({
                    'name': artist.artist,
                    'image': url_for('static', filename=relative_path)
                })
            else:
                print(f"Warning: File not found for artist {artist.artist}: {full_path}")

    # Get generated images
    generated_images = GeneratedImages.query.all()
    generated_image_data = [{
        'file_name': image.file_name,
        'artist_palette': image.artist_palette.split('|'),
        'model': image.model,
        'model_version': image.model_version,
        'prompt': image.prompt
    } for image in generated_images]

    return render_template(
        'main/creating.html',
        artists=artist_data,
        generated_images=generated_image_data,
        nav_items=nav_items
    )
