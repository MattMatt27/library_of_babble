#!/usr/bin/env python3
"""
Script to create an admin user for Library of Babble
Usage: python create_admin_user.py
"""

from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import sqlite3
import getpass

# Load environment variables
load_dotenv('.env')

def create_admin_user():
    """Create a new admin user in the database"""

    print("=" * 50)
    print("Library of Babble - Create Admin User")
    print("=" * 50)

    # Get user input
    username = input("Enter username: ").strip()

    if not username:
        print("Error: Username cannot be empty!")
        return

    # Check if user exists
    conn = sqlite3.connect('instance/portfolio_prd.db')
    cursor = conn.cursor()

    cursor.execute("SELECT username FROM user WHERE username = ?", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        print(f"Error: User '{username}' already exists!")
        conn.close()
        return

    # Get password (hidden input)
    password = getpass.getpass("Enter password: ")
    password_confirm = getpass.getpass("Confirm password: ")

    if password != password_confirm:
        print("Error: Passwords don't match!")
        conn.close()
        return

    if len(password) < 6:
        print("Error: Password must be at least 6 characters!")
        conn.close()
        return

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Insert the user
    try:
        cursor.execute(
            "INSERT INTO user (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_password, 'admin')
        )
        conn.commit()
        print(f"\n✓ Admin user '{username}' created successfully!")
        print(f"  Role: admin")
        print(f"  You can now log in with these credentials.\n")
    except sqlite3.IntegrityError as e:
        print(f"Error creating user: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_admin_user()
