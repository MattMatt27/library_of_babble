import csv
import re
from datetime import datetime

# Book CSV Parsing
def read_pins_from_csv():
    pins = []
    with open('data/pins.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Owned'] or row['Sold']:
                image = '../static/images/antiques/pins/' + row['ID'] + '.jpg' if row['ID'] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg'
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
                    'reproduction': row['Repro- duction?']
                }
                pins.append(pin)
    return pins

# Function to get the five most recently read books
def get_recently_added_pins():
    pins = read_pins_from_csv()
    sorted_pins = sorted(pins, key=lambda x: int(x.get('id', 0)), reverse=True)
    return sorted_pins[:10]