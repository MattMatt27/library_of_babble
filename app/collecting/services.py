"""
Collecting Business Logic and Helper Functions
"""
import os
from flask import current_app
from app.extensions import db
from app.collecting.models import Pin, AlcoholLabel


def get_all_pins():
    """Get all pins from database"""
    return Pin.query.filter(
        (Pin.owned == True) | (Pin.sold == True)
    ).order_by(Pin.id.desc()).all()


def get_pin_by_id(pin_id):
    """Get a single pin by ID"""
    return Pin.query.get_or_404(pin_id)


def get_recently_added_pins(limit=10):
    """Get most recently added pins"""
    return Pin.query.filter(
        (Pin.owned == True) | (Pin.sold == True)
    ).order_by(Pin.id.desc()).limit(limit).all()


def get_all_labels():
    """Get all alcohol labels from database"""
    return AlcoholLabel.query.filter(
        (AlcoholLabel.owned == True) | (AlcoholLabel.sold == True)
    ).order_by(AlcoholLabel.id.desc()).all()


def get_label_by_id(label_id):
    """Get a single alcohol label by ID"""
    return AlcoholLabel.query.get_or_404(label_id)


def get_recently_added_labels(limit=10):
    """Get most recently added alcohol labels"""
    return AlcoholLabel.query.filter(
        (AlcoholLabel.owned == True) | (AlcoholLabel.sold == True)
    ).order_by(AlcoholLabel.id.desc()).limit(limit).all()


def send_offer_email(item_id, item_type, item_name, customer_name, customer_email, offer_amount, customer_message=''):
    """
    Send email notification when someone makes an offer

    For now, this just logs the offer. In production, you would configure
    Flask-Mail and send an actual email.
    """
    # Log the offer (in production, this would send an email)
    current_app.logger.info(f"""
    NEW OFFER RECEIVED:
    Item: {item_name} (ID: {item_id}, Type: {item_type})
    Customer: {customer_name} ({customer_email})
    Offer Amount: ${offer_amount}
    Message: {customer_message}
    """)

    # TODO: Configure Flask-Mail and send actual email
    # Example implementation:
    #
    # try:
    #     from app.extensions import mail
    #     msg = Message(
    #         subject=f'New Offer: {item_name}',
    #         recipients=[os.getenv('ADMIN_EMAIL', 'your@email.com')],
    #         body=f"""
    #         New offer received for: {item_name}
    #
    #         Customer: {customer_name}
    #         Email: {customer_email}
    #         Offer Amount: ${offer_amount}
    #
    #         Message:
    #         {customer_message}
    #
    #         Item Details:
    #         - ID: {item_id}
    #         - Type: {item_type}
    #         """
    #     )
    #     mail.send(msg)
    #     return True
    # except Exception as e:
    #     current_app.logger.error(f'Error sending offer email: {e}')
    #     return False

    # For now, just return True (logged successfully)
    return True
