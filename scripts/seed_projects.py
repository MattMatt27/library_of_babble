"""
Seed projects and categories from existing content

Run with: python scripts/seed_projects.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.creating.models import ProjectCategory, Project, ProjectImage

CATEGORIES = [
    {
        'slug': 'art',
        'name': 'Art Projects',
        'description': None,
        'icon': None,
        'display_order': 1,
    },
]

PROJECTS = [
    # Art Projects
    {
        'category_slug': 'art',
        'slug': 'museum-interpolations',
        'title': 'Museum Interpolations',
        'status': 'active',
        'layout_type': 'split',
        'display_order': 1,
        'hero_image': 'images/creating/interpolations/Terminal Sump.png',
        'hero_image_alt': 'Museum Interpolations - Terminal Sump',
        'full_description': '''<p>This project uses image models to generate visual paths between artifacts in museum collections. Taking high-resolution photographs of two objects, say a bronze vessel and a ceramic figure or a textile and a carved relief, and it produces the intermediate steps: images that sit between them, inheriting features from both.</p>
<p>We developed the methodology to work with any documented collection of artifacts. The Harvard CAMLab has generously supported us as we build out the project, but the code and processes are designed to be generalizable.</p>
<p>The interpolated artifacts aren't invented by the process so much as revealed by it. The original objects, by existing, define a space of possible intermediates; the model traverses that space and renders what it finds. We display the results as single path progressions as grid projections, where diagonal paths create artifacts that sit between multiple pairs of sources at once.</p>
<p>What emerges are objects no culture actually produced, but that carry recognizable traces of the cultures that did. Allowing for speculative archaeology.</p>''',
    },
    {
        'category_slug': 'art',
        'slug': 'books-on-tape',
        'title': 'Books on Tape',
        'status': 'in_development',
        'layout_type': 'standard',
        'display_order': 2,
        'full_description': '''<p>This installation is built from CRT monitors, hollowed-out VCRs fitted with NFC readers, and a library of tagged paperback books. You select books, insert them into the VCR slots, and the system identifies what you've chosen. Working with language models behind the scenes, it generates a literary artifact that draws on the styles, themes, and structures of your inputs. The result displays on the CRT, and the output is viewable and downloadable online.</p>
<p>VCRs and CRTs, early-generation technologies in a then-new media format, were chosen to engage with the idea that language models are in a similarly early stage of technological development. The temptation is to sell AI as distinctly modern and novel, but in this piece we aim to challenge viewers to consider the opposite. That this is merely the beginning.</p>''',
        'images': [
            {'path': 'images/creating/books-on-tape/Origins.jpg', 'alt': 'Books on Tape - Origins'},
            {'path': 'images/creating/books-on-tape/Books.jpg', 'alt': 'Books on Tape - Books'},
            {'path': 'images/creating/books-on-tape/Sample_stack.jpg', 'alt': 'Books on Tape - Sample Stack'},
        ]
    },
    {
        'category_slug': 'art',
        'slug': 'generative-art',
        'title': 'Generative Art',
        'status': 'active',
        'layout_type': 'interactive',
        'display_order': 3,
        'full_description': '''<p>When thinking about making art with generative image models I treat artists as my palette. I find painters, illustrators, photographers, designers, etc. whose work the image model has absorbed well enough to interpolate coherently. Then I combine them in prompts, as if they were fictional co-authors of images that exist in the spaces between their styles.</p>
<p>These images aren't collaborations with the named artists, but they're also not conjured from nothing. And I certainly would not claim any kind of creative ownership of the work for myself alone. The artists' bodies of work, by existing in the training data, define a space of possible combinations. The images were always latent there; the prompt is what makes them visible. I am exercising more curatorial and exploratory skills to identify images that move me, images that the original artists unknowingly made possible.</p>''',
    },
]


def seed():
    app = create_app()
    with app.app_context():
        print("Seeding project categories and projects...")

        # Create categories
        category_map = {}
        for cat_data in CATEGORIES:
            category = ProjectCategory.query.filter_by(slug=cat_data['slug']).first()
            if not category:
                category = ProjectCategory(**cat_data)
                db.session.add(category)
                db.session.flush()
                print(f"  Created category: {cat_data['name']}")
            else:
                print(f"  Category already exists: {cat_data['name']}")
            category_map[cat_data['slug']] = category

        # Create projects
        for proj_data in PROJECTS:
            category_slug = proj_data.pop('category_slug')
            images_data = proj_data.pop('images', [])

            project = Project.query.filter_by(slug=proj_data['slug']).first()
            if not project:
                project = Project(
                    category_id=category_map[category_slug].id,
                    **proj_data
                )
                db.session.add(project)
                db.session.flush()
                print(f"  Created project: {proj_data['title']}")

                # Add images
                for i, img_data in enumerate(images_data):
                    if isinstance(img_data, str):
                        img_data = {'path': img_data, 'alt': project.title}
                    image = ProjectImage(
                        project_id=project.id,
                        image_path=img_data['path'],
                        alt_text=img_data.get('alt', project.title),
                        display_order=i
                    )
                    db.session.add(image)
                    print(f"    Added image: {img_data['path']}")
            else:
                print(f"  Project already exists: {proj_data['title']}")
                # Restore popped keys for next iteration
                proj_data['category_slug'] = category_slug
                proj_data['images'] = images_data

        db.session.commit()
        print(f"\nSeeding complete!")
        print(f"  Categories: {len(CATEGORIES)}")
        print(f"  Projects: {len(PROJECTS)}")


if __name__ == '__main__':
    seed()
