"""
Main Application Routes

Root-level pages like home, writing, creating, etc.
"""
from flask import render_template, url_for
from app.main import main_bp
from app.main.services import get_user_nav_items


@main_bp.route('/')
def home():
    """Home page"""
    from app.services.settings import get_setting

    nav_items = get_user_nav_items()

    # Get background images and interval from settings
    home_backgrounds = get_setting('home_background_images', [])
    background_interval = get_setting('home_background_interval', 15000)

    return render_template(
        'main/home.html',
        nav_items=nav_items,
        home_backgrounds=home_backgrounds,
        background_interval=background_interval
    )


@main_bp.route('/writing')
def writing():
    """Redirect to new writing blueprint"""
    from flask import redirect
    return redirect(url_for('writing.index'))


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
    """Redirect to new creating blueprint"""
    from flask import redirect
    return redirect(url_for('creating.index'))
