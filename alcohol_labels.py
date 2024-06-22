import csv
import re
from datetime import datetime

# Book CSV Parsing
def read_alc_labels_from_csv():
    labels = []
    with open('data/alcohol_labels.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Owned'] or row['Sold']:
                image = '../static/images/antiques/alcohol labels/' + row['ID'] + '.jpg' if row['ID'] else 'https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg'
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
    return labels

# Function to get the five most recently read books
def get_recently_added_labels():
    labels = read_alc_labels_from_csv()
    sorted_labels = sorted(labels, key=lambda x: int(x.get('id', 0)), reverse=True)
    return sorted_labels[:6]