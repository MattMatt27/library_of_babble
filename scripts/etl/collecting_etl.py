"""
Collecting ETL Script
Loads pins and alcohol labels from CSV files into database

INCREMENTAL IMPORT STRATEGY:
- Database is source of truth
- Owned/sold items are locked - only report conflicts if data differs
- Other items can be updated
- New items are added
- Never deletes existing data
"""
import csv
import sys
from pathlib import Path
from datetime import datetime
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app import create_app
from app.extensions import db
from app.collecting.models import Pin, AlcoholLabel

# Configure paths
CSV_FOLDER = Path('data/archive/')
LOADED_FOLDER = Path('data/loaded/')
REPORTS_FOLDER = Path('data/reports/')


def load_pins_from_csv():
    """Load pins from CSV file"""
    csv_file = CSV_FOLDER / 'pins.csv'

    if not csv_file.exists():
        print(f"❌ CSV file not found: {csv_file}")
        return

    print(f"\n{'='*60}")
    print(f"LOADING PINS FROM CSV")
    print(f"{'='*60}")

    stats = {
        'total_rows': 0,
        'added': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }

    conflicts = []

    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            stats['total_rows'] += 1
            pin_id = int(row['ID']) if row['ID'] else None

            if not pin_id:
                stats['skipped'] += 1
                continue

            # Check if pin exists
            existing_pin = Pin.query.get(pin_id)

            # Parse boolean values
            owned = row['Owned'] == '1'
            sold = row['Sold'] == '1'
            reproduction = row.get('Repro- duction?', '0') == '1'

            # Only process owned or sold items
            if not owned and not sold:
                stats['skipped'] += 1
                continue

            pin_data = {
                'id': pin_id,
                'year': row['Year'] if row['Year'] else None,
                'text': row['Text'],
                'pin_type': row['Type'],
                'notes': row['Notes'],
                'associated_person': row['Associated Person'],
                'origin': row['Origin'],
                'owned': owned,
                'sold': sold,
                'dimensions': row['Dimen-sions'],
                'grade': row['Grade'],
                'reproduction': reproduction,
                'original_year': row['Original Year'] if row['Original Year'] else None,
                'links': row['Links'],
                'set_id': int(row['Set ID']) if row['Set ID'] else None,
                'number_in_set': int(row['Number in Set']) if row['Number in Set'] else None,
                'image_filename': f"{pin_id}.jpg" if row['Image'] else None
            }

            if existing_pin:
                # Check if locked (owned or sold)
                if existing_pin.owned or existing_pin.sold:
                    # Report conflicts if data differs
                    changes = []
                    for key, value in pin_data.items():
                        if key != 'id' and getattr(existing_pin, key) != value:
                            changes.append(f"{key}: {getattr(existing_pin, key)} → {value}")

                    if changes:
                        conflicts.append({
                            'id': pin_id,
                            'text': existing_pin.text[:50],
                            'changes': changes
                        })
                    stats['skipped'] += 1
                else:
                    # Update unlocked item
                    for key, value in pin_data.items():
                        if key != 'id':
                            setattr(existing_pin, key, value)
                    stats['updated'] += 1
            else:
                # Add new pin
                new_pin = Pin(**pin_data)
                db.session.add(new_pin)
                stats['added'] += 1

    # Commit changes
    try:
        db.session.commit()
        print(f"\n✅ Pins loaded successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error committing pins: {e}")
        stats['errors'] += 1

    # Print summary
    print(f"\n{'='*60}")
    print(f"PINS IMPORT SUMMARY")
    print(f"{'='*60}")
    print(f"Total rows in CSV: {stats['total_rows']}")
    print(f"Added: {stats['added']}")
    print(f"Updated: {stats['updated']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")

    if conflicts:
        print(f"\n⚠️  {len(conflicts)} CONFLICTS DETECTED (locked items with differing data):")
        for conflict in conflicts[:10]:  # Show first 10
            print(f"\n  Pin {conflict['id']}: {conflict['text']}")
            for change in conflict['changes'][:5]:  # Show first 5 changes
                print(f"    - {change}")

        # Write conflicts to report
        report_file = REPORTS_FOLDER / f"pins_conflicts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        REPORTS_FOLDER.mkdir(exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("PINS IMPORT CONFLICTS\n")
            f.write("=" * 60 + "\n\n")
            for conflict in conflicts:
                f.write(f"\nPin {conflict['id']}: {conflict['text']}\n")
                for change in conflict['changes']:
                    f.write(f"  - {change}\n")
        print(f"\n📝 Full conflict report: {report_file}")


def load_alcohol_labels_from_csv():
    """Load alcohol labels from CSV file"""
    csv_file = CSV_FOLDER / 'alcohol_labels.csv'

    if not csv_file.exists():
        print(f"❌ CSV file not found: {csv_file}")
        return

    print(f"\n{'='*60}")
    print(f"LOADING ALCOHOL LABELS FROM CSV")
    print(f"{'='*60}")

    stats = {
        'total_rows': 0,
        'added': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }

    conflicts = []

    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            stats['total_rows'] += 1
            label_id = int(row['ID']) if row['ID'] else None

            if not label_id:
                stats['skipped'] += 1
                continue

            # Check if label exists
            existing_label = AlcoholLabel.query.get(label_id)

            # Parse boolean values
            owned = row['Owned'] == '1'
            sold = row['Sold'] == '1'

            # Only process owned or sold items
            if not owned and not sold:
                stats['skipped'] += 1
                continue

            label_data = {
                'id': label_id,
                'year': row['Year'] if row['Year'] else None,
                'text': row['Text'],
                'alcohol_volume': row['Alcohol Volume'],
                'alcohol_proof': int(row['Alcohol Proof']) if row['Alcohol Proof'] else None,
                'alcohol_type': row['Alcohol Type'],
                'dimensions': row['Dimensions'],
                'distributed_by': row['Distributed By'],
                'distributed_by_location': row['Distributed By Location'],
                'bottled_by': row['Bottled By'],
                'bottled_by_location': row['Bottled By Location'],
                'distilled_by': row['Distilled By'],
                'distilled_by_location': row['Distilled By Location'],
                'notes': row['Notes'],
                'grade': row['Grade'],
                'origin': row['Origin'],
                'owned': owned,
                'sold': sold,
                'image_filename': f"{label_id}.jpg" if row['Image'] else None
            }

            if existing_label:
                # Check if locked (owned or sold)
                if existing_label.owned or existing_label.sold:
                    # Report conflicts if data differs
                    changes = []
                    for key, value in label_data.items():
                        if key != 'id' and getattr(existing_label, key) != value:
                            changes.append(f"{key}: {getattr(existing_label, key)} → {value}")

                    if changes:
                        conflicts.append({
                            'id': label_id,
                            'text': existing_label.text[:50],
                            'changes': changes
                        })
                    stats['skipped'] += 1
                else:
                    # Update unlocked item
                    for key, value in label_data.items():
                        if key != 'id':
                            setattr(existing_label, key, value)
                    stats['updated'] += 1
            else:
                # Add new label
                new_label = AlcoholLabel(**label_data)
                db.session.add(new_label)
                stats['added'] += 1

    # Commit changes
    try:
        db.session.commit()
        print(f"\n✅ Alcohol labels loaded successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error committing labels: {e}")
        stats['errors'] += 1

    # Print summary
    print(f"\n{'='*60}")
    print(f"ALCOHOL LABELS IMPORT SUMMARY")
    print(f"{'='*60}")
    print(f"Total rows in CSV: {stats['total_rows']}")
    print(f"Added: {stats['added']}")
    print(f"Updated: {stats['updated']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")

    if conflicts:
        print(f"\n⚠️  {len(conflicts)} CONFLICTS DETECTED (locked items with differing data):")
        for conflict in conflicts[:10]:  # Show first 10
            print(f"\n  Label {conflict['id']}: {conflict['text']}")
            for change in conflict['changes'][:5]:  # Show first 5 changes
                print(f"    - {change}")

        # Write conflicts to report
        report_file = REPORTS_FOLDER / f"alcohol_labels_conflicts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        REPORTS_FOLDER.mkdir(exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("ALCOHOL LABELS IMPORT CONFLICTS\n")
            f.write("=" * 60 + "\n\n")
            for conflict in conflicts:
                f.write(f"\nLabel {conflict['id']}: {conflict['text']}\n")
                for change in conflict['changes']:
                    f.write(f"  - {change}\n")
        print(f"\n📝 Full conflict report: {report_file}")


if __name__ == '__main__':
    app = create_app()

    with app.app_context():
        print("\n🏺 COLLECTING ETL SCRIPT")
        print("=" * 60)

        # Load pins
        load_pins_from_csv()

        # Load alcohol labels
        load_alcohol_labels_from_csv()

        print(f"\n{'='*60}")
        print("✅ COLLECTING ETL COMPLETE")
        print(f"{'='*60}\n")
