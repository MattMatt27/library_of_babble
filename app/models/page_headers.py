"""
Page Headers Model

Stores page-level header configuration (browser tab title, page title, subtitle)
for each page in the application.
"""
from app.extensions import db
from datetime import datetime


class PageHeader(db.Model):
    """
    Page-level header configuration.

    Each page can have:
    - tab_title: Text shown in browser tab (null = just show site name)
    - title: Main heading displayed on page (null = no header shown)
    - subtitle: Optional description text below the title
    """

    __tablename__ = 'page_headers'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    tab_title = db.Column(db.String(100))
    title = db.Column(db.String(200))
    subtitle = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<PageHeader {self.slug}>'
