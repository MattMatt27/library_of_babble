"""
Collections Business Logic and Helper Functions
"""
import csv


def read_pins_from_csv():
    """Read pins from CSV file"""
    pins = []
    try:
        with open('data/pins.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Owned'] or row['Sold']:
                    image = f"../static/images/antiques/pins/{row['ID']}.jpg" if row['ID'] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg'
                    year = row['Year'] if row['Year'] else 'Unsure'
                    pin = {
                        'id': row['ID'],
                        'year': year,
                        'text': row['Text'],
                        'type': row['Type'],
                        'notes': row['Notes'],
                        'image_url': image,
                        'owned': row['Owned'],
                        'sold': row['Sold'],
                        'reproduction': row.get('Repro- duction?', '')
                    }
                    pins.append(pin)
    except FileNotFoundError:
        pass  # Return empty list if file doesn't exist

    return pins


def get_recently_added_pins(limit=10):
    """Get most recently added pins"""
    pins = read_pins_from_csv()
    sorted_pins = sorted(pins, key=lambda x: int(x.get('id', 0)), reverse=True)
    return sorted_pins[:limit]


def read_alc_labels_from_csv():
    """Read alcohol labels from CSV file"""
    labels = []
    try:
        with open('data/alcohol_labels.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Owned'] or row['Sold']:
                    image = f"../static/images/antiques/alcohol labels/{row['ID']}.jpg" if row['ID'] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg'
                    year = row['Year'] if row['Year'] else 'Unsure'
                    label = {
                        'id': row['ID'],
                        'year': year,
                        'text': row['Text'],
                        'type': row['Alcohol Type'],
                        'dimensions': row['Dimensions'],
                        'distribution_location': row['Distributed By Location'],
                        'bottling_location': row['Bottled By Location'],
                        'notes': row['Notes'],
                        'image_url': image,
                        'owned': row['Owned'],
                        'sold': row['Sold'],
                    }
                    labels.append(label)
    except FileNotFoundError:
        pass  # Return empty list if file doesn't exist

    return labels


def get_recently_added_labels(limit=10):
    """Get most recently added alcohol labels"""
    labels = read_alc_labels_from_csv()
    sorted_labels = sorted(labels, key=lambda x: int(x.get('id', 0)), reverse=True)
    return sorted_labels[:limit]
