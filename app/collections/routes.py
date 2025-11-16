"""
Collections Routes

Handles pins, alcohol labels, and general collecting page
"""
from flask import render_template
from app.collections import collections_bp
from app.collections.services import (
    get_recently_added_pins,
    get_recently_added_labels,
    read_pins_from_csv,
    read_alc_labels_from_csv
)


@collections_bp.route('/')
def index():
    """Main collecting page with recent pins and labels"""
    recently_added_pins = get_recently_added_pins()
    recently_added_labels = get_recently_added_labels()

    return render_template(
        'collections/index.html',
        recently_added_pins=recently_added_pins,
        recently_added_labels=recently_added_labels
    )


@collections_bp.route('/pins')
def pins():
    """Full pins collection page"""
    pins_data = read_pins_from_csv()
    return render_template('collections/pins.html', pins=pins_data)


@collections_bp.route('/alcohol-labels')
def alcohol_labels():
    """Full alcohol labels collection page"""
    labels_data = read_alc_labels_from_csv()
    return render_template('collections/alcohol_labels.html', labels=labels_data)
