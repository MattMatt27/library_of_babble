"""
Creating Routes

Routes for the creative projects showcase page.
"""
import os
from collections import OrderedDict
from flask import render_template, url_for, current_app
from flask_login import login_required
from app.creating import creating_bp
from app.creating.models import ProjectCategory, Project
from app.main.services import get_user_nav_items


@creating_bp.route('/')
def index():
    """Creating - unified project showcase page"""
    from app.artworks.models import Artworks, GeneratedImages

    nav_items = get_user_nav_items()

    # Get all public categories ordered by display_order
    categories = ProjectCategory.query.filter_by(
        is_public=True
    ).order_by(ProjectCategory.display_order).all()

    # Build projects grouped by category
    projects_by_category = OrderedDict()
    for category in categories:
        projects = Project.query.filter_by(
            category_id=category.id,
            is_public=True
        ).order_by(Project.display_order).all()

        if projects:  # Only include categories that have projects
            projects_by_category[category] = projects

    # Keep existing Lunacy data for interactive section
    generated_images = GeneratedImages.query.all()
    generated_image_data = [{
        'file_name': image.file_name,
        'artist_palette': image.artist_palette.split('|'),
        'model': image.model,
        'model_version': image.model_version,
        'prompt': image.prompt
    } for image in generated_images]

    # Get artist data for the Lunacy interactive section
    artists = Artworks.query.with_entities(
        Artworks.artist,
        Artworks.file_name
    ).distinct().all()

    artist_data = []
    for artist in artists:
        if artist.artist and artist.file_name:
            relative_path = f'images/artists/{artist.artist}/{artist.file_name}'
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

    return render_template(
        'creating/index.html',
        projects_by_category=projects_by_category,
        artists=artist_data,
        generated_images=generated_image_data,
        nav_items=nav_items
    )
