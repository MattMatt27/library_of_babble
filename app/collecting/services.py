"""
Collecting Business Logic and Helper Functions
"""
from app.extensions import db
from app.collecting.models import Pin, AlcoholLabel


def get_all_pins():
    """Get all pins from database"""
    return Pin.query.filter(
        (Pin.owned == True) | (Pin.sold == True)
    ).order_by(Pin.id.desc()).all()


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


def get_recently_added_labels(limit=10):
    """Get most recently added alcohol labels"""
    return AlcoholLabel.query.filter(
        (AlcoholLabel.owned == True) | (AlcoholLabel.sold == True)
    ).order_by(AlcoholLabel.id.desc()).limit(limit).all()
