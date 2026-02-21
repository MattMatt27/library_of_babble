"""
Creating Routes

Routes for the creative projects showcase page.
"""
import os
from collections import OrderedDict
from flask import render_template, url_for, current_app, request, jsonify, abort
from flask_login import login_required, current_user
from app.creating import creating_bp
from app.creating.models import ProjectCategory, Project, ProjectRelation
from app.extensions import db
from app.main.services import get_user_nav_items


@creating_bp.route('/')
def index():
    """Creating - unified project showcase page"""
    from app.artworks.models import Artworks, GeneratedImages

    nav_items = get_user_nav_items()

    is_admin = current_user.is_authenticated and current_user.is_admin

    # Get categories (admins see all, public sees only public)
    cat_query = ProjectCategory.query.order_by(ProjectCategory.display_order)
    if not is_admin:
        cat_query = cat_query.filter_by(is_public=True)
    categories = cat_query.all()

    # Build projects grouped by category
    projects_by_category = OrderedDict()
    for category in categories:
        proj_query = Project.query.filter_by(category_id=category.id)
        if not is_admin:
            proj_query = proj_query.filter_by(is_public=True)
        projects = proj_query.order_by(Project.display_order).all()

        # Admins see all categories (even empty), public only sees non-empty
        if projects or is_admin:
            projects_by_category[category] = projects

    # Build project relations dict (bidirectional)
    project_relations = {}
    all_relations = ProjectRelation.query.all()
    for rel in all_relations:
        # Forward direction
        if rel.project_id not in project_relations:
            project_relations[rel.project_id] = []
        related = Project.query.get(rel.related_project_id)
        if related and related.is_public:
            cat = ProjectCategory.query.get(related.category_id)
            project_relations[rel.project_id].append({
                'slug': related.slug,
                'title': related.title,
                'short_description': related.short_description,
                'hero_image': related.hero_image,
                'category_slug': cat.slug if cat else '',
                'category_name': cat.name if cat else '',
                'note': rel.note,
            })
        # Reverse direction
        if rel.related_project_id not in project_relations:
            project_relations[rel.related_project_id] = []
        source = Project.query.get(rel.project_id)
        if source and source.is_public:
            cat = ProjectCategory.query.get(source.category_id)
            project_relations[rel.related_project_id].append({
                'slug': source.slug,
                'title': source.title,
                'short_description': source.short_description,
                'hero_image': source.hero_image,
                'category_slug': cat.slug if cat else '',
                'category_name': cat.name if cat else '',
                'note': rel.note,
            })

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

    # For admin modal: flat list of all projects for relation picker
    all_projects_list = []
    if is_admin:
        all_projects = Project.query.order_by(Project.title).all()
        all_projects_list = [{'id': p.id, 'title': p.title} for p in all_projects]

    return render_template(
        'creating/index.html',
        projects_by_category=projects_by_category,
        project_relations=project_relations,
        artists=artist_data,
        generated_images=generated_image_data,
        nav_items=nav_items,
        all_categories=categories,
        all_projects_list=all_projects_list,
    )


def _sync_relations(project_id, relations_data):
    """Replace all relations for a project with the given list.

    relations_data: list of {'project_id': int, 'note': str}
    """
    # Delete existing relations in both directions
    ProjectRelation.query.filter(
        db.or_(
            ProjectRelation.project_id == project_id,
            ProjectRelation.related_project_id == project_id,
        )
    ).delete(synchronize_session='fetch')

    # Create new relations
    for rel in (relations_data or []):
        other_id = rel.get('project_id')
        if other_id and other_id != project_id:
            db.session.add(ProjectRelation(
                project_id=project_id,
                related_project_id=other_id,
                note=rel.get('note', ''),
            ))


# ── Admin API routes ────────────────────────────────────────────

@creating_bp.route('/api/project', methods=['POST'])
@login_required
def create_project():
    """Create a new project (admin only)"""
    if not current_user.is_admin:
        abort(403)

    data = request.get_json()
    if not data or not data.get('title') or not data.get('category_id'):
        return jsonify({'success': False, 'error': 'Title and category are required'}), 400

    # Generate slug from title
    slug = data['title'].lower().replace(' ', '-')
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')

    # Ensure unique slug
    existing = Project.query.filter_by(slug=slug).first()
    if existing:
        slug = f"{slug}-{Project.query.count() + 1}"

    project = Project(
        slug=slug,
        title=data['title'],
        category_id=data['category_id'],
        short_description=data.get('short_description', ''),
        full_description=data.get('full_description', ''),
        tech_stack=data.get('tech_stack', ''),
        project_url=data.get('project_url', ''),
        github_url=data.get('github_url', ''),
        status=data.get('status', 'active'),
        layout_type=data.get('layout_type', 'standard'),
        is_public=data.get('is_public', True),
        display_order=data.get('display_order', 0),
    )
    db.session.add(project)
    db.session.flush()  # get project.id before syncing relations

    if 'relations' in data:
        _sync_relations(project.id, data['relations'])

    db.session.commit()
    return jsonify({'success': True, 'project_id': project.id})


@creating_bp.route('/api/project/<int:project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    """Get project data for editing (admin only)"""
    if not current_user.is_admin:
        abort(403)

    project = Project.query.get_or_404(project_id)

    # Get relations (both directions)
    relations = []
    for rel in ProjectRelation.query.filter(
        db.or_(
            ProjectRelation.project_id == project_id,
            ProjectRelation.related_project_id == project_id,
        )
    ).all():
        other_id = rel.related_project_id if rel.project_id == project_id else rel.project_id
        other = Project.query.get(other_id)
        if other:
            relations.append({
                'project_id': other.id,
                'title': other.title,
                'note': rel.note or '',
            })

    return jsonify({
        'success': True,
        'project': {
            'id': project.id,
            'title': project.title,
            'slug': project.slug,
            'category_id': project.category_id,
            'short_description': project.short_description or '',
            'full_description': project.full_description or '',
            'tech_stack': project.tech_stack or '',
            'project_url': project.project_url or '',
            'github_url': project.github_url or '',
            'status': project.status,
            'layout_type': project.layout_type,
            'is_public': project.is_public,
            'display_order': project.display_order,
            'relations': relations,
        }
    })


@creating_bp.route('/api/project/<int:project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    """Update a project (admin only)"""
    if not current_user.is_admin:
        abort(403)

    project = Project.query.get_or_404(project_id)
    data = request.get_json()

    if 'title' in data:
        project.title = data['title']
    if 'category_id' in data:
        project.category_id = data['category_id']
    if 'short_description' in data:
        project.short_description = data['short_description']
    if 'full_description' in data:
        project.full_description = data['full_description']
    if 'tech_stack' in data:
        project.tech_stack = data['tech_stack']
    if 'project_url' in data:
        project.project_url = data['project_url']
    if 'github_url' in data:
        project.github_url = data['github_url']
    if 'status' in data:
        project.status = data['status']
    if 'layout_type' in data:
        project.layout_type = data['layout_type']
    if 'is_public' in data:
        project.is_public = data['is_public']
    if 'display_order' in data:
        project.display_order = data['display_order']

    if 'relations' in data:
        _sync_relations(project_id, data['relations'])

    db.session.commit()
    return jsonify({'success': True})


@creating_bp.route('/api/project/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    """Delete a project (admin only)"""
    if not current_user.is_admin:
        abort(403)

    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'success': True})


@creating_bp.route('/api/project/<int:project_id>/toggle-visibility', methods=['POST'])
@login_required
def toggle_project_visibility(project_id):
    """Toggle project visibility (admin only)"""
    if not current_user.is_admin:
        abort(403)

    project = Project.query.get_or_404(project_id)
    project.is_public = not project.is_public
    db.session.commit()
    return jsonify({'success': True, 'is_public': project.is_public})


@creating_bp.route('/api/category', methods=['POST'])
@login_required
def create_category():
    """Create a new project category (admin only)"""
    if not current_user.is_admin:
        abort(403)

    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'success': False, 'error': 'Name is required'}), 400

    slug = data.get('slug') or data['name'].lower().replace(' ', '-')
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')

    if ProjectCategory.query.filter_by(slug=slug).first():
        return jsonify({'success': False, 'error': 'A category with that slug already exists'}), 400

    # Place new category after the last one
    max_order = db.session.query(db.func.max(ProjectCategory.display_order)).scalar() or 0

    category = ProjectCategory(
        slug=slug,
        name=data['name'],
        description=data.get('description', ''),
        icon=data.get('icon', ''),
        display_order=max_order + 1,
        is_public=data.get('is_public', True),
    )
    db.session.add(category)
    db.session.commit()
    return jsonify({'success': True, 'category_id': category.id})
