"""
Collecting Routes

Handles pins, alcohol labels, and general collecting page
"""
from flask import render_template
from app.collecting import collecting_bp
from app.collecting.services import (
    get_recently_added_pins,
    get_recently_added_labels,
    get_all_pins,
    get_all_labels
)


@collecting_bp.route('/')
def index():
    """Main collecting page with recent pins and labels"""
    recently_added_pins = get_recently_added_pins()
    recently_added_labels = get_recently_added_labels()

    return render_template(
        'collecting/index.html',
        recently_added_pins=recently_added_pins,
        recently_added_labels=recently_added_labels
    )


@collecting_bp.route('/pins')
def pins():
    """Full pins collection page"""
    pins_data = get_all_pins()
    return render_template('collecting/pins.html', pins=pins_data)


@collecting_bp.route('/alcohol-labels')
def alcohol_labels():
    """Full alcohol labels collection page"""
    labels_data = get_all_labels()
    return render_template('collecting/alcohol_labels.html', labels=labels_data)
