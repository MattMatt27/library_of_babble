"""
Collecting Routes

Handles pins, alcohol labels, and general collecting page
"""
from flask import render_template, request, redirect, url_for, flash
from app.collecting import collecting_bp
from app.collecting.services import (
    get_recently_added_pins,
    get_recently_added_labels,
    get_all_pins,
    get_all_labels,
    get_pin_by_id,
    get_label_by_id,
    send_offer_email
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


@collecting_bp.route('/pins/<int:pin_id>')
def pin_detail(pin_id):
    """Individual pin detail page"""
    pin = get_pin_by_id(pin_id)
    return render_template('collecting/pin_detail.html', pin=pin)


@collecting_bp.route('/alcohol-labels')
def alcohol_labels():
    """Full alcohol labels collection page"""
    labels_data = get_all_labels()
    return render_template('collecting/alcohol_labels.html', labels=labels_data)


@collecting_bp.route('/alcohol-labels/<int:label_id>')
def label_detail(label_id):
    """Individual alcohol label detail page"""
    label = get_label_by_id(label_id)
    return render_template('collecting/alcohol_label_detail.html', label=label)


@collecting_bp.route('/submit-offer', methods=['POST'])
def submit_offer():
    """Handle offer submissions"""
    item_id = request.form.get('item_id')
    item_type = request.form.get('item_type')
    item_name = request.form.get('item_name')
    name = request.form.get('name')
    email = request.form.get('email')
    amount = request.form.get('amount')
    message = request.form.get('message', '')

    # Send email notification
    success = send_offer_email(
        item_id=item_id,
        item_type=item_type,
        item_name=item_name,
        customer_name=name,
        customer_email=email,
        offer_amount=amount,
        customer_message=message
    )

    if success:
        flash('Your offer has been submitted successfully! We\'ll be in touch soon.', 'success')
    else:
        flash('There was an error submitting your offer. Please try again later.', 'error')

    # Redirect back to the appropriate page
    if item_type == 'pin':
        return redirect(url_for('collecting.pins'))
    else:
        return redirect(url_for('collecting.alcohol_labels'))
