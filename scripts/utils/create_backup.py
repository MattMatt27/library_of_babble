#!/usr/bin/env python3
"""
Create a database backup before collections migration.
This uses the same backup function used by the ETL imports.
"""
from pathlib import Path
from datetime import datetime
from app import create_app
from app.account.routes import create_database_backup

def main():
    """Create a timestamped database backup"""
    app = create_app()

    with app.app_context():
        print("Creating database backup before collections migration...")

        success, backup_path = create_database_backup()

        if success:
            backup_file = Path(backup_path)
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            print(f"✓ Backup created successfully!")
            print(f"  Location: {backup_path}")
            print(f"  Size: {size_mb:.2f} MB")
            print(f"\nYou can restore from this backup if needed using:")
            print(f"  psql library_of_babble < {backup_path}")
        else:
            print(f"✗ Backup failed: {backup_path}")
            exit(1)

if __name__ == '__main__':
    main()
