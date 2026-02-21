"""
Creating Models

Database models for creative projects organized by categories.
"""
from app.extensions import db
from datetime import datetime


class ProjectCategory(db.Model):
    """Categories for organizing projects (Art, Software, Research, etc.)"""

    __tablename__ = 'project_categories'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # Font Awesome icon class
    display_order = db.Column(db.Integer, default=0)
    is_public = db.Column(db.Boolean, default=True)

    projects = db.relationship('Project', backref='category', lazy='dynamic',
                                order_by='Project.display_order')

    def __repr__(self):
        return f'<ProjectCategory {self.name}>'


class Project(db.Model):
    """Creative projects for the Creating page"""

    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='active')  # active, in_development, archived

    category_id = db.Column(db.Integer, db.ForeignKey('project_categories.id'))

    short_description = db.Column(db.Text)
    full_description = db.Column(db.Text)  # HTML allowed

    display_order = db.Column(db.Integer, default=0)
    layout_type = db.Column(db.String(50), default='standard')  # standard, split, gallery, interactive
    is_featured = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=True)

    hero_image = db.Column(db.String(500))
    hero_image_alt = db.Column(db.String(200))

    project_url = db.Column(db.String(500))
    github_url = db.Column(db.String(500))
    documentation_url = db.Column(db.String(500))

    # Software-specific (optional)
    tech_stack = db.Column(db.String(500))
    version = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images = db.relationship('ProjectImage', backref='project', lazy='dynamic',
                              cascade='all, delete-orphan', order_by='ProjectImage.display_order')

    def __repr__(self):
        return f'<Project {self.title}>'


class ProjectRelation(db.Model):
    """Links between related projects across categories"""

    __tablename__ = 'project_relations'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    related_project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    note = db.Column(db.String(200))  # e.g., "Built to support this project"

    def __repr__(self):
        return f'<ProjectRelation {self.project_id} -> {self.related_project_id}>'


class ProjectImage(db.Model):
    """Images associated with a project"""

    __tablename__ = 'project_images'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(500))
    alt_text = db.Column(db.String(200))
    display_order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<ProjectImage {self.image_path}>'
